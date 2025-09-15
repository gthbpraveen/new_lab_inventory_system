# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# IMPORTANT: app.py must import this db and call db.init_app(app)
db = SQLAlchemy()


# -------------------------
# Auth / Users (unchanged)
# -------------------------
# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(150), unique=True, nullable=False, index=True)
#     password = db.Column(db.String(150), nullable=False)
#     is_approved = db.Column(db.Boolean, default=False)
#     reset_token = db.Column(db.String(100), nullable=True)
#     reset_token_expiry = db.Column(db.DateTime, nullable=True)
#     registered_at = db.Column(db.DateTime, default=datetime.utcnow)
#     approved_at = db.Column(db.DateTime, nullable=True)
#     is_active = db.Column(db.Boolean, default=True)

#     def __repr__(self) -> str:
#         return f"<User {self.email}>"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin, staff, faculty, student
    is_approved = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

# -------------------------
# Rooms & Seating
# -------------------------
class RoomLab(db.Model):
    __tablename__ = "room_lab"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    staff_incharge = db.Column(db.String(100), nullable=True)

    cubicles = db.relationship(
        "Cubicle",
        backref="room_lab",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self) -> str:
        return f"<RoomLab {self.name} cap={self.capacity}>"


class Cubicle(db.Model):
    __tablename__ = "cubicle"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    room_lab_id = db.Column(db.Integer, db.ForeignKey("room_lab.id"), nullable=False)
    # Occupant (optional)
    student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Cubicle {self.number} room={self.room_lab_id} student={self.student_roll}>"


# -------------------------
# Students
# -------------------------
class Student(db.Model):
    __tablename__ = "student"
    roll = db.Column(db.String(20), primary_key=True)  # e.g., cs24mtech11091
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(20))
    year = db.Column(db.String(10))
    joining_year = db.Column(db.String(10))
    faculty = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))

    # 🔑 Link to User table
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("student", uselist=False))

    # Seat (one cubicle at a time)
    cubicle = db.relationship("Cubicle", backref="student", uselist=False)

    # Equipment assigned to this student
    assigned_equipment = db.relationship("Equipment", backref="student", lazy=True)

    # Workstation assignment history (zero or many over time)
    workstation_assignments = db.relationship(
        "WorkstationAssignment",
        backref="student",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def active_assignment(self):
        """Return the current active workstation assignment (if any)."""
        return next((a for a in self.workstation_assignments if a.is_active), None)

    def __repr__(self) -> str:
        return f"<Student {self.roll} {self.name}>"


# -------------------------
# IT Equipment (unchanged shape)
# -------------------------
class Equipment(db.Model):
    __tablename__ = "equipment"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
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
        nullable=True,
        index=True,
    )
    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Equipment {self.name} SN={self.serial_number} to={self.assigned_to_roll}>"


class EquipmentHistory(db.Model):
    __tablename__ = "equipment_history"
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, nullable=False, index=True)
    assigned_to_roll = db.Column(
        db.String(20),
        db.ForeignKey("student.roll", name="fk_equipment_history_assigned_to_roll"),
        nullable=True,
        index=True,
    )
    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    unassigned_date = db.Column(db.DateTime, nullable=True)
    status_snapshot = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EquipmentHistory eq={self.equipment_id} to={self.assigned_to_roll}>"


# -------------------------
# Provisioning Requests (PXE, etc.)
# -------------------------
class ProvisioningRequest(db.Model):
    __tablename__ = "provisioning_request"
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(32), nullable=False, index=True)
    ip_address = db.Column(db.String(32), nullable=False)
    os_image = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProvisioningRequest {self.mac_address} {self.os_image}>"


# # -------------------------
# # NEW: Workstation Inventory (separate from seating)
# # -------------------------
# class WorkstationAsset(db.Model):
#     """
#     A physical machine in inventory (reusable).
#     No room/cubicle fields here—seating is separate.
#     """
#     __tablename__ = "workstation_asset"
#     id = db.Column(db.Integer, primary_key=True)  # auto-increment asset ID

#     # Identity & specs
#     manufacturer = db.Column(db.String(100))
#     otherManufacturer = db.Column(db.String(100))
#     model = db.Column(db.String(100))
#     serial = db.Column(db.String(100), unique=True, index=True)  # recommended unique
#     os = db.Column(db.String(50))
#     otherOs = db.Column(db.String(50))
#     processor = db.Column(db.String(100))
#     cores = db.Column(db.String(10))
#     ram = db.Column(db.String(20))
#     otherRam = db.Column(db.String(20))
#     storage_type1 = db.Column(db.String(50))
#     storage_capacity1 = db.Column(db.String(20))
#     storage_type2 = db.Column(db.String(50))
#     storage_capacity2 = db.Column(db.String(20))
#     gpu = db.Column(db.String(100))
#     vram = db.Column(db.String(10))

