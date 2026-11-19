"""Data model for the Car Dealership platform."""
from __future__ import annotations

from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Date, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class FuelType(str, PyEnum):
    Petrol = "Petrol"
    Diesel = "Diesel"
    Electric = "Electric"
    Hybrid = "Hybrid"
    LPG = "LPG"


class Transmission(str, PyEnum):
    Manual = "Manual"
    Automatic = "Automatic"
    CVT = "CVT"
    DualClutch = "Dual Clutch"


class BodyType(str, PyEnum):
    Sedan = "Sedan"
    Hatchback = "Hatchback"
    SUV = "SUV"
    Coupe = "Coupe"
    Wagon = "Wagon"
    Convertible = "Convertible"
    Pickup = "Pickup"
    Van = "Van"
    Minivan = "Minivan"


class VehicleCondition(str, PyEnum):
    New = "New"
    Used = "Used"
    Demo = "Demo"


class VehicleState(str, PyEnum):
    New = "New"
    Used = "Used"
    Sold = "Sold"
    InService = "In Service"


class LeadSource(str, PyEnum):
    Website = "Website"
    Phone = "Phone"
    WalkIn = "Walk-in"
    ThirdParty = "Third-party"
    Social = "Social"
    Referral = "Referral"
    Event = "Event / Test-drive"


class LeadStage(str, PyEnum):
    NewLead = "New lead"
    Contacted = "Contacted"
    TestDriveSet = "Test drive set"
    Showed = "Showed"
    CreditApp = "Credit app / negotiation"
    DealAgreed = "Deal agreed"
    FinanceProcessing = "Finance processing"
    Sold = "Sold"
    Delivered = "Delivered"
    UnsoldNurture = "Unsold nurture"


class LeadStatus(str, PyEnum):
    Open = "Open"
    Contacted = "Contacted"
    Appointment = "Appointment booked"
    Negotiation = "Negotiating"
    Sold = "Sold"
    Lost = "Lost"


class Priority(str, PyEnum):
    Low = "Low"
    Normal = "Normal"
    High = "High"
    Urgent = "Urgent"


class ApplicationStatus(str, PyEnum):
    New = "New"
    Viewed = "Viewed"
    InReview = "In review"
    Approved = "Approved"
    Rejected = "Rejected"
    NoResponse = "No response"


class TradeInStatus(str, PyEnum):
    NotOffered = "Not offered"
    Valued = "Valued"
    Accepted = "Accepted"
    Declined = "Declined"


class TestDriveStatus(str, PyEnum):
    Booked = "Booked"
    Confirmed = "Confirmed"
    Completed = "Completed"
    Cancelled = "Cancelled"
    NoShow = "No show"


class DocumentType(str, PyEnum):
    ID = "ID"
    ProofOfAddress = "Proof of address"
    Payslip = "Payslip"
    BankStatement = "Bank statement"
    ProofOfIncome = "Proof of income"
    Other = "Other"


class Currency(str, PyEnum):
    ZAR = "ZAR"
    USD = "USD"
    EUR = "EUR"


# ---------------------------------------------------------------------------
# Settings (key/value)
# ---------------------------------------------------------------------------
class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(120), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_value(self, default=None):
        return self.value or default


