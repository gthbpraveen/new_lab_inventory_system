from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class RoomLab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    staff_incharge = db.Column(db.String(100), nullable=True)
    cubicles = db.relationship("Cubicle", backref="room_lab", cascade="all, delete-orphan")

class Cubicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    room_lab_id = db.Column(db.Integer, db.ForeignKey("room_lab.id"), nullable=False)
    student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=True)

class Student(db.Model):
    roll = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(20))
    year = db.Column(db.String(10))
    joining_year = db.Column(db.String(10))
    faculty = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    workstation = db.relationship("Workstation", backref="student", uselist=False, cascade="all, delete")
    cubicle = db.relationship("Cubicle", backref="student", uselist=False)
    assigned_equipment = db.relationship("Equipment", backref="student", lazy=True)

class Workstation(db.Model):
    roll = db.Column(db.String(20), db.ForeignKey("student.roll"), primary_key=True)
    room_lab_name = db.Column(db.String(50))
    cubicle_no = db.Column(db.String(10))
    manufacturer = db.Column(db.String(100))
    otherManufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial = db.Column(db.String(100))
    os = db.Column(db.String(50))
    otherOs = db.Column(db.String(50))
    processor = db.Column(db.String(100))
    cores = db.Column(db.String(10))
    ram = db.Column(db.String(20))
    otherRam = db.Column(db.String(20))
    storage_type1 = db.Column(db.String(50))
    storage_capacity1 = db.Column(db.String(20))
    storage_type2 = db.Column(db.String(50))
    storage_capacity2 = db.Column(db.String(20))
    gpu = db.Column(db.String(100))
    vram = db.Column(db.String(10))
    issue_date = db.Column(db.String(20))
    system_required_till = db.Column(db.String(20))
    po_date = db.Column(db.String(20))
    source_of_fund = db.Column(db.String(100))
    keyboard_provided = db.Column(db.String(10))
    keyboard_details = db.Column(db.String(100))
    mouse_provided = db.Column(db.String(10))
    mouse_details = db.Column(db.String(100))
    monitor_provided = db.Column(db.String(20))
    monitor_details = db.Column(db.String(100))
    monitor_size = db.Column(db.String(10))
    monitor_serial = db.Column(db.String(100))
    mac_address = db.Column(db.String(50), nullable=True)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    invoice_number = db.Column(db.String(100), nullable=True)
    cost_per_unit = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    po_date = db.Column(db.String(20), nullable=True)
    purchase_date = db.Column(db.String(20), nullable=True)
    warranty_expiry = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default="Available")
    intender_name = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.String(200), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    department_code = db.Column(db.String(100), unique=True, nullable=True)
    mac_address = db.Column(db.String(50), nullable=True)

    assigned_to_roll = db.Column(
        db.String(20), 
        db.ForeignKey("student.roll", name="fk_equipment_assigned_to_roll"), 
        nullable=True
    )
    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)

class EquipmentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, nullable=False)
    assigned_to_roll = db.Column(
        db.String(20), 
        db.ForeignKey("student.roll", name="fk_equipment_history_assigned_to_roll"), 
        nullable=True
    )
    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    unassigned_date = db.Column(db.DateTime, nullable=True)
    status_snapshot = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ProvisioningRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(32), nullable=False)
    ip_address = db.Column(db.String(32), nullable=False)
    os_image = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

room_data = [
    ("CS-107", 43, "G Praveen Kumar"),
    ("CS-108", 21, "G Praveen Kumar"),
    ("CS-109", 114, "G Praveen Kumar"),
    ("CS-207", 30, "M Shiva Reddy"),
    ("CS-208", 25, "M Shiva Reddy"),
    ("CS-209", 142, "M Shiva Reddy"),
    ("CS-317", 25, "Sunitha M"),
    ("CS-318", 25, "Sunitha M"),
    ("CS-319", 32, "Sunitha M"),
    ("CS-320", 27, "Sunitha M"),
    ("CS-411", 25, "Mr Nikith Reddy"),
    ("CS-412", 33, "Mr Nikith Reddy")
]

def populate_room_and_cubicles():
    for name, capacity, staff in room_data:
        room = RoomLab(name=name, capacity=capacity, staff_incharge=staff)
        db.session.add(room)
        db.session.flush()
        for i in range(1, capacity + 1):
            cubicle = Cubicle(number=str(i), room_lab_id=room.id)
            db.session.add(cubicle)
    db.session.commit()
