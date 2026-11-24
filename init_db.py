"""Initialise the database: create tables and seed the first superuser + demo data."""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, date
from json import dumps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from datetime import datetime, timedelta, date
from json import dumps

# Ensure the project root is importable when running as a module
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker

from models import (
    Base, User, Vehicle, Application, Lead, TestDrive, Contact, Document,
    Setting, DocumentType, FuelType, Transmission, BodyType,
    VehicleCondition, VehicleState, LeadSource, LeadStage, LeadStatus,
    Priority, ApplicationStatus, TestDriveStatus,
)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/car_dealership.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}
                       if DATABASE_URL.startswith("sqlite") else "")
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _hash(pw: str) -> str:
    import bcrypt
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def seed_superuser(db) -> int:
    existing = db.query(User).filter_by(email="admin@dealership.com").first()
    if existing:
        return existing.id
    uid = uuid.uuid4().int % (10 ** 8)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@dealership.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    user = User(
        id=uid,
        full_name="Dealership Administrator",
        email=admin_email,
        password_hash=_hash(admin_password),
        is_superuser=True,
        phone="+27 82 000 0000",
    )
    db.add(user)
    db.commit()
    return uid


def seed_demo_vehicles(db) -> list:
    vehicles = [
        # ---- NEW STOCK ----
        dict(make="Toyota", model="Land Cruiser", year=2024, price=899_000,
             fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.New,
             state=VehicleState.New, vin="4S1ZZZ159MA012345", chassis="12345ABC",
             trim="Premium", engine="5.7 L V8", horsepower=384, torque="553 Nm",
             seats=8, boot_space_l=722, title="Clear", country="South Africa",
             province="Gauteng", city="Johannesburg", address="Unit 4, Sandton Auto Park",
             short_description="2024 Toyota Land Cruiser 57. Pricey but pristine.",
             description="Exclusively imported 2024 Toyota Land Cruiser 57. Full service history, original number plate, pristine condition. Perfect for families who demand the best.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Land+Cruiser"],
             show_on_home=True, featured=True),
        dict(make="Mercedes-Benz", model="GLE 300d", year=2024, price=749_000,
             fuel_type=FuelType.Diesel, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.New,
             state=VehicleState.New, vin="WD2 cruiser", chassis="W168X24",
             trim="Launch Edition", engine="3.0 L dCi", horsepower=258,
             torque="550 Nm", seats=5, boot_space_l=630, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2024 Mercedes-Benz GLE 300d Luxury.",
             description="The GLE 300d combines diesel efficiency with Mercedes-Benz luxury. Pre-registered, low mileage.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=GLE+300d"],
             show_on_home=True, featured=True),
        dict(make="Hyundai", model="Tucson", year=2024, price=399_000,
             fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.New,
             state=VehicleState.New, vin="HR0725", chassis="H100-7XY",
             trim="S", engine="1.6 T-GDi", horsepower=239, torque="367 Nm",
             seats=5, boot_space_l=613, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2024 Hyundai Tucson S AT",
             description="Attractive subcompact SUV with strong warranty and low running costs.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Tucson+S"],
             show_on_home=True),
        dict(make="Volkswagen", model="Tiguan", year=2024, price=449_000,
             fuel_type=FuelType.Diesel, transmission=Transmission.DualClutch,
             body_type=BodyType.SUV, condition=VehicleCondition.New,
             state=VehicleState.New, vin="WCR0000", chassis="PQ35-V8Y",
             trim="Sun", engine="2.0 L TDI", horsepower=150, torque="340 Nm",
             seats=5, boot_space_l=680, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2024 Volkswagen Tiguan Sun",
             description="Spacious 7-seat wagon, efficient diesel, TSDi common-rail.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Tiguan"],
             show_on_home=True),
        dict(make="Ford", model="Turbine", year=2024, price=429_000,
             fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.New,
             state=VehicleState.New, vin="2FU7P3EX1NU123456", chassis="F150-F45",
             trim="ST-Line", engine="2.0 L EcoBoost", horsepower=245,
             torque="370 Nm", seats=5, boot_space_l=651, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2024 Ford Turbine ST-Line",
             description="Sporty SUV with aggressive styling and powerful engine.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Turbine"],
             show_on_home=True),
        # ---- USED STOCK ----
        dict(make="BMW", model="X5", year=2022, price=529_000, mileage=45_000,
             fuel_type=FuelType.Diesel, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.Used,
             state=VehicleState.Used, vin="WBA456123BR789012", chassis="F07-XY",
             trim="M Sport", engine="3.0 L dCi", horsepower=258, torque="550 Nm",
             seats=5, boot_space_l=710, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2022 BMW X5 M Sport - low mileage",
             description="One of only two X5 units imported new. Full service history available on request. Clean title.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=BMW+X5"],
             show_on_home=True, featured=True),
        dict(make="Audi", model="Q5", year=2022, price=419_000, mileage=38_000,
             fuel_type=FuelType.Diesel, transmission=Transmission.Automatic,
             body_type=BodyType.SUV, condition=VehicleCondition.Used,
             state=VehicleState.Used, vin="WAUZN1", chassis="4L5",
             trim="Prestige", engine="2.0 L TFSI", horsepower=204,
             torque="370 Nm", seats=5, boot_space_l=600, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2022 Audi Q5 Prestige diesel",
             description="Sophisticated premium SUV with quattro drive. Clean title.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Audi+Q5"],
             show_on_home=True),
        dict(make="Chevrolet", model="Malibu", year=2021, price=149_000,
             mileage=32_000, fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.Sedan, condition=VehicleCondition.Used,
             state=VehicleState.Used, vin="1G1WL5SE4KF312345", chassis="CLS-SF",
             trim="LS", engine="2.5 L", horsepower=172, torque="231 Nm",
             seats=5, boot_space_l=522, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2021 Chevrolet Malibu LS",
             description="Comfortable family sedan at a great price. Full service records available.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Malibu"],
             show_on_home=True),
        dict(make="Mazda", model="MX-5", year=2022, price=799_000, mileage=18_000,
             fuel_type=FuelType.Petrol, transmission=Transmission.Manual,
             body_type=BodyType.Coupe, condition=VehicleCondition.Used,
             state=VehicleState.Used, vin="JTDCJ7A54H4123456", chassis="ND-EC",
             trim="Build Week", engine="2.0 L", horsepower=162, torque="200 Nm",
             seats=2, boot_space_l=280, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2022 Mazda MX-5 Build Week",
             description="Pure driving pleasure. Iconic open-air roadster in excellent condition.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=MX-5"],
             show_on_home=True),
        dict(make="Toyota", model="Corolla", year=2023, price=319_000,
             mileage=12_000, fuel_type=FuelType.Petrol, transmission=Transmission.CVT,
             body_type=BodyType.Sedan, condition=VehicleCondition.New,
             state=VehicleState.New, vin="4T1P51D04GU123456", chassis="XA10-Z4",
             trim="TRD", engine="1.8 L", horsepower=140, torque="185 Nm",
             seats=5, boot_space_l=485, title="Clear",
             country="South Africa", province="KwaZulu-Natal", city="Durban",
             address="Unit 7, Point Shopping Centre",
             short_description="2023 Toyota Corolla TRD - unbeatable value",
             description="Dense, reliable, economical. The everyday driver's dream.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Corolla+TRD"],
             show_on_home=True),
        dict(make="Nissan", model="Patrol", year=2023, price=1_149_000,
             mileage=9_000, fuel_type=FuelType.Diesel, transmission=Transmission.Automatic,
             body_type=BodyType.Pickup, condition=VehicleCondition.New,
             state=VehicleState.New, vin="PCB1234", chassis="N16",
             trim="Pro-4x4", engine="3.0 L V6", horsepower=228, torque="385 Nm",
             seats=5, boot_space_l=772, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2023 Nissan Patrol Pro-4x4",
             description="King of the road. Rugged, reliable and ready for anything.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Nissan+Patrol"],
             show_on_home=True),
        dict(make="Mercedes-Benz", model="C 200", year=2021, price=329_000,
             mileage=31_000, fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.Sedan, condition=VehicleCondition.Used,
             state=VehicleState.Used, vin="W20550", chassis="C254",
             trim="Elegance", engine="1.8 L", horsepower=163, torque="270 Nm",
             seats=5, boot_space_l=470, title="Clear",
             country="South Africa", province="Western Cape", city="Cape Town",
             address="Unit 2, V&A Shopping Centre",
             short_description="2021 Mercedes-Benz C 200 Elegance",
             description="Elegant, refined and remarkably low mileage. Perfect first luxury car.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=C200"],
             show_on_home=True),
        dict(make="Porsche", model="911 Carrera", year=2024, price=3_290_000,
             fuel_type=FuelType.Petrol, transmission=Transmission.Automatic,
             body_type=BodyType.Coupe, condition=VehicleCondition.New,
             state=VehicleState.New, vin="992200567890123", chassis="992-11X",
             trim="S A 4.0", engine="3.0 L horizontally opposed 6", horsepower=379,
             torque="430 Nm", seats=2, boot_space_l=235, title="Clear",
             country="South Africa", province="Gauteng", city="Johannesburg",
             address="Unit 4, Sandton Auto Park",
             short_description="2024 Porsche 911 Carrera 4",
             description="One of six units imported new. An investment in the ultimate driving machine.",
             photos=["https://placehold.co/800x500/1a1a2e/e8e2d9?text=Porsche+911"],
             show_on_home=False, featured=True),
    ]

    created = []
    for v in vehicles:
        obj = Vehicle(**v)
        db.add(obj)
        db.flush()
        created.append(obj)
    db.commit()
    return created


