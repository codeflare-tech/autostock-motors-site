"""Admin routes: authentication, dashboard, vehicles, leads, applications, test drives, contacts, settings."""
from __future__ import annotations

import json
import os
import re
import base64
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from jinja2 import Undefined
from sqlalchemy import desc, func, and_
from sqlalchemy.orm import Session

import settings
from database import get_db
from models import (
    Vehicle, Application, Lead, TestDrive, Contact, Document, User,
    Setting, DocumentType, LeadSource, LeadStage, LeadStatus, Priority,
    ApplicationStatus, TestDriveStatus, BodyType, FuelType, Transmission,
    VehicleCondition,
)
from schemas import (
    VehicleCreate, VehicleUpdate, ApplicationCreate, ApplicationUpdate,
    LeadCreate, LeadUpdate, TestDriveCreate, TestDriveUpdate,
    ContactCreate, UserCreate,
)
from auth import hash_password, verify_password, create_access_token, decode_token

router = APIRouter()
# Use the compatibility template object (legacy TemplateResponse(name, context) signature,
# shared money filter and cache-disabled environment) from templates_config
from templates_config import templates_admin_compat as templates

# DEBUG: print template directory
import os as _os
print("ADMIN_TEMPLATES_DIR:", settings.TEMPLATES_DIR / "admin", "exists:", _os.path.exists(settings.TEMPLATES_DIR / "admin"))

ADMIN_PREFIX = "/admin"
UPLOAD_DIR = settings.UPLOAD_DIR
MEDIA_URL = settings.MEDIA_URL


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("admin_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter_by(id=int(payload["sub"]), is_superuser=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def login_required(f):
    from functools import wraps
    return f


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def admin_login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Invalid email format",
        }, status_code=400)
    user = db.query(User).filter_by(email=email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Invalid email or password",
        }, status_code=400)

    token = create_access_token(user.id, user.email, user.full_name)
    response = RedirectResponse(url="/admin/", status_code=303)
    response.set_cookie(
        key="admin_access_token", value=token,
        httponly=True, secure=False, samesite="lax", max_age=60*60*24*30,
    )
    return response


@router.post("/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_access_token")
    return response


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)  # auth check (raises 401 on failure)

    total_vehicles = db.query(Vehicle).filter_by(state="New").count()
    total_applications = db.query(Application).count()
    total_leads = db.query(Lead).count()
    total_test_drives = db.query(TestDrive).count()
    total_contacts = db.query(Contact).filter_by(status="New").count()
    today_apps = db.query(Application).filter(
        func.date(Application.created_at) == func.date(func.now())
    ).count()

    vehicles = db.query(Vehicle).filter_by(state="New").order_by(desc(Vehicle.created_at)).limit(5).all()
    applications = db.query(Application).order_by(desc(Application.created_at)).limit(5).all()
    leads = db.query(Lead).order_by(desc(Lead.created_at)).limit(5).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "vehicles": total_vehicles, "applications": total_applications,
            "leads": total_leads, "test_drives": total_test_drives,
            "contacts": total_contacts, "today_apps": today_apps,
        },
        "vehicles": [ _v_dict(v) for v in vehicles ],
        "applications": _apps_list(applications),
        "leads": [ l.data for l in leads ],
    })


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------
@router.get("/vehicles", response_class=HTMLResponse)
async def admin_vehicles(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    vehicles = db.query(Vehicle).filter_by(state="New").order_by(Vehicle.sort_order, desc(Vehicle.year)).all()
    return templates.TemplateResponse("vehicles.html", {
        "request": request, "vehicles": [_v_dict(v) for v in vehicles],
    })


@router.get("/vehicles/new", response_class=HTMLResponse)
async def admin_vehicle_new(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request, "vehicle": None, "mode": "add", "action": "/admin/vehicles",
        "makes": sorted({v.make for v in []}),
    })


