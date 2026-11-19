"""App-wide configuration and environment helpers."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
ADMIN_STATIC_DIR = STATIC_DIR / "admin"
ADMIN_JS_DIR = STATIC_DIR / "js"
ADMIN_CSS_DIR = STATIC_DIR / "css"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'car_dealership.db'}",
)

# Uploads folder (documents). Relative to BASE_DIR.
UPLOAD_DIR = BASE_DIR / "uploads"

# Render media files via authenticated endpoint (documents/base64).
MEDIA_URL = "/media"
