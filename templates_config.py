# Templates configuration
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, select_autoescape, FileSystemLoader
from pathlib import Path
from starlette.responses import HTMLResponse

_BASE = Path(__file__).resolve().parent


def money_filter(value):
    """Format a number as a South African Rand currency value."""
    if value is None:
        return "R 0"
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("R", "").strip()
        return f"R {float(value):,.2f}"
    except (ValueError, TypeError):
        return "R 0"


def _hasattr(obj, name):
    """hasattr helper exposed to templates."""
    return hasattr(obj, name)


def _make_env(directory):
    env = Environment(
        loader=FileSystemLoader(str(directory)),
        autoescape=select_autoescape(),
        cache_size=0,  # request object is unhashable; disable template cache
    )
    env.filters["money"] = money_filter
    env.globals["hasattr"] = _hasattr
    return env


# Jinja2 environments for public and admin templates (cache disabled)
_public_env = _make_env(_BASE / "templates" / "public")
_admin_env = _make_env(_BASE / "templates" / "admin")

# Standard Jinja2Templates instances (new Starlette signature: request, name, context)
templates_public = Jinja2Templates(env=_public_env)
templates_admin = Jinja2Templates(env=_admin_env)


def _render(env, name, context=None):
    template = env.get_template(name)
    return HTMLResponse(content=template.render(context or {}))


def render_template(request, name, context=None):
    """Render a public template (request kept for signature compatibility)."""
    return _render(_public_env, name, context)


class CompatTemplates:
    """Compatibility wrapper accepting BOTH TemplateResponse signatures:
       - legacy: TemplateResponse(name, context)
       - modern: TemplateResponse(request, name, context)
    """

    def __init__(self, env):
        self.env = env

    def TemplateResponse(self, *args, **kwargs):
        # Modern Starlette signature: (request, name, context=None, ...)
        # Legacy signature: (name, context=None, ...)
        if len(args) >= 2 and hasattr(args[0], 'scope'):
            # First arg is a Request object -> modern signature
            request = args[0]
            name = args[1]
            context = args[2] if len(args) >= 3 else (kwargs.get('context') or {})
        else:
            # Legacy signature
            name = args[0] if args else kwargs.get('name')
            context = args[1] if len(args) >= 2 else (kwargs.get('context') or {})
        return _render(self.env, name, context)

    def get_template(self, name):
        return self.env.get_template(name)


# Legacy-style template objects for routers still using TemplateResponse(name, context)
templates_admin_compat = CompatTemplates(_admin_env)