def seed_demo_leads(db, vehicles: list, applications: list):
    """Auto-generate a few leads for demo purposes."""
    from datetime import timedelta, datetime, timezone
    now = datetime.now(timezone.utc)
    vehicle_ids = [v.id for v in vehicles]
    lead_defs = [
        (LeadSource.Website, "Sipho M", "sipho@example.com", "082 123 4567",
         "Gauteng", "Johannesburg", "2001",
         "Interested in the Land Cruiser", "New lead", "Open", "High"),
        (LeadSource.Website, "Nthabiseng P", "nthabi@example.com", "072 000 0001",
         "Gauteng", "Johannesburg", "2002",
         "Wants to test drive the Porsche", "Test drive set", "Appointment booked", "Normal"),
        (LeadSource.Phone, "Lindiwe N", "lindiwe@example.com", "061 000 0002",
         "KwaZulu-Natal", "Durban", "4001",
         "Family sedan under R400k", "Contacted", "Open", "Normal"),
        (LeadSource.Referral, "Tony D", "tony@example.com", "083 000 0003",
         "Western Cape", "Cape Town", "8001",
         "Trade-in enquiry", "Contacted", "Open", "Low"),
    ]
    created = []
    for i, (source, name, email, phone, province, city, zipcode,
            note, stage, status, priority) in enumerate(lead_defs):
        # attach to a vehicle if provided
        vid = vehicle_ids[i % len(vehicle_ids)] if vehicle_ids else None
        app = applications[i] if applications and i < len(applications) else None
        app_id = app.id if app else None
        lead = Lead(
            application_id=app_id,
            vehicle_id=vid,
            lead_source=source,
            full_name=name,
            email=email,
            phone=phone,
            province=province,
            city=city,
            postal_code=zipcode,
            notes=note,
            stage=stage,
            status=status,
            priority=priority,
            created_at=now - timedelta(days=i * 3, hours=i),
            next_follow_up_due=now + timedelta(days=i + 2),
        )
        db.add(lead)
        created.append(lead)
    db.commit()
    return created


