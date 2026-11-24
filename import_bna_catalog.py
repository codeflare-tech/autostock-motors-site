#!/usr/bin/env python3
"""Build the bundled BNA catalog manifest and copy its images into static/.

Run once from the project root. The generated catalog/bna_vehicles.json is what
init_db.seed_bna_catalog() loads on every boot (including fresh Render deploys).
The original download lives at /home/bongani/bna_motors and is not required at runtime.
"""
from __future__ import annotations

import json
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = "/home/bongani/bna_motors"
STATIC = os.path.join(ROOT, "static", "images", "bna")
MANIFEST = os.path.join(ROOT, "catalog", "bna_vehicles.json")

FUEL = {
    "PETROL": "Petrol", "DIESEL": "Diesel", "HYBRID": "Hybrid",
    "ELECTRIC": "Electric", "LPG": "LPG",
}
TRANS = {
    "manual": "Manual", "automatic": "Automatic", "cvt": "CVT",
    "dual clutch": "Dual Clutch",
}
BODY = {
    "Hatchback": "Hatchback", "Sedan": "Sedan", "SUV": "SUV",
    "Coupe": "Coupe", "Wagon": "Wagon", "Convertible": "Convertible",
    "Pickup": "Pickup", "Van": "Van", "Minivan": "Minivan",
    "Crossover": "SUV", "Crossover/SUV": "SUV",
    "Bakkie Single Cab": "Pickup", "Bakkie Double Cab": "Pickup",
    "MPV": "Minivan",
}


def _number(value, cast):
    try:
        return cast(str(value).strip())
    except (TypeError, ValueError):
        return None


def _city(location):
    low = (location or "").lower()
    for name in ("Parow", "Goodwood", "Cape Town", "Bellville"):
        if low.startswith(name.lower()):
            return name
    return None


def _copy_images(stock, images):
    """Copy images into static/ and return ordered URLs with a 1024px hero first."""
    dest_dir = os.path.join(STATIC, stock)
    os.makedirs(dest_dir, exist_ok=True)
    urls = []

    hero_src = None
    if images:
        candidate = images[0].get("large_local")
        if candidate and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
            hero_src = candidate

    if hero_src:
        shutil.copy2(hero_src, os.path.join(dest_dir, "00_hero.jpg"))
        urls.append(f"/static/images/bna/{stock}/00_hero.jpg")

    for n, item in enumerate(images, 1):
        if hero_src and n == 1:  # hero is image 1 at higher resolution
            continue
        src = item.get("web_local")
        if not src or not os.path.isfile(src) or os.path.getsize(src) == 0:
            continue
        ext = os.path.splitext(src)[1].lower() or ".jpg"
        name = f"{n:02d}{ext}"
        shutil.copy2(src, os.path.join(dest_dir, name))
        urls.append(f"/static/images/bna/{stock}/{name}")

    return urls


def build():
    with open(os.path.join(SRC, "products.json"), encoding="utf-8") as fh:
        records = json.load(fh)["products"]

    rows = []
    seen_vins = set()
    copied = 0

    for i, p in enumerate(records):
        stock = str(p.get("stock_no") or "").strip()
        if not stock:
            continue
        vin = (p.get("vin") or "").strip() or None
        if vin and vin in seen_vins:
            continue
        if vin:
            seen_vins.add(vin)

        photos = _copy_images(stock, p.get("images") or [])
        if not photos:
            continue
        copied += len(photos)

        extras = p.get("extras") or []
        extras_text = "; ".join(str(x) for x in extras if str(x).strip())
        description = (p.get("description") or "").strip()
        if extras_text:
            description = f"{description}\n\nFeatures: {extras_text}".strip()

        kw = _number(p.get("power_kw"), float)
        nm = _number(p.get("torque_nm"), float)
        cc = _number(p.get("engine_cc"), float)
        city = _city(p.get("branch_location"))

        rows.append({
            "stock_no": stock,
            "sort_order": 100 + i,
            "make": str(p.get("make") or "Unknown")[:60],
            "model": str(p.get("model") or p.get("title") or "Unknown")[:60],
            "year": _number(p.get("year"), int) or 2019,
            "price": _number(p.get("price_zar"), float) or 0,
            "currency": "ZAR",
            "mileage": _number(p.get("mileage_km"), float),
            "color": (p.get("color") or "").strip()[:40] or None,
            "fuel_type": FUEL.get((p.get("fuel") or "").upper(), "Petrol"),
            "transmission": TRANS.get((p.get("transmission") or "").lower(), "Automatic"),
            "body_type": BODY.get(p.get("body"), "Sedan"),
            "condition": "Used",
            "state": "New",  # the app's "available on the public site" flag
            "vin": vin,
            "trim": (p.get("variant") or "").strip()[:60] or None,
            "engine": f"{int(cc)} cc" if cc else None,
            "horsepower": round(kw * 1.34102) if kw else None,
            "torque": f"{int(nm)} Nm" if nm else None,
            "description": description,
            "short_description": (p.get("description") or "")[:500],
            "photos": photos,
            "offer": True,
            "show_on_home": i < 12,
            "featured": i < 4,
            "country": "South Africa",
            "province": "Western Cape" if city else None,
            "city": city,
        })

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump({"source": "https://bnamotors.co.za/",
                   "count": len(rows), "vehicles": rows}, fh, indent=1)

    print(f"Manifest: {MANIFEST}")
    print(f"Vehicles: {len(rows)}")
    print(f"Images copied: {copied}")
    return rows


if __name__ == "__main__":
    build()
