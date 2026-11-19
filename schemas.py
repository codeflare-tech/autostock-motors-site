"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class OrmModel(BaseModel):
    """Base that can read SQLAlchemy ORM objects (model config from_attributes=True)."""
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------
class VehicleCreate(OrmModel):
    sort_order: int = 0
    make: str
    model: str
    year: int
    price: float
    currency: str = "ZAR"
    mileage: Optional[float] = None
    color: Optional[str] = None
    fuel_type: str
    transmission: str
    body_type: str
    condition: str
    state: str = "New"
    vin: Optional[str] = None
    chassis: Optional[str] = None
    trim: Optional[str] = None
    engine: Optional[str] = None
    horsepower: Optional[int] = None
    torque: Optional[str] = None
    seats: Optional[int] = None
    boot_space_l: Optional[float] = None
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    photos: Optional[list[str]] = None
    offer: bool = True
    show_on_home: bool = False
    featured: bool = False
    country: str = "South Africa"
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None


class VehicleOut(OrmModel):
    id: int
    sort_order: int
    make: str
    model: str
    year: int
    price: float
    currency: str
    mileage: Optional[float]
    color: Optional[str]
    fuel_type: str
    transmission: str
    body_type: str
    condition: str
    state: str
    vin: Optional[str]
    chassis: Optional[str]
    trim: Optional[str]
    engine: Optional[str]
    horsepower: Optional[int]
    torque: Optional[str]
    seats: Optional[int]
    boot_space_l: Optional[float]
    title: Optional[str]
    description: Optional[str]
    short_description: Optional[str]
    photos: Optional[list[str]]
    offer: bool
    show_on_home: bool
    featured: bool
    country: str
    province: Optional[str]
    city: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleUpdate(OrmModel):
    """Partial update — only fields present are updated."""
    sort_order: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    mileage: Optional[float] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    condition: Optional[str] = None
    state: Optional[str] = None
    vin: Optional[str] = None
    chassis: Optional[str] = None
    trim: Optional[str] = None
    engine: Optional[str] = None
    horsepower: Optional[int] = None
    torque: Optional[str] = None
    seats: Optional[int] = None
    boot_space_l: Optional[float] = None
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    photos: Optional[list[str]] = None
    offer: Optional[bool] = None
    show_on_home: Optional[bool] = None
    featured: Optional[bool] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None


# ---------------------------------------------------------------------------
# Application (online submission)
# ---------------------------------------------------------------------------
class ApplicationCreate(OrmModel):
    full_name: str
    email: EmailStr
    phone: str
    preferred_make: Optional[str] = None
    preferred_model: Optional[str] = None
    preferred_year: Optional[int] = None
    preferred_fuel: Optional[str] = None
    preferred_transmission: Optional[str] = None
    preferred_body: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    provinces: Optional[list[str]] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    test_drive_needed: bool = False
    trade_in_needed: bool = False
    financing_needed: bool = False
    message: Optional[str] = None
    source: Optional[str] = None
    referred_by: Optional[str] = None
    vehicle_id: Optional[int] = None


class ApplicationOut(OrmModel):
    id: int
    full_name: str
    email: str
    phone: str
    preferred_make: Optional[str]
    preferred_model: Optional[str]
    preferred_year: Optional[int]
    preferred_fuel: Optional[str]
    preferred_transmission: Optional[str]
    preferred_body: Optional[str]
    budget_min: Optional[float]
    budget_max: Optional[float]
    provinces: Optional[str]  # JSON string
    city: Optional[str]
    postal_code: Optional[str]
    test_drive_needed: bool
    trade_in_needed: bool
    financing_needed: bool
    message: Optional[str]
    source: Optional[str]
    referred_by: Optional[str]
    status: str
    replies_count: int
    last_reply_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    vehicle_id: Optional[int]
    vehicle: Optional[VehicleOut] = None

    class Config:
        from_attributes = True


class ApplicationUpdate(OrmModel):
    status: Optional[str] = None
    replies_count: Optional[int] = None
    last_reply_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------
class LeadCreate(OrmModel):
    application_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    lead_source: str
    full_name: str
    email: EmailStr
    phone: str
    province: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    stage: str = "New lead"
    status: str = "Open"
    priority: str = "Normal"
    assigned_to_admin_id: Optional[int] = None


class LeadOut(OrmModel):
    id: int
    application_id: Optional[int]
    vehicle_id: Optional[int]
    lead_source: str
    full_name: str
    email: str
    phone: str
    province: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    stage: str
    status: str
    priority: str
    assigned_to_admin_id: Optional[int]
    assigned_to_admin: Optional[dict] = None
    next_follow_up_due: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(OrmModel):
    stage: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_admin_id: Optional[int] = None
    next_follow_up_due: Optional[datetime] = None
    notes: Optional[str] = None


class LeadOutSimple(OrmModel):
    """Minimal shape used in the admin table list."""
    id: int
    full_name: str
    email: str
    phone: str
    stage: str
    status: str
    priority: str
    assigned_to_admin: Optional[str] = None
    created_at: datetime
    next_follow_up_due: Optional[datetime]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Test drive
# ---------------------------------------------------------------------------
class TestDriveCreate(OrmModel):
    application_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    lead_id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    appointment_date: str  # "YYYY-MM-DD"
    time_slot: str
    notes: Optional[str] = None
    status: str = "Booked"


class TestDriveOut(OrmModel):
    id: int
    application_id: Optional[int]
    vehicle_id: Optional[int]
    lead_id: Optional[int]
    first_name: str
    last_name: str
    email: str
    phone: str
    appointment_date: str
    time_slot: str
    notes: Optional[str]
    status: str
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleOut] = None

    class Config:
        from_attributes = True


class TestDriveUpdate(OrmModel):
    """Partial update for a test drive."""
    status: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
class ContactCreate(OrmModel):
    full_name: str
    email: EmailStr
    phone: str
    category: str
    subject: Optional[str] = None
    message: str
    source: Optional[str] = None


class ContactOut(OrmModel):
    id: int
    full_name: str
    email: str
    phone: str
    category: str
    subject: Optional[str]
    message: str
    source: Optional[str]
    status: str
    replies_count: int
    last_reply_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
class DocumentOut(OrmModel):
    id: int
    application_id: int
    document_type: str
    file_name: str
    mime: str
    size_bytes: int
    storage: str
    data_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class UserCreate(OrmModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    is_superuser: bool = False


class UserOut(OrmModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingOut(OrmModel):
    key: str
    value: str
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