def seed_demo_applications(db, vehicles: list):
    now = datetime.now().astimezone()
    app_defs = [
        dict(full_name="Sipho Mokoena", email="sipho@example.com", phone="082 123 4567",
             preferred_make="Toyota", preferred_model="Land Cruiser", preferred_year=2024,
             preferred_fuel=None, preferred_transmission=None, preferred_body=None,
             budget_min=800_000, budget_max=1_200_000, provinces=["Gauteng"],
             city="Johannesburg", postal_code="2001",
             test_drive_needed=True, trade_in_needed=True, financing_needed=False,
             message="We are a family of four. We want a reliable SUV for school runs.",
             source="Website", referred_by=None),
        dict(full_name="Nthabiseng Phalatse", email="nthabi@example.com", phone="072 000 0001",
             preferred_make="Porsche", preferred_model="911", preferred_year=2024,
             preferred_fuel=None, preferred_transmission=None, preferred_body=None,
             budget_min=None, budget_max=None, provinces=["Gauteng"],
             city="Johannesburg", postal_code="2001",
             test_drive_needed=True, trade_in_needed=False, financing_needed=True,
             message="Couple looking to upgrade to something special.",
             source="Website", referred_by="Existing customer"),
        dict(full_name="Lindiwe Ndlovu", email="lindiwe@example.com", phone="061 000 0002",
             preferred_make="Chevrolet", preferred_model="Malibu", preferred_year=2021,
             preferred_fuel=None, preferred_transmission=None, preferred_body=None,
             budget_min=120_000, budget_max=180_000, provinces=["KwaZulu-Natal"],
             city="Durban", postal_code="4001",
             test_drive_needed=False, trade_in_needed=False, financing_needed=True,
             message="Need a family sedan. Can pay cash.",
             source="Walk-in", referred_by=None),
        dict(full_name="Tony Daniels", email="tony@example.com", phone="083 000 0003",
             preferred_make="Ford", preferred_model="Turbine", preferred_year=2024,
             preferred_fuel=None, preferred_transmission=None, preferred_body=None,
             budget_min=None, budget_max=None, provinces=["Western Cape"],
             city="Cape Town", postal_code="8001",
             test_drive_needed=True, trade_in_needed=True, financing_needed=False,
             message="Trade in my old X6, thinking of a Truck.",
             source="Referral", referred_by=None),
        dict(full_name="Zinhle M", email="zinhle@example.com", phone="073 000 0004",
             preferred_make="Volkswagen", preferred_model="Tiguan", preferred_year=2024,
             preferred_fuel=None, preferred_transmission=None, preferred_body=None,
             budget_min=400_000, budget_max=500_000, provinces=["Gauteng"],
             city="Johannesburg", postal_code="2001",
             test_drive_needed=True, trade_in_needed=False, financing_needed=True,
             message="Planning a family with 3 kids.",
             source="Social", referred_by=None),
    ]
    created = []
    for i, d in enumerate(app_defs):
        d = dict(d)
        d["provinces"] = dumps(d.get("provinces") or [])
        app = Application(vehicle_id=vehicles[i % len(vehicles)].id, **d)
        db.add(app)
        db.flush()
        created.append(app)

    # test drives
    app_refs = [(now, "10:00", "Land Cruiser"),
                (now + timedelta(days=1), "14:00", "BMW X5"),
                (now + timedelta(days=2), "09:30", "Porsche 911"),
                (now + timedelta(days=3), "16:00", "Ford Turbine")]
    for i, (dt, slot, vin) in enumerate(app_refs):
        v = next((x for x in vehicles if x.vin and vin in x.vin), None)
        app = created[i]
        vd = TestDrive(
            application_id=app.id,
            vehicle_id=v.id if v else None,
            first_name=app.full_name.split()[0],
            last_name=app.full_name.split()[-1],
            email=app.email,
            phone=app.phone,
            appointment_date=dt.date(),
            time_slot=slot,
            status="Booked",
        )
        db.add(vd)
    db.commit()
    return created


