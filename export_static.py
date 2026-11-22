#!/usr/bin/env python3
"""Export the public site to static HTML for GitHub Pages.

Renders every public page through the real FastAPI app (so the actual Jinja
templates and DB data are used), rewrites absolute internal URLs to the
GitHub Pages base path, and copies static assets.
"""
from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

import main  # noqa: F401  (ensures app + routers are registered)

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / "static_export"
BASE = "/autostock-motors"

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

client = TestClient(main.app)


def fix_urls(html: str) -> str:
    """Prefix absolute internal links with the GitHub Pages base path."""
    html = re.sub(r'(href|src|action)="/(?!/)', rf'\1="{BASE}/', html)
    html = html.replace("url(/", f"url({BASE}/")
    return html


FORM_INTERCEPT = """
<script>
// Static demo: there is no backend on GitHub Pages, so block form posts.
document.addEventListener('submit', function (e) {
  e.preventDefault();
  alert('This is the static demo on GitHub Pages — form submissions are disabled.\\n\\nRun the live app for the full interactive site.');
}, true);
</script>
"""


def write_page(path: str, dest: str) -> None:
    r = client.get(path, follow_redirects=True)
    if r.status_code != 200:
        print(f"  SKIP {path} -> {r.status_code}")
        return
    html = fix_urls(r.text)
    if "</body>" in html:
        html = html.replace("</body>", FORM_INTERCEPT + "</body>")
    target = OUT / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    print(f"  {path} -> {dest} ({len(html)} bytes)")


print("Exporting public pages...")
write_page("/", "index.html")
write_page("/cars", "cars/index.html")

# Vehicle detail pages
conn = sqlite3.connect(BASE_DIR / "car_dealership.db")
ids = [r[0] for r in conn.execute("SELECT id FROM vehicles ORDER BY id")]
conn.close()
for vid in ids:
    write_page(f"/cars/{vid}", f"cars/{vid}/index.html")

write_page("/test-drives", "test-drives/index.html")
write_page("/applications", "applications/index.html")
write_page("/contact", "contact/index.html")
write_page("/test-drives/thanks", "test-drives/thanks/index.html")
write_page("/applications/thanks", "applications/thanks/index.html")
write_page("/contact/thanks", "contact/thanks/index.html")

# Static assets
print("Copying static assets...")
shutil.copytree(BASE_DIR / "static", OUT / "static")

# Custom 404
(OUT / "404.html").write_text(
    "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Not found</title></head>"
    "<body><h1>404 — page not found</h1><p><a href='/autostock-motors/'>Back to AutoStock Motors</a></p>"
    "</body></html>",
    encoding="utf-8",
)

print(f"\nDone. Exported to {OUT}")