# ---------------------------------------------------------------------------
# User (admin)
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    phone = Column(String(40), nullable=True)
    avatar = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    leads = relationship("Lead", back_populates="assigned_to_admin")
    applications = relationship("Application", back_populates="submitted_by")
    test_drives = relationship("TestDrive", back_populates="booked_by")


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    sort_order = Column(Integer, default=0)
    make = Column(String(60), nullable=False)
    model = Column(String(60), nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="ZAR")
    mileage = Column(Float, nullable=True)
    color = Column(String(40), nullable=True)
    fuel_type = Column(String(20), nullable=False)  # FuelType
    transmission = Column(String(20), nullable=False)  # Transmission
    body_type = Column(String(20), nullable=False)  # BodyType
    condition = Column(String(20), nullable=False)  # VehicleCondition
    state = Column(String(20), default="New", nullable=False)  # VehicleState
    vin = Column(String(100), unique=True, nullable=True)
    chassis = Column(String(100), nullable=True)
    trim = Column(String(60), nullable=True)
    engine = Column(String(40), nullable=True)
    horsepower = Column(Integer, nullable=True)
    torque = Column(String(20), nullable=True)
    seats = Column(Integer, nullable=True)
    boot_space_l = Column(Float, nullable=True)
    title = Column(String(40), nullable=True)  # "Clear" / "Collateral" / "Outstanding"
    description = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    photos = Column(JSON, nullable=True)  # list of image URLs
    offer = Column(Boolean, default=True, nullable=False)
    show_on_home = Column(Boolean, default=False, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)
    country = Column(String(60), default="South Africa")
    province = Column(String(60), nullable=True)
    city = Column(String(60), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    leads = relationship("Lead", back_populates="vehicle")
    applications = relationship("Application", back_populates="vehicle")
    test_drives = relationship("TestDrive", back_populates="vehicle")

    @property
    def price_nice(self) -> str:
        return f"{self.price:,.0f}" if self.price else "–"

    @property
    def price_formatted(self) -> str:
        return f"{self.price:,.0f}" if self.price else "0"

    @property
    def formatted_year(self) -> str:
        return str(self.year) if self.year else "–"


# ---------------------------------------------------------------------------
# Application (online inquiry form)
# ---------------------------------------------------------------------------
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(40), nullable=False)
    preferred_make = Column(String(60), nullable=True)
    preferred_model = Column(String(60), nullable=True)
    preferred_year = Column(Integer, nullable=True)
    preferred_fuel = Column(String(20), nullable=True)
    preferred_transmission = Column(String(20), nullable=True)
    preferred_body = Column(String(20), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    provinces = Column(Text, nullable=True)  # JSON list of provinces
    city = Column(String(80), nullable=True)
    postal_code = Column(String(20), nullable=True)
    test_drive_needed = Column(Boolean, default=False, nullable=False)
    trade_in_needed = Column(Boolean, default=False, nullable=False)
    financing_needed = Column(Boolean, default=False, nullable=False)
    message = Column(Text, nullable=True)
    source = Column(String(40), nullable=True)
    referred_by = Column(String(120), nullable=True)
    status = Column(String(20), default="New", nullable=False)  # ApplicationStatus
    replies_count = Column(Integer, default=0, nullable=False)
    last_reply_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vehicle = relationship("Vehicle", back_populates="applications")
    submitted_by = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    lead = relationship("Lead", uselist=False, back_populates="application", cascade="all, delete-orphan")

    def documents_by_type(self, doc_type: DocumentType):
        return [d for d in self.documents if d.document_type == doc_type]


# ---------------------------------------------------------------------------
# Document (uploads attached to an application)
# ---------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(40), nullable=False)  # DocumentType
    file_name = Column(String(120), nullable=False)
    mime = Column(String(60), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    storage = Column(String(20), default="base64", nullable=False)  # base64 / file
    data_url = Column(Text, nullable=True)  # base64 data URL when storage=base64
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="documents")
    user = relationship("User")


# ---------------------------------------------------------------------------
# Lead (CRM pipeline record)
# ---------------------------------------------------------------------------
class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)

    lead_source = Column(String(40), nullable=False)  # LeadSource
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(40), nullable=False)
    province = Column(String(60), nullable=True)
    city = Column(String(80), nullable=True)
    postal_code = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    stage = Column(String(40), default="New lead", nullable=False)  # LeadStage
    status = Column(String(20), default="Open", nullable=False)  # LeadStatus
    priority = Column(String(20), default="Normal", nullable=False)  # Priority

    assigned_to_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_admin = relationship("User", back_populates="leads")
    vehicle = relationship("Vehicle", back_populates="leads")
    application = relationship("Application", back_populates="lead")
    test_drives = relationship("TestDrive", back_populates="lead")
    next_follow_up_due = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def data(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "stage": self.stage,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to_admin.full_name if self.assigned_to_admin else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "next_follow_up_due": self.next_follow_up_due.isoformat() if self.next_follow_up_due else None,
        }


# ---------------------------------------------------------------------------
# Test drive appointment
# ---------------------------------------------------------------------------
class TestDrive(Base):
    __tablename__ = "test_drives"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    booked_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(40), nullable=False)
    appointment_date = Column(Date, nullable=False)
    time_slot = Column(String(40), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="Booked", nullable=False)  # TestDriveStatus
    confirmed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vehicle = relationship("Vehicle", back_populates="test_drives")
    application = relationship("Application")
    lead = relationship("Lead", back_populates="test_drives")
    booked_by = relationship("User", back_populates="test_drives")


# ---------------------------------------------------------------------------
# Complaint / feedback
# ---------------------------------------------------------------------------
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(40), nullable=False)
    category = Column(String(60), nullable=False)
    subject = Column(String(160), nullable=True)
    message = Column(Text, nullable=False)
    source = Column(String(40), nullable=True)
    status = Column(String(20), default="New", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    replies_count = Column(Integer, default=0, nullable=False)
    last_reply_at = Column(DateTime, nullable=True)