#     # Peripherals are properties of the machine (not the person)
#     keyboard_provided = db.Column(db.String(10))
#     keyboard_details = db.Column(db.String(100))
#     mouse_provided = db.Column(db.String(10))
#     mouse_details = db.Column(db.String(100))
#     monitor_provided = db.Column(db.String(20))
#     monitor_details = db.Column(db.String(100))
#     monitor_size = db.Column(db.String(10))
#     monitor_serial = db.Column(db.String(100))
#     mac_address = db.Column(db.String(50), nullable=True)

#     # Procurement (asset-level)
#     po_date = db.Column(db.String(20))
#     source_of_fund = db.Column(db.String(100))

#     # Lifecycle status
#     # in_stock | assigned | retired
#     status = db.Column(db.String(20), default="in_stock", index=True)

#     # 🔹 New fields
#     location = db.Column(db.String(100))   # Lab/Dept/Other location
#     indenter = db.Column(db.String(100))   # Professor/Staff name (who owns/initiated purchase)

#     assignments = db.relationship(
#         "WorkstationAssignment",
#         backref="asset",
#         cascade="all, delete-orphan",
#         lazy=True,
#     )

#     def __repr__(self) -> str:
#         return (
#             f"<WSAsset id={self.id} serial={self.serial} "
#             f"status={self.status} location={self.location} indenter={self.indenter}>"
#         )

# -------------------------
# NEW: Workstation Inventory (separate from seating)
# -------------------------
class WorkstationAsset(db.Model):
    """
    A physical machine in inventory (reusable).
    No room/cubicle fields here—seating is separate.
    """
    __tablename__ = "workstation_asset"
    id = db.Column(db.Integer, primary_key=True)  # auto-increment asset ID

    # Identity & specs
    manufacturer = db.Column(db.String(100))
    otherManufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial = db.Column(db.String(100), unique=True, index=True)  # recommended unique
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

    # Peripherals
    keyboard_provided = db.Column(db.String(10))
    keyboard_details = db.Column(db.String(100))
    mouse_provided = db.Column(db.String(10))
    mouse_details = db.Column(db.String(100))
    monitor_provided = db.Column(db.String(20))
    monitor_details = db.Column(db.String(100))
    monitor_size = db.Column(db.String(10))
    monitor_serial = db.Column(db.String(100))
    mac_address = db.Column(db.String(50), nullable=True)

    # Procurement
    po_date = db.Column(db.String(20))
    source_of_fund = db.Column(db.String(100))

    # Lifecycle status
    status = db.Column(db.String(20), default="in_stock", index=True)

    # New fields
    location = db.Column(db.String(100))   # Lab/Dept/Other location
    indenter = db.Column(db.String(100))   # Faculty/Staff who raised PO

    # 🔹 Department Code (new)
    department_code = db.Column(db.String(200), unique=True, index=True)

    assignments = db.relationship(
        "WorkstationAssignment",
        backref="asset",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self) -> str:
        return (
            f"<WSAsset id={self.id} serial={self.serial} dept_code={self.department_code} "
            f"status={self.status} location={self.location} indenter={self.indenter}>"
        )

class WorkstationAssignment(db.Model):
    """
    One row per assignment (history).
    When returned, mark is_active = False and set end_date.
    """
    __tablename__ = "workstation_assignment"
    id = db.Column(db.Integer, primary_key=True)
    workstation_id = db.Column(db.Integer, db.ForeignKey("workstation_asset.id"), nullable=False, index=True)
    student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=False, index=True)

    # Assignment timing
    issue_date = db.Column(db.String(20), nullable=False)
    system_required_till = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=True)  # when returned

    # Optional notes
    remarks = db.Column(db.String(200))

    # Fast flag
    is_active = db.Column(db.Boolean, default=True, index=True)

    def __repr__(self) -> str:
        return f"<WSAssign asset={self.workstation_id} roll={self.student_roll} active={self.is_active}>"



class SlurmAccount(db.Model):
    __tablename__ = "slurm_account"
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(
        db.String(20),
        db.ForeignKey("student.roll"),   # ✅ Correct FK
        nullable=False,
        unique=True
    )
    status = db.Column(db.String(20), nullable=False, default="active")


# -------------------------
# Defaults & Seed helper
# -------------------------
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
    ("CS-412", 33, "Mr Nikith Reddy"),
]


def populate_room_and_cubicles(force=False):
    """
    Populate RoomLab and Cubicle from room_data.
    - If force=False, will do nothing if rooms already exist.
    - If force=True, will insert even if rooms exist (be careful!).
    """
    if not force:
        # Skip if any rooms exist
        if RoomLab.query.count() > 0:
            return

    for name, capacity, staff in room_data:
        room = RoomLab(name=name, capacity=capacity, staff_incharge=staff)
        db.session.add(room)
        db.session.flush()
        for i in range(1, capacity + 1):
            db.session.add(Cubicle(number=str(i), room_lab_id=room.id))
    db.session.commit()