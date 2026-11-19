"""Public-facing routes: home, listings, vehicle detail, applications, test drives, contact."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from jinja2 import Undefined
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

import settings
from database import get_db
from models import (
    Vehicle, Application, Lead, TestDrive, Contact, DocumentType,
    LeadSource, LeadStage, LeadStatus, Priority, ApplicationStatus,
    BodyType, FuelType, Transmission, TestDriveStatus, VehicleCondition,
)
from schemas import (
    VehicleCreate, VehicleUpdate, ApplicationCreate, ApplicationUpdate,
    LeadCreate, LeadUpdate, TestDriveCreate, TestDriveUpdate,
    ContactCreate,
)
from auth import hash_password, create_access_token, decode_token

router = APIRouter()
# Use the templates instance and render_template function from templates_config.py
# (both with cache disabled)
from templates_config import templates_public as templates, render_template

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _vehicle_dict(v: Vehicle) -> dict:
    photos = v.photos or []
    # Parse photos JSON string into list if needed
    if isinstance(photos, str):
        try:
            photos = json.loads(photos)
        except (json.JSONDecodeError, TypeError):
            photos = []
    
    # Extract actual values from SQLAlchemy model
    # SQLAlchemy columns return their values directly when accessed on an instance
    def _get_value(obj, field):
        val = getattr(obj, field, None)
        # Handle datetime objects that need to be converted to string
        if hasattr(val, 'isoformat') and not isinstance(val, str):
            return val.isoformat()
        return val
    
    price_val = _get_value(v, 'price')
    # Handle Decimal or other numeric types
    if hasattr(price_val, 'item'):
        price_val = price_val.item()
    
    return {
        "id": _get_value(v, 'id'), "make": _get_value(v, 'make'), 
        "model": _get_value(v, 'model'), "year": _get_value(v, 'year'),
        "price": price_val, 
        "price_formatted": f"{price_val:,.0f}" if price_val else "0",
        "mileage": _get_value(v, 'mileage'), "color": _get_value(v, 'color'),
        "fuel_type": _get_value(v, 'fuel_type'), "transmission": _get_value(v, 'transmission'),
        "body_type": _get_value(v, 'body_type'), "condition": _get_value(v, 'condition'), 
        "state": _get_value(v, 'state'),
        "vin": _get_value(v, 'vin'), "trim": _get_value(v, 'trim'), 
        "engine": _get_value(v, 'engine'), 
        "horsepower": _get_value(v, 'horsepower'),
        "torque": _get_value(v, 'torque'), "seats": _get_value(v, 'seats'), 
        "boot_space_l": _get_value(v, 'boot_space_l'),
        "title": _get_value(v, 'title'), "description": _get_value(v, 'description'),
        "short_description": _get_value(v, 'short_description'), 
        "photos": photos,
        "offer": _get_value(v, 'offer'), "show_on_home": _get_value(v, 'show_on_home'), 
        "featured": _get_value(v, 'featured'),
        "country": _get_value(v, 'country'), "province": _get_value(v, 'province'), 
        "city": _get_value(v, 'city'),
        "address": _get_value(v, 'address'), 
        "created_at": _get_value(v, 'created_at'),
        "updated_at": _get_value(v, 'updated_at'),
    }


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    featured = db.query(Vehicle).filter_by(featured=True, state="New").order_by(desc(Vehicle.created_at)).limit(4).all()
    popular = db.query(Vehicle).filter_by(state="New").order_by(desc(Vehicle.mileage)).limit(4).all()
    recent = db.query(Vehicle).filter_by(state="New").order_by(desc(Vehicle.created_at)).limit(4).all()
    stats = {
        "total": db.query(Vehicle).filter_by(state="New").count(),
        "new": db.query(Vehicle).filter_by(state="New", condition=VehicleCondition.New).count(),
        "used": db.query(Vehicle).filter_by(state="Used").count(),
        "suv": db.query(Vehicle).filter_by(body_type=BodyType.SUV).count(),
    }
    # Create a simple settings dict instead of passing the full settings module
    app_settings = {
        "site_name": "AutoStock Motors",
        "brand_confidence": 0,
    }
    return render_template(request, "index.html", {
        "featured": [ _vehicle_dict(v) for v in featured ],
        "popular": [ _vehicle_dict(v) for v in popular ],
        "recent": [ _vehicle_dict(v) for v in recent ],
        "stats": stats,
        "max_price": db.query(func.max(Vehicle.price)).scalar() or 0,
        "settings": app_settings,
    })

# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------
@router.get("/cars", response_class=HTMLResponse)
async def cars(request: Request,
               db: Session = Depends(get_db),
               make: str = None, model: str = None, min_year: int = None,
               max_year: int = None, max_price: float = None,
               body_type: str = None, fuel_type: str = None,
               transmission: str = None, search: str = None):
    q = db.query(Vehicle).filter(Vehicle.state == "New")
    if make: q = q.filter(Vehicle.make.ilike(f"%{make}%"))
    if model: q = q.filter(Vehicle.model.ilike(f"%{model}%"))
    if min_year: q = q.filter(Vehicle.year >= int(min_year))
    if max_year: q = q.filter(Vehicle.year <= int(max_year))
    if max_price: q = q.filter(Vehicle.price <= float(max_price))
    if body_type: q = q.filter(Vehicle.body_type == BodyType(body_type))
    if fuel_type: q = q.filter(Vehicle.fuel_type == FuelType(fuel_type))
    if transmission: q = q.filter(Vehicle.transmission == Transmission(transmission))
    if search:
        like = f"%{search}%"
        q = q.filter((Vehicle.make.ilike(like)) | (Vehicle.model.ilike(like)) | (Vehicle.trim.ilike(like)))
    vehicles = q.order_by(Vehicle.sort_order, desc(Vehicle.year)).all()
    makes = sorted({v.make for v in vehicles})
    body_types = sorted({v.body_type for v in vehicles})
    fuel_types = sorted({v.fuel_type for v in vehicles})
    transmissions = sorted({v.transmission for v in vehicles})
    # Convert query_params to a plain dict, excluding the request object
    filters = {}
    for k, v in request.query_params.items():
        if k != "request":
            filters[k] = v
    request_params = dict(filters)
    return render_template(request, "cars.html", {
        "vehicles": [ _vehicle_dict(v) for v in vehicles ],
        "makes": makes, "body_types": body_types, "fuel_types": fuel_types,
        "transmissions": transmissions,
        "filters": filters,
        "request_params": request_params,
        "selected_models": [v.model for v in vehicles],
    })


# ---------------------------------------------------------------------------
# Vehicle detail
# ---------------------------------------------------------------------------
@router.get("/cars/{vehicle_id}", response_class=HTMLResponse)
async def vehicle_detail(request: Request, vehicle_id: int,
                         db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter_by(id=vehicle_id, state="New").first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    # related: same make, other stock
    related = db.query(Vehicle).filter(
        Vehicle.make == v.make, Vehicle.id != v.id, Vehicle.state == "New"
    ).order_by(func.random()).limit(3).all()
    # Convert query_params to a plain dict, excluding the request object
    request_params = {}
    for k, val in request.query_params.items():
        if k != "request":
            request_params[k] = val
    return render_template(request, "vehicle.html", {
        "vehicle": _vehicle_dict(v),
        "related": [ _vehicle_dict(rv) for rv in related ],
        "request_params": request_params,
    })


# ---------------------------------------------------------------------------
# Online application (submit)
# ---------------------------------------------------------------------------
@router.post("/applications/submit")
async def application_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    preferred_make: str = Form(""),
    preferred_model: str = Form(""),
    preferred_year: str = Form(""),
    preferred_fuel: str = Form(""),
    preferred_transmission: str = Form(""),
    preferred_body: str = Form(""),
    budget_min: str = Form(""),
    budget_max: str = Form(""),
    provinces: str = Form(""),
    city: str = Form(""),
    postal_code: str = Form(""),
    test_drive_needed: str = Form("false"),
    trade_in_needed: str = Form("false"),
    financing_needed: str = Form("false"),
    message: str = Form(""),
    source: str = Form(""),
    referred_by: str = Form(""),
    vehicle_id: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        year = int(preferred_year) if preferred_year else None
        budget_min_f = float(budget_min) if budget_min else None
        budget_max_f = float(budget_max) if budget_max else None
        provinces_list = json.loads(provinces) if provinces else None
        vehicle_id_int = int(vehicle_id) if vehicle_id else None
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid form data")

    # Email validation
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    app = Application(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        preferred_make=preferred_make.strip() or None,
        preferred_model=preferred_model.strip() or None,
        preferred_year=year,
        preferred_fuel=preferred_fuel.strip() or None,
        preferred_transmission=preferred_transmission.strip() or None,
        preferred_body=preferred_body.strip() or None,
        budget_min=budget_min_f,
        budget_max=budget_max_f,
        provinces=json.dumps(provinces_list) if provinces_list else None,
        city=city.strip() or None,
        postal_code=postal_code.strip() or None,
        test_drive_needed=test_drive_needed == "true",
        trade_in_needed=trade_in_needed == "true",
        financing_needed=financing_needed == "true",
        message=message.strip() or None,
        source=source.strip() or None,
        referred_by=referred_by.strip() or None,
        vehicle_id=vehicle_id_int,
    )
    db.add(app)
    db.flush()

    # Auto-create a lead for the CRM pipeline
    lead = Lead(
        application_id=app.id,
        vehicle_id=vehicle_id_int,
        lead_source=LeadSource.Website,
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        city=city.strip() or None,
        postal_code=postal_code.strip() or None,
        notes=message.strip() or None,
        stage="New lead",
        status="Open",
        priority="High" if test_drive_needed else "Normal",
    )
    db.add(lead)
    db.commit()

    return RedirectResponse(url="/applications/thanks", status_code=303)


# ---------------------------------------------------------------------------
# Test drive booking
# ---------------------------------------------------------------------------
@router.post("/test-drives/book")
async def test_drive_book(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    application_id: str = Form(""),
    vehicle_id: str = Form(""),
    appointment_date: str = Form(...),
    time_slot: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    app_id_int = int(application_id) if application_id else None
    veh_id_int = int(vehicle_id) if vehicle_id else None

    # Validate vehicle date sanity (no past dates, no weekends)
    try:
        from datetime import date as _date
        appt = _date.fromisoformat(appointment_date)
        if appt < datetime.utcnow().date():
            raise HTTPException(status_code=400, detail="Appointment date must be in the future")
        if appt.weekday() >= 5:
            raise HTTPException(status_code=400, detail="Appointment must be on a weekday")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")

    # Check slot availability
    booked = db.query(TestDrive).filter_by(appointment_date=appt, status="Booked").count()
    if booked >= 6:
        raise HTTPException(status_code=400, detail="All slots for this date are full")

    td = TestDrive(
        application_id=app_id_int,
        vehicle_id=veh_id_int,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        appointment_date=appt,
        time_slot=time_slot.strip(),
        notes=notes.strip() or None,
        status="Booked",
    )
    db.add(td)
    db.commit()

    return RedirectResponse(url="/test-drives/thanks", status_code=303)


# ---------------------------------------------------------------------------
# GET routes for application and test drive forms
# ---------------------------------------------------------------------------
@router.get("/applications", response_class=HTMLResponse)
async def application_form(request: Request):
    return render_template(request, "application.html", {})


@router.get("/test-drives", response_class=HTMLResponse)
async def test_drive_form(request: Request):
    return render_template(request, "testdrive.html", {})
@router.get("/applications/thanks", response_class=HTMLResponse)
async def application_thanks(request: Request):
    return render_template(request, "application_thanks.html", {})


@router.get("/test-drives/thanks", response_class=HTMLResponse)
async def test_drive_thanks(request: Request):
    return render_template(request, "testdrive_thanks.html", {})


# ---------------------------------------------------------------------------
# Contact form
# ---------------------------------------------------------------------------
@router.get("/contact", response_class=HTMLResponse)
async def contact_form(request: Request):
    return render_template(request, "contact.html", {})


@router.post("/contact")
async def contact_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    category: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...),
    source: str = Form(""),
    db: Session = Depends(get_db),
):
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    contact = Contact(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        category=category.strip(),
        subject=subject.strip() or None,
        message=message.strip(),
        source=source.strip() or None,
    )
    db.add(contact)
    db.commit()

    return RedirectResponse(url="/contact/thanks", status_code=303)


@router.get("/contact/thanks", response_class=HTMLResponse)
async def contact_thanks(request: Request):
    return render_template(request, "contact_thanks.html", {})


# ---------------------------------------------------------------------------
# API: list vehicles (JSON)
# ---------------------------------------------------------------------------
@router.get("/api/vehicles")
async def api_vehicles(
    make: str = None, body_type: str = None, fuel: str = None,
    min_year: int = None, max_year: int = None, max_price: float = None,
    db: Session = Depends(get_db),
):
    q = db.query(Vehicle).filter(Vehicle.state == "New")
    if make: q = q.filter(Vehicle.make.ilike(f"%{make}%"))
    if body_type: q = q.filter(Vehicle.body_type == BodyType(body_type))
    if fuel: q = q.filter(Vehicle.fuel_type == FuelType(fuel))
    if min_year: q = q.filter(Vehicle.year >= int(min_year))
    if max_year: q = q.filter(Vehicle.year <= int(max_year))
    if max_price: q = q.filter(Vehicle.price <= float(max_price))
    vehicles = q.order_by(Vehicle.sort_order, desc(Vehicle.year)).all()
    return {"items": [_vehicle_dict(v) for v in vehicles]}


# ---------------------------------------------------------------------------
# API: get a single vehicle (JSON)
# ---------------------------------------------------------------------------
@router.get("/api/vehicles/{vehicle_id}")
async def api_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter_by(id=vehicle_id, state="New").first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return _vehicle_dict(v)