@router.post("/vehicles")
async def admin_vehicle_create(
    request: Request,
    make: str = Form(...),
    model: str = Form(...),
    year: str = Form(...),
    price: str = Form(...),
    currency: str = Form("ZAR"),
    mileage: str = Form(""),
    color: str = Form(""),
    fuel_type: str = Form(...),
    transmission: str = Form(...),
    body_type: str = Form(...),
    condition: str = Form(...),
    state: str = Form("New"),
    vin: str = Form(""),
    chassis: str = Form(""),
    trim: str = Form(""),
    engine: str = Form(""),
    horsepower: str = Form(""),
    torque: str = Form(""),
    seats: str = Form(""),
    boot_space_l: str = Form(""),
    title: str = Form(""),
    description: str = Form(""),
    short_description: str = Form(""),
    photos: str = Form(""),
    show_on_home: str = Form("false"),
    featured: str = Form("false"),
    province: str = Form(""),
    city: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    try:
        year_i = int(year)
        price_f = float(price)
        mileage_f = float(mileage) if mileage else None
        boot_f = float(boot_space_l) if boot_space_l else None
        hp_i = int(horsepower) if horsepower else None
    except ValueError:
        return templates.TemplateResponse("vehicle_form.html", {
            "request": request, "error": "Year, price, mileage must be numbers",
        }, status_code=400)

    photos_list = json.loads(photos) if photos else []
    if isinstance(photos_list, str):  # single string wrapped
        photos_list = [photos_list]

    vehicle = Vehicle(
        make=make.strip(), model=model.strip(), year=year_i, price=price_f,
        currency=currency.upper(), mileage=mileage_f, color=color.strip() or None,
        fuel_type=fuel_type, transmission=transmission, body_type=body_type,
        condition=condition, state=state, vin=vin.strip() or None,
        chassis=chassis.strip() or None, trim=trim.strip() or None,
        engine=engine.strip() or None, horsepower=hp_i,
        torque=torque.strip() or None, seats=int(seats) if seats else None,
        boot_space_l=boot_f, title=title.strip() or None,
        description=description.strip() or None,
        short_description=short_description.strip() or None,
        photos=photos_list, show_on_home=show_on_home == "true",
        featured=featured == "true",
        province=province.strip() or None, city=city.strip() or None,
        address=address.strip() or None,
    )
    db.add(vehicle)
    db.flush()
    db.commit()
    return RedirectResponse(url="/admin/vehicles", status_code=303)


@router.get("/vehicles/{vehicle_id}/edit", response_class=HTMLResponse)
async def admin_vehicle_edit(request: Request, vehicle_id: int, db: Session = Depends(get_db)):
    get_current_user(request, db)
    v = db.query(Vehicle).filter_by(id=vehicle_id, state="New").first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request, "vehicle": _v_dict(v), "mode": "edit",
        "action": f"/admin/vehicles/{vehicle_id}",
    })


