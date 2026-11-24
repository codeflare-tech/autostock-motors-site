"""Car Dealership - FastAPI application factory and entry point."""
from __future__ import annotations

import os
import sys
import socket
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure the project root is importable regardless of cwd
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import HTTPException
from pathlib import Path

from routers import public, admin
from settings import STATIC_DIR, ADMIN_STATIC_DIR

# Ensure uploads directory exists
settings_dir = _HERE / "uploads"
settings_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed the database on first boot (no-op when already populated).
    try:
        import init_db
        init_db.init_db()
        init_db.seed_bna_catalog()
    except Exception as exc:  # never block startup on seeding
        print("seed skipped:", exc)
    yield


app = FastAPI(title="Car Dealership", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Redirect browser navigation to /admin/login on 401; keep JSON for APIs/assets."""
    if exc.status_code == 401 and request.url.path.startswith("/admin"):
        accept = request.headers.get("accept", "")
        is_asset = any(request.url.path.endswith(ext) for ext in
                       (".js", ".css", ".png", ".jpg", ".ico", ".woff", ".woff2"))
        if "text/html" in accept and not is_asset:
            return RedirectResponse(url="/admin/login", status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

# ---------------------------------------------------------------------------
# Static file mounts (media is served via authenticated admin endpoint)
# ---------------------------------------------------------------------------
if os.path.isdir(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.isdir(ADMIN_STATIC_DIR):
    app.mount("/admin/static", StaticFiles(directory=ADMIN_STATIC_DIR), name="admin-static")

# ---------------------------------------------------------------------------
# Router includes
# ---------------------------------------------------------------------------
app.include_router(public.router)
app.include_router(admin.router, prefix="/admin")


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return RedirectResponse(url="/cars", status_code=302)


@app.get("/phone-access")
async def phone_access(request: Request):
    """SSRF-safe phone-access helper page with QR codes for LAN/public sharing.

    The public tunnel URL is the page's own origin when reached via the Cloudflare
    tunnel; we surface that plus the local (WiFi) URL so any device on any network
    can open it instantly.
    """
    import base64
    from io import BytesIO

    try:
        import qrcode
    except ImportError:
        qrcode = None

    def png_b64(data):
        buf = BytesIO()
        data.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    # Public URL = where the user actually reached this page (through the tunnel)
    public_url = request.url.scheme + "://" + request.url.netloc
    # Local (same WiFi) URL
    lan_url = f"http://{get_lan_ip()}:8123"

    if qrcode:
        public_qr = png_b64(qrcode.make(public_url))
        lan_qr = png_b64(qrcode.make(lan_url))
    else:
        public_qr = lan_qr = ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phone Access</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; margin: 0; padding: 24px; }}
  .card {{ max-width: 640px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  h1 {{ font-size: 20px; margin-bottom: 8px; }}
  p {{ color: #666; margin: 4px 0; }}
  .qr {{ display: inline-block; margin: 8px 0; }}
  img {{ max-width: 180px; }}
  a {{ color: #0066cc; }}
  .row {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .col {{ flex: 1; min-width: 200px; }}
  .hint {{ font-size: 12px; color: #888; margin-top: 8px; }}
</style>
</head>
<body>
  <div class="card">
    <h1>Phone Access</h1>
    <p><strong>From anywhere (internet):</strong></p>
    <div class="qr"><img src="data:image/png;base64,{public_qr}" alt="QR"></div>
    <p><a href="{public_url}">{public_url}</a></p>
    <p class="hint">Open this address in any browser on any device. It is routed to this site through Cloudflare.</p>
    <p><strong>From your WiFi (local):</strong></p>
    <div class="qr"><img src="data:image/png;base64,{lan_qr}" alt="QR"></div>
    <p><a href="{lan_url}">{lan_url}</a></p>
    <p class="hint">Keep this computer powered on. The site auto-starts on boot.</p>
  </div>
</body>
</html>
"""


def get_lan_ip():
    """Find the real WiFi/LAN IP of this machine.

    Falls back to hostname resolution when the interface IP cannot be read.
    """
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 8.8.8.8 is only used to determine the route; no packets are sent.
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


def main():
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8123))
    ssl_cert = os.environ.get("SSL_CERT")
    ssl_key = os.environ.get("SSL_KEY")
    if ssl_cert and ssl_key:
        uvicorn.run(app, host=host, port=port, ssl_certfile=ssl_cert, ssl_keyfile=ssl_key)
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