def seed_bna_catalog():
    """Idempotently load the bundled BNA showroom stock (survives fresh DBs)."""
    manifest = os.path.join(BASE_DIR, "catalog", "bna_vehicles.json")
    if not os.path.isfile(manifest):
        return
    with open(manifest, encoding="utf-8") as fh:
        rows = json.load(fh).get("vehicles", [])
    if not rows:
        return

    db = SessionLocal()
    try:
        by_id = {v.id: v for v in db.query(Vehicle).all()}
        added = 0

        for i, data in enumerate(rows):
            values = dict(data)
            values.pop("stock_no", None)
            target_id = i + 1  # real stock takes over the placeholder slots
            row = by_id.get(target_id)
            if row is not None:
                for key, val in values.items():
                    setattr(row, key, val)
            else:
                db.add(Vehicle(id=target_id, **values))
                added += 1

        # The generated demo cars are not real stock - hide them from the
        # public site (which shows only state="New") without deleting them.
        hidden = 0
        for v in db.query(Vehicle).all():
            photos = v.photos or []
            if isinstance(photos, str):
                try:
                    photos = json.loads(photos)
                except (ValueError, TypeError):
                    photos = []
            if any(("placehold.co" in str(p) or "/static/images/vehicle-" in str(p))
                   for p in photos):
                if v.state != "Sold":
                    v.state = "Sold"
                    hidden += 1

        db.commit()
        print(f"✅ BNA catalog: {added} added, {hidden} demo cars hidden, "
              f"{db.query(func.count(Vehicle.id)).filter(Vehicle.state == 'New').scalar()} available")
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Only seed when the database is empty, so restarts/redeploys are safe.
        if db.query(User).count() > 0:
            print("✅ Database already seeded — skipping.")
            return
        seed_superuser(db)
        vehicles = seed_demo_vehicles(db)
        applications = seed_demo_applications(db, vehicles)
        seed_demo_leads(db, vehicles, applications)
        print("✅ Database initialised and demo data seeded.")
        print(f"   Superuser: {os.environ.get('ADMIN_EMAIL', 'admin@dealership.com')} / "
              f"{os.environ.get('ADMIN_PASSWORD', 'admin123')}")
        print(f"   Vehicles: {len(vehicles)}")
        print(f"   Applications: {len(applications)}")
        print(f"   Leads: {db.query(Lead).count()}")
        print(f"   Test drives: {db.query(TestDrive).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