@router.post("/vehicles/{vehicle_id}")
async def admin_vehicle_update(
    request: Request, vehicle_id: int,
    make: str = Form(...), model: str = Form(...), year: str = Form(...),
    price: str = Form(...), currency: str = Form("ZAR"), mileage: str = Form(""),
    color: str = Form(""), fuel_type: str = Form(...), transmission: str = Form(...),
    body_type: str = Form(...), condition: str = Form(...), state: str = Form("New"),
    vin: str = Form(""), chassis: str = Form(""), trim: str = Form(""),
    engine: str = Form(""), horsepower: str = Form(""), torque: str = Form(""),
    seats: str = Form(""), boot_space_l: str = Form(""), title: str = Form(""),
    description: str = Form(""), short_description: str = Form(""),
    photos: str = Form(""), show_on_home: str = Form("false"),
    featured: str = Form("false"), province: str = Form(""),
    city: str = Form(""), address: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    v = db.query(Vehicle).filter_by(id=vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    try:
        v.make = make
        v.model = model
        v.year = int(year)
        v.price = float(price)
        v.currency = currency
        v.mileage = float(mileage) if mileage else None
        v.color = color or None
        v.fuel_type = fuel_type
        v.transmission = transmission
        v.body_type = body_type
        v.condition = condition
        v.state = state
        v.vin = vin or None
        v.chassis = chassis or None
        v.trim = trim or None
        v.engine = engine or None
        v.horsepower = int(horsepower) if horsepower else None
        v.torque = torque or None
        v.seats = int(seats) if seats else None
        v.boot_space_l = float(boot_space_l) if boot_space_l else None
        v.title = title or None
        v.description = description or None
        v.short_description = short_description or None
        v.photos = json.loads(photos) if photos else []
        v.show_on_home = show_on_home.lower() == "true"
        v.featured = featured.lower() == "true"
        v.province = province or None
        v.city = city or None
        v.address = address or None
        v.updated_at = datetime.utcnow()
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid form data")
    db.commit()
    return RedirectResponse(url="/admin/vehicles", status_code=303)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------
@router.get("/leads", response_class=HTMLResponse)
async def admin_leads(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    leads = db.query(Lead).order_by(desc(Lead.created_at)).all()
    return templates.TemplateResponse("leads.html", {
        "request": request, "leads": [_l_dict(l) for l in leads],
    })


@router.get("/leads/new", response_class=HTMLResponse)
async def admin_lead_new(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("lead_form.html", {"request": request})


@router.post("/leads")
async def admin_lead_create(
    request: Request,
    application_id: str = Form(""),
    vehicle_id: str = Form(""),
    lead_source: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    province: str = Form(""),
    city: str = Form(""),
    postal_code: str = Form(""),
    address: str = Form(""),
    notes: str = Form(""),
    stage: str = Form("New lead"),
    status: str = Form("Open"),
    priority: str = Form("Normal"),
    assigned_to: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    try:
        app_id = int(application_id) if application_id else None
        veh_id = int(vehicle_id) if vehicle_id else None
        assigned_id = int(assigned_to) if assigned_to else None
    except ValueError:
        return templates.TemplateResponse("lead_form.html", {
            "request": request, "error": "Invalid selected record",
        }, status_code=400)

    lead = Lead(
        application_id=app_id, vehicle_id=veh_id,
        lead_source=lead_source, full_name=full_name.strip(),
        email=email.strip().lower(), phone=phone.strip(),
        province=province.strip() or None, city=city.strip() or None,
        postal_code=postal_code.strip() or None,
        address=address.strip() or None, notes=notes.strip() or None,
        stage=stage, status=status, priority=priority, assigned_to_admin_id=assigned_id,
    )
    db.add(lead)
    db.commit()
    return RedirectResponse(url="/admin/leads", status_code=303)


@router.post("/leads/{lead_id}/stage")
async def admin_lead_stage(
    request: Request, lead_id: int,
    stage: str = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    lead = db.query(Lead).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.stage = stage
    lead.status = LeadStatus.Contacted if stage == "Contacted" else lead.status
    db.commit()
    return {"ok": True, "id": lead_id}


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
@router.get("/applications/new", response_class=HTMLResponse)
async def admin_application_new(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("application_form.html", {"request": request})


@router.get("/applications", response_class=HTMLResponse)
async def admin_applications(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    apps = db.query(Application).order_by(desc(Application.created_at)).all()
    return templates.TemplateResponse("applications.html", {
        "request": request, "applications": _apps_list(apps),
    })


@router.get("/applications/{application_id}", response_class=HTMLResponse)
async def admin_application_detail(request: Request, application_id: int, db: Session = Depends(get_db)):
    get_current_user(request, db)
    app = db.query(Application).filter_by(id=application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return templates.TemplateResponse("application_detail.html", {
        "request": request, "app": _app_detail(app), "documents": _app_docs(app),
    })


@router.post("/applications")
async def admin_application_create(
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
    get_current_user(request, db)
    try:
        year = int(preferred_year) if preferred_year else None
        budget_min_f = float(budget_min) if budget_min else None
        budget_max_f = float(budget_max) if budget_max else None
        provinces_list = json.loads(provinces) if provinces else None
        veh_id = int(vehicle_id) if vehicle_id else None
    except (ValueError, json.JSONDecodeError):
        return templates.TemplateResponse("application_form.html", {
            "request": request, "error": "Invalid form data",
        }, status_code=400)

    app = Application(
        full_name=full_name.strip(), email=email.strip().lower(),
        phone=phone.strip(), preferred_make=preferred_make.strip() or None,
        preferred_model=preferred_model.strip() or None, preferred_year=year,
        preferred_fuel=preferred_fuel.strip() or None,
        preferred_transmission=preferred_transmission.strip() or None,
        preferred_body=preferred_body.strip() or None,
        budget_min=budget_min_f, budget_max=budget_max_f,
        provinces=provinces_list, city=city.strip() or None,
        postal_code=postal_code.strip() or None,
        test_drive_needed=test_drive_needed == "true",
        trade_in_needed=trade_in_needed == "true",
        financing_needed=financing_needed == "true",
        message=message.strip() or None, source=source.strip() or None,
        referred_by=referred_by.strip() or None, vehicle_id=veh_id,
    )
    db.add(app)
    db.flush()
    db.commit()
    return RedirectResponse(url="/admin/applications", status_code=303)


@router.post("/applications/{application_id}/status")
async def admin_application_status(
    request: Request, application_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    app = db.query(Application).filter_by(id=application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.status = status
    app.replies_count = (app.replies_count or 0) + 1
    app.last_reply_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": application_id}


# ---------------------------------------------------------------------------
# Test drives
# ---------------------------------------------------------------------------
@router.get("/test-drives", response_class=HTMLResponse)
async def admin_test_drives(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    tds = db.query(TestDrive).order_by(TestDrive.appointment_date, TestDrive.time_slot).all()
    return templates.TemplateResponse("test_drives.html", {
        "request": request, "test_drives": [_td_dict(t) for t in tds],
    })


@router.post("/test-drives/{test_drive_id}/status")
async def admin_test_drive_status(
    request: Request, test_drive_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    td = db.query(TestDrive).filter_by(id=test_drive_id).first()
    if not td:
        raise HTTPException(status_code=404, detail="Test drive not found")
    td.status = status
    if status == TestDriveStatus.Completed:
        td.confirmed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": test_drive_id}


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
@router.get("/contacts", response_class=HTMLResponse)
async def admin_contacts(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    contacts = db.query(Contact).order_by(desc(Contact.created_at)).all()
    return templates.TemplateResponse("contacts.html", {
        "request": request, "contacts": [_c_dict(c) for c in contacts],
    })


@router.get("/contacts/new", response_class=HTMLResponse)
async def admin_contact_new(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("contact_form.html", {"request": request})


@router.post("/contacts")
async def admin_contact_create(
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
    get_current_user(request, db)
    contact = Contact(
        full_name=full_name.strip(), email=email.strip().lower(),
        phone=phone.strip(), category=category.strip(),
        subject=subject.strip() or None, message=message.strip(),
        source=source.strip() or None,
    )
    db.add(contact)
    db.commit()
    return RedirectResponse(url="/admin/contacts", status_code=303)


@router.post("/contacts/{contact_id}/reply")
async def admin_contact_reply(
    request: Request, contact_id: int,
    reply: str = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    c = db.query(Contact).filter_by(id=contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    c.status = "Replied"
    c.replies_count = (c.replies_count or 0) + 1
    c.last_reply_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "id": contact_id}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    settings_rows = db.query(Setting).all()
    return templates.TemplateResponse("settings.html", {
        "request": request, "settings": {s.key: s.value for s in settings_rows},
    })


@router.post("/settings")
async def admin_settings_save(
    request: Request,
    site_name: str = Form(""), site_tagline: str = Form(""),
    company_name: str = Form(""), company_address: str = Form(""),
    company_phone: str = Form(""), company_email: str = Form(""),
    company_website: str = Form(""), license_plates: str = Form(""),
    test_drive_hours: str = Form(""), show_on_homepage_count: str = Form("3"),
    key: str = Form(""), value: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    values = {
        "site_name": site_name, "site_tagline": site_tagline,
        "company_name": company_name, "company_address": company_address,
        "company_phone": company_phone, "company_email": company_email,
        "company_website": company_website, "license_plates": license_plates,
        "test_drive_hours": test_drive_hours,
        "show_on_homepage_count": show_on_homepage_count,
    }
    # Support both the full settings form and a single key/value update
    updates = values if not key else {key: value}
    for k, v in updates.items():
        if not v and k != "site_name":
            continue
        row = db.query(Setting).filter_by(key=k).first()
        if not row:
            db.add(Setting(key=k, value=v))
        else:
            row.value = v
    db.commit()
    return RedirectResponse(url="/admin/settings", status_code=303)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _v_dict(v: Vehicle) -> dict:
    return {
        "id": v.id, "make": v.make, "model": v.model, "year": v.year,
        "price": v.price, "price_formatted": v.price_formatted, "mileage": v.mileage, "color": v.color,
        "fuel_type": v.fuel_type, "transmission": v.transmission,
        "body_type": v.body_type, "condition": v.condition, "state": v.state,
        "vin": v.vin, "trim": v.trim, "engine": v.engine,
        "horsepower": v.horsepower, "torque": v.torque, "seats": v.seats,
        "boot_space_l": v.boot_space_l, "title": v.title or "",
        "description": v.description or "", "photos": v.photos or [],
        "offer": v.offer, "show_on_home": v.show_on_home, "featured": v.featured,
        "country": v.country, "province": v.province, "city": v.city,
        "address": v.address or "",
        "created_at": v.created_at.isoformat() if v.created_at else "",
    }


def _l_dict(l: Lead) -> dict:
    return {
        "id": l.id, "full_name": l.full_name, "email": l.email, "phone": l.phone,
        "stage": l.stage, "status": l.status, "priority": l.priority,
        "assigned_to": l.assigned_to_admin.full_name if l.assigned_to_admin else "",
        "created_at": l.created_at.isoformat() if l.created_at else "",
        "next_follow_up_due": l.next_follow_up_due.isoformat() if l.next_follow_up_due else "",
    }


def _apps_list(apps) -> list:
    return [
        {
            "id": a.id, "full_name": a.full_name, "email": a.email, "phone": a.phone,
            "preferred_make": a.preferred_make or "", "preferred_model": a.preferred_model or "",
            "preferred_year": a.preferred_year or "", "status": a.status,
            "test_drive_needed": a.test_drive_needed, "budget_min": a.budget_min or "",
            "created_at": a.created_at.isoformat() if a.created_at else "",
            "vehicle": a.vehicle,
        } for a in apps
    ]


def _app_detail(app: Application) -> dict:
    return {
        "id": app.id, "full_name": app.full_name, "email": app.email,
        "phone": app.phone, "preferred_make": app.preferred_make or "",
        "preferred_model": app.preferred_model or "", "preferred_year": app.preferred_year or "",
        "preferred_fuel": app.preferred_fuel or "", "preferred_transmission": app.preferred_transmission or "",
        "preferred_body": app.preferred_body or "", "budget_min": app.budget_min or "",
        "budget_max": app.budget_max or "", "provinces": app.provinces or "",
        "city": app.city or "", "postal_code": app.postal_code or "",
        "test_drive_needed": app.test_drive_needed, "trade_in_needed": app.trade_in_needed,
        "financing_needed": app.financing_needed, "message": app.message or "",
        "source": app.source or "", "referred_by": app.referred_by or "",
        "status": app.status, "replies_count": app.replies_count or 0,
        "last_reply_at": app.last_reply_at.isoformat() if app.last_reply_at else "",
        "created_at": app.created_at.isoformat() if app.created_at else "",
        "vehicle": _v_dict(app.vehicle) if app.vehicle else None,
    }


def _app_docs(app: Application) -> list:
    docs = app.documents or []  # InstrumentedList, already loaded
    return [
        {
            "id": d.id, "document_type": d.document_type,
            "file_name": d.file_name, "mime": d.mime,
            "size_bytes": d.size_bytes, "storage": d.storage,
            "data_url": d.data_url, "created_at": d.created_at.isoformat() if d.created_at else "",
        } for d in docs
    ]


@router.get("/test-drives/new", response_class=HTMLResponse)
async def admin_test_drive_new(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    vehicles = db.query(Vehicle).filter_by(state="New").order_by(Vehicle.year.desc(), Vehicle.make).all()
    return templates.TemplateResponse("test_drive_form.html", {
        "request": request, "vehicles": [_v_dict(v) for v in vehicles],
    })


@router.post("/test-drives")
async def admin_test_drive_create(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    vehicle_id: str = Form(""),
    appointment_date: str = Form(...),
    time_slot: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    try:
        veh_id = int(vehicle_id) if vehicle_id else None
        appt = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        return templates.TemplateResponse("test_drive_form.html", {
            "request": request, "error": "Invalid vehicle or date", "vehicles": db.query(Vehicle).filter_by(state='New').all(),
        }, status_code=400)

    test_drive = TestDrive(
        first_name=first_name.strip(), last_name=last_name.strip(),
        email=email.strip().lower(), phone=phone.strip(),
        vehicle_id=veh_id,
        appointment_date=appt,
        time_slot=time_slot.strip() or None,
        notes=notes.strip() or None,
    )
    db.add(test_drive)
    db.commit()
    return RedirectResponse(url="/admin/test-drives", status_code=303)


def _td_dict(td: TestDrive) -> dict:
    return {
        "id": td.id, "first_name": td.first_name, "last_name": td.last_name,
        "email": td.email, "phone": td.phone,
        "appointment_date": td.appointment_date.isoformat() if td.appointment_date else "",
        "time_slot": td.time_slot, "notes": td.notes or "",
        "status": td.status, "vehicle": _v_dict(td.vehicle) if td.vehicle else None,
    }


def _c_dict(c: Contact) -> dict:
    return {
        "id": c.id, "full_name": c.full_name, "email": c.email, "phone": c.phone,
        "category": c.category, "subject": c.subject or "", "message": c.message or "",
        "source": c.source or "", "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else "",
    }


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
@router.get("/documents/new", response_class=HTMLResponse)
async def admin_document_new(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("document_form.html", {"request": request})


@router.post("/documents")
async def admin_document_create(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form("Other"),
    application_id: str = Form(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    # Documents table requires application_id (NOT NULL). Use a selected app or the first available.
    app_id = int(application_id) if application_id.isdigit() else None
    if app_id is None:
        first_app = db.query(Application).order_by(Application.id).first()
        app_id = first_app.id if first_app else 1
    data_url = f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"
    doc = Document(
        application_id=app_id,
        file_name=file.filename or "document.bin",
        mime=mime,
        size_bytes=len(content),
        document_type=document_type,
        storage="base64",
        data_url=data_url,
    )
    db.add(doc)
    db.commit()
    return RedirectResponse(url="/admin/documents", status_code=303)


@router.get("/documents", response_class=HTMLResponse)
async def admin_documents(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return templates.TemplateResponse(request, "documents.html", {
        "documents": [{
            "id": d.id,
            "file_name": d.file_name,
            "document_type": d.document_type,
            "size_bytes": d.size_bytes,
            "created_at": d.created_at,
            "storage": d.storage,
        } for d in docs],
    })


@router.get("/documents/{document_id}/download")
async def admin_document_download(request: Request, document_id: int, db: Session = Depends(get_db)):
    get_current_user(request, db)
    doc = db.query(Document).filter_by(id=document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    headers = {"Content-Disposition": f'attachment; filename="{doc.file_name}"'}
    if doc.storage == "base64" and doc.data_url:
        # data URL format: data:<mime>;base64,<payload>
        payload = doc.data_url.split(",", 1)[1] if "," in doc.data_url else ""
        try:
            content = base64.b64decode(payload)
        except Exception:
            raise HTTPException(status_code=500, detail="Corrupt document data")
        return Response(content=content, media_type=doc.mime or "application/octet-stream", headers=headers)
    if doc.storage == "local":
        stored = getattr(doc, "data_url", None) or ""
        file_path = settings.UPLOAD_DIR / stored.split("/")[-1] if stored else None
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return Response(content=file_path.read_bytes(), media_type=doc.mime or "application/octet-stream", headers=headers)
    raise HTTPException(status_code=400, detail="Unsupported document storage")


# ---------------------------------------------------------------------------
# Media files (authenticated)
# ---------------------------------------------------------------------------
@router.get("/media/{filename:path}")
async def admin_media(request: Request, filename: str, db: Session = Depends(get_db)):
    get_current_user(request, db)
    # Only serve files in the uploads folder
    file_path = (settings.UPLOAD_DIR / filename).resolve()
    if not str(file_path).startswith(str(settings.UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "application/octet-stream"
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        media_type = "image/" + filename.rsplit(".", 1)[-1].upper()
    elif filename.lower().endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.lower().endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return Response(content=file_path.read_bytes(), media_type=media_type)
