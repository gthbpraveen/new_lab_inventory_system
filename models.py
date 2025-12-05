# from flask_sqlalchemy import SQLAlchemy
# from flask_login import UserMixin
# from datetime import datetime, date

# # IMPORTANT: app.py must import this db and call db.init_app(app)
# db = SQLAlchemy()


# # -------------------------
# # Auth / Users
# # -------------------------
# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(150), unique=True, nullable=False, index=True)
#     password = db.Column(db.String(255), nullable=False)
#     role = db.Column(db.String(20), nullable=False, default="student")  # admin, staff, faculty, student
#     is_approved = db.Column(db.Boolean, default=False)
#     reset_token = db.Column(db.String(200), nullable=True)
#     reset_token_expiry = db.Column(db.DateTime, nullable=True)
#     registered_at = db.Column(db.DateTime, default=datetime.utcnow)
#     approved_at = db.Column(db.DateTime, nullable=True)
#     is_active = db.Column(db.Boolean, default=True)

#     # Links to profile (optional): a user may be linked to either a student, faculty OR staff profile
#     student = db.relationship('Student', back_populates='user', uselist=False, cascade='all, delete')
#     faculty = db.relationship('Faculty', back_populates='user', uselist=False, cascade='all, delete')
#     staff = db.relationship('Staff', back_populates='user', uselist=False, cascade='all, delete')

#     def __repr__(self) -> str:
#         return f"<User {self.email} ({self.role})>"


# # -------------------------
# # Association table: Staff <-> RoomLab (lab incharge, many-to-many)
# # -------------------------
# staff_lab_incharge = db.Table(
#     'staff_lab_incharge',
#     db.Column('staff_id', db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'), primary_key=True),
#     db.Column('room_lab_id', db.Integer, db.ForeignKey('room_lab.id', ondelete='CASCADE'), primary_key=True)
# )


# # -------------------------
# # Faculty
# # -------------------------
# class Faculty(db.Model):
#     __tablename__ = "faculty"
#     id = db.Column(db.Integer, primary_key=True)
#     faculty_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # human-friendly ID
#     name = db.Column(db.String(120), nullable=False)
#     doj = db.Column(db.Date, nullable=False)                        # Date of joining
#     email = db.Column(db.String(150), unique=True, nullable=False, index=True)
#     mobile = db.Column(db.String(20), nullable=True)
#     room = db.Column(db.String(50), nullable=True)
#     years_exp = db.Column(db.Integer, nullable=True)                # can be computed from doj
#     designation = db.Column(db.String(50), nullable=False)         # Professor, Assistant Professor, ...
#     profile_photo = db.Column(db.String(200), nullable=True)       # filename/path
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     # Optional link to User (if you want login for faculty accounts)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
#     user = db.relationship('User', back_populates='faculty')

#     # Relationships to assets/assignments
#     workstation_assignments = db.relationship(
#         'WorkstationAssignment',
#         backref='faculty_owner',
#         cascade='all, delete-orphan',
#         lazy=True,
#         foreign_keys='WorkstationAssignment.faculty_id'
#     )

#     assigned_equipments = db.relationship(
#         'Equipment',
#         backref='assigned_faculty',
#         cascade='all, delete-orphan',
#         lazy=True,
#         foreign_keys='Equipment.assigned_to_faculty_id'
#     )

#     def compute_years_exp(self):
#         if not self.doj:
#             return None
#         today = date.today()
#         years = today.year - self.doj.year - ((today.month, today.day) < (self.doj.month, self.doj.day))
#         return years

#     def __repr__(self) -> str:
#         return f"<Faculty {self.faculty_id} {self.name} ({self.designation})>"


# # -------------------------
# # Staff (NEW)
# # -------------------------
# class Staff(db.Model):
#     __tablename__ = 'staff'
#     id = db.Column(db.Integer, primary_key=True)
#     staff_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., ST1234
#     name = db.Column(db.String(120), nullable=False)
#     doj = db.Column(db.Date, nullable=False)
#     email = db.Column(db.String(150), unique=True, nullable=False, index=True)
#     mobile = db.Column(db.String(20), nullable=True)
#     room = db.Column(db.String(50), nullable=True)
#     years_exp = db.Column(db.Integer, nullable=True)
#     designation = db.Column(db.String(50), nullable=False)  # e.g., Lab Engineer, Staff
#     profile_photo = db.Column(db.String(200), nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     # Optional user link
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
#     user = db.relationship('User', back_populates='staff')

#     # Lab incharge: many-to-many to RoomLab
#     lab_incharge = db.relationship(
#         'RoomLab',
#         secondary=staff_lab_incharge,
#         back_populates='lab_incharges',
#         lazy=True
#     )

#     # Relationships for assets/assignments
#     workstation_assignments = db.relationship(
#         'WorkstationAssignment',
#         backref='staff_owner',
#         cascade='all, delete-orphan',
#         lazy=True,
#         foreign_keys='WorkstationAssignment.staff_id'
#     )

#     assigned_equipments = db.relationship(
#         'Equipment',
#         backref='assigned_staff',
#         cascade='all, delete-orphan',
#         lazy=True,
#         foreign_keys='Equipment.assigned_to_staff_id'
#     )

#     def compute_years_exp(self):
#         if not self.doj:
#             return None
#         today = date.today()
#         years = today.year - self.doj.year - ((today.month, today.day) < (self.doj.month, self.doj.day))
#         return years

#     def __repr__(self) -> str:
#         return f"<Staff {self.staff_id} {self.name} ({self.designation})>"


# # -------------------------
# # Rooms & Seating
# # -------------------------
# class RoomLab(db.Model):
#     __tablename__ = "room_lab"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), unique=True, nullable=False, index=True)
#     capacity = db.Column(db.Integer, nullable=False)
#     staff_incharge = db.Column(db.String(100), nullable=True)

#     cubicles = db.relationship(
#         "Cubicle",
#         backref="room_lab",
#         cascade="all, delete-orphan",
#         lazy=True,
#     )

#     # backref for staff lab incharge many-to-many
#     lab_incharges = db.relationship(
#         'Staff',
#         secondary=staff_lab_incharge,
#         back_populates='lab_incharge',
#         lazy=True
#     )

#     def __repr__(self) -> str:
#         return f"<RoomLab {self.name} cap={self.capacity}>"


# class Cubicle(db.Model):
#     __tablename__ = "cubicle"
#     id = db.Column(db.Integer, primary_key=True)
#     number = db.Column(db.String(10), nullable=False)
#     room_lab_id = db.Column(db.Integer, db.ForeignKey("room_lab.id"), nullable=False)
#     # Occupant (optional)
#     student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=True, index=True)

#     def __repr__(self) -> str:
#         return f"<Cubicle {self.number} room={self.room_lab_id} student={self.student_roll}>"


# # -------------------------
# # Students
# # -------------------------
# class Student(db.Model):
#     __tablename__ = "student"
#     roll = db.Column(db.String(20), primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     course = db.Column(db.String(20))
#     year = db.Column(db.String(10))
#     joining_year = db.Column(db.String(10))
#     faculty = db.Column(db.String(100))
#     email = db.Column(db.String(100), unique=True)
#     phone = db.Column(db.String(20))

#     profile_photo = db.Column(db.String(200), nullable=True)

#     user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
#     user = db.relationship('User', back_populates='student')

#     cubicle = db.relationship('Cubicle', backref='student', uselist=False)
#     assigned_equipment = db.relationship('Equipment', backref='student', lazy=True, foreign_keys='Equipment.assigned_to_roll')
#     workstation_assignments = db.relationship(
#         'WorkstationAssignment',
#         backref='student_owner',
#         cascade='all, delete-orphan',
#         lazy=True,
#         foreign_keys='WorkstationAssignment.student_roll'
#     )

#     @property
#     def active_assignment(self):
#         """Return the current active workstation assignment (if any)."""
#         return next((a for a in self.workstation_assignments if a.is_active), None)

#     def __repr__(self) -> str:
#         return f"<Student {self.roll} {self.name}>"


# # -------------------------
# # IT Equipment
# # -------------------------
# class Equipment(db.Model):
#     __tablename__ = "equipment"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     category = db.Column(db.String(50), nullable=False)
#     manufacturer = db.Column(db.String(100), nullable=True)
#     model = db.Column(db.String(100), nullable=True)
#     serial_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
#     invoice_number = db.Column(db.String(100), nullable=True)
#     cost_per_unit = db.Column(db.Float, nullable=True)
#     location = db.Column(db.String(100), nullable=True)

#     # 🧾 Procurement Info
#     po_date = db.Column(db.String(20), nullable=True)
#     po_number = db.Column(db.String(100), nullable=True)
#     source_of_fund = db.Column(db.String(100), nullable=True)

#     # 🛡️ Warranty Info
#     warranty_start = db.Column(db.String(20), nullable=True)
#     warranty_expiry = db.Column(db.String(20), nullable=True)

#     # 🏢 Vendor Contact Info
#     vendor_company = db.Column(db.String(150), nullable=True)
#     vendor_contact_person = db.Column(db.String(100), nullable=True)
#     vendor_mobile = db.Column(db.String(20), nullable=True)

#     status = db.Column(db.String(20), default="Available")
#     intender_name = db.Column(db.String(100), nullable=True)
#     remarks = db.Column(db.String(200), nullable=True)
#     quantity = db.Column(db.Integer, nullable=True)
#     department_code = db.Column(db.String(100), unique=True, nullable=True)
#     mac_address = db.Column(db.String(50), nullable=True)

#     # 🔗 Equipment–Student Relationship
#     assigned_to_roll = db.Column(
#         db.String(20),
#         db.ForeignKey('student.roll', name='fk_equipment_assigned_to_roll'),
#         nullable=True,
#         index=True,
#     )

#     # Assigned to faculty (nullable)
#     assigned_to_faculty_id = db.Column(
#         db.Integer,
#         db.ForeignKey('faculty.id', name='fk_equipment_assigned_to_faculty_id'),
#         nullable=True,
#         index=True,
#     )

#     # Assigned to staff (nullable)
#     assigned_to_staff_id = db.Column(
#         db.Integer,
#         db.ForeignKey('staff.id', name='fk_equipment_assigned_to_staff_id'),
#         nullable=True,
#         index=True,
#     )

#     assigned_by = db.Column(db.String(100), nullable=True)
#     assigned_date = db.Column(db.DateTime, nullable=True)

#     def __repr__(self) -> str:
#         return (
#             f"<Equipment {self.name} SN={self.serial_number} "
#             f"PO={self.po_number} Warranty={self.warranty_expiry}>"
#         )


# class EquipmentHistory(db.Model):
#     __tablename__ = "equipment_history"
#     id = db.Column(db.Integer, primary_key=True)
#     equipment_id = db.Column(db.Integer, nullable=False, index=True)
#     assigned_to_roll = db.Column(
#         db.String(20),
#         db.ForeignKey('student.roll', name='fk_equipment_history_assigned_to_roll'),
#         nullable=True,
#         index=True,
#     )
#     assigned_to_faculty_id = db.Column(db.Integer, nullable=True, index=True)
#     assigned_to_staff_id = db.Column(db.Integer, nullable=True, index=True)
#     assigned_by = db.Column(db.String(100), nullable=True)
#     assigned_date = db.Column(db.DateTime, nullable=True)
#     unassigned_date = db.Column(db.DateTime, nullable=True)
#     status_snapshot = db.Column(db.String(50), nullable=True)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)

#     def __repr__(self) -> str:
#         return f"<EquipmentHistory eq={self.equipment_id} to={self.assigned_to_roll}>"


# # -------------------------
# # Provisioning Requests (PXE, etc.)
# # -------------------------
# class ProvisioningRequest(db.Model):
#     __tablename__ = "provisioning_request"
#     id = db.Column(db.Integer, primary_key=True)
#     mac_address = db.Column(db.String(32), nullable=False, index=True)
#     ip_address = db.Column(db.String(32), nullable=False)
#     os_image = db.Column(db.String(64), nullable=False)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)

#     def __repr__(self) -> str:
#         return f"<ProvisioningRequest {self.mac_address} {self.os_image}>"


# # -------------------------
# # Workstation Inventory
# # -------------------------
# class WorkstationAsset(db.Model):
#     """
#     Physical machine in inventory (reusable).
#     """
#     __tablename__ = "workstation_asset"
#     id = db.Column(db.Integer, primary_key=True)

#     # Identity & specs
#     manufacturer = db.Column(db.String(100))
#     otherManufacturer = db.Column(db.String(100))
#     model = db.Column(db.String(100))
#     serial = db.Column(db.String(100), unique=True, index=True)
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

#     # Peripherals
#     keyboard_provided = db.Column(db.String(10))
#     keyboard_details = db.Column(db.String(100))
#     mouse_provided = db.Column(db.String(10))
#     mouse_details = db.Column(db.String(100))
#     monitor_provided = db.Column(db.String(20))
#     monitor_details = db.Column(db.String(100))
#     monitor_size = db.Column(db.String(10))
#     monitor_serial = db.Column(db.String(100))
#     mac_address = db.Column(db.String(50), nullable=True)

#     # 🧾 Procurement Info
#     po_date = db.Column(db.String(20), nullable=True)
#     po_number = db.Column(db.String(100), nullable=True)
#     source_of_fund = db.Column(db.String(100), nullable=True)

#     # 🛡️ Warranty Info
#     warranty_start = db.Column(db.String(20), nullable=True)
#     warranty_expiry = db.Column(db.String(20), nullable=True)

#     # 🏢 Vendor Contact Info
#     vendor_company = db.Column(db.String(150), nullable=True)
#     vendor_contact_person = db.Column(db.String(100), nullable=True)
#     vendor_mobile = db.Column(db.String(20), nullable=True)

#     # Lifecycle and ownership
#     status = db.Column(db.String(20), default="in_stock", index=True)
#     location = db.Column(db.String(100))
#     indenter = db.Column(db.String(100))
#     department_code = db.Column(db.String(200), unique=True, index=True)

#     # Relationships
#     assignments = db.relationship(
#         "WorkstationAssignment",
#         backref="asset",
#         cascade="all, delete-orphan",
#         lazy=True,
#     )

#     def __repr__(self) -> str:
#         return (
#             f"<WorkstationAsset id={self.id} serial={self.serial} "
#             f"PO={self.po_number} Warranty={self.warranty_expiry}>"
#         )


# class WorkstationAssignment(db.Model):
#     """
#     One row per assignment (history).
#     When returned, mark is_active = False and set end_date.
#     Assignment may be to a student OR to a faculty OR to staff (one of the three should be non-null).
#     """
#     __tablename__ = "workstation_assignment"
#     id = db.Column(db.Integer, primary_key=True)
#     workstation_id = db.Column(db.Integer, db.ForeignKey("workstation_asset.id"), nullable=False, index=True)

#     # Either student_roll OR faculty_id OR staff_id will be set (mutually exclusive by app logic)
#     student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=True, index=True)
#     faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True, index=True)
#     staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True, index=True)

#     issue_date = db.Column(db.String(20), nullable=False)
#     system_required_till = db.Column(db.String(20), nullable=False)
#     end_date = db.Column(db.String(20), nullable=True)  # when returned

#     remarks = db.Column(db.String(200))

#     # Fast flag
#     is_active = db.Column(db.Boolean, default=True, index=True)

#     def __repr__(self) -> str:
#         owner = 'unassigned'
#         if self.student_roll:
#             owner = f"student={self.student_roll}"
#         elif self.faculty_id:
#             owner = f"faculty={self.faculty_id}"
#         elif self.staff_id:
#             owner = f"staff={self.staff_id}"
#         return f"<WSAssign asset={self.workstation_id} {owner} active={self.is_active}>"


# class SlurmAccount(db.Model):
#     __tablename__ = "slurm_account"
#     id = db.Column(db.Integer, primary_key=True)
#     roll = db.Column(
#         db.String(20),
#         db.ForeignKey("student.roll"),   # ✅ Correct FK
#         nullable=False,
#         unique=True
#     )
#     status = db.Column(db.String(20), nullable=False, default="active")


# # -------------------------
# # Defaults & Seed helper
# # -------------------------
# room_data = [
#     ("CS-107", 43, "G Praveen Kumar"),
#     ("CS-108", 21, "G Praveen Kumar"),
#     ("CS-109", 114, "G Praveen Kumar"),
#     ("CS-207", 30, "M Shiva Reddy"),
#     ("CS-208", 25, "M Shiva Reddy"),
#     ("CS-209", 142, "M Shiva Reddy"),
#     ("CS-317", 25, "Sunitha M"),
#     ("CS-318", 25, "Sunitha M"),
#     ("CS-319", 32, "Sunitha M"),
#     ("CS-320", 27, "Sunitha M"),
#     ("CS-411", 25, "Mr Nikith Reddy"),
#     ("CS-412", 33, "Mr Nikith Reddy"),
# ]


# def populate_room_and_cubicles(force=False):
#     """
#     Populate RoomLab and Cubicle from room_data.
#     - If force=False, will do nothing if rooms already exist.
#     - If force=True, will insert even if rooms exist (be careful!).
#     """
#     if not force:
#         # Skip if any rooms exist
#         if RoomLab.query.count() > 0:
#             return

#     for name, capacity, staff in room_data:
#         room = RoomLab(name=name, capacity=capacity, staff_incharge=staff)
#         db.session.add(room)
#         db.session.flush()
#         for i in range(1, capacity + 1):
#             db.session.add(Cubicle(number=str(i), room_lab_id=room.id))
#     db.session.commit()


# -------------------------
# Notes on migrations
# -------------------------
# - This file adds a Staff table and updates Equipment and WorkstationAssignment
#   to reference staff (in addition to students/faculty). Use Alembic / Flask-Migrate to
#   create proper migration scripts rather than relying on create_all() in production.
# - When assigning equipment or workstations, application logic should ensure only
#   one owner field is set (student_roll OR faculty_id OR staff_id for workstation assignments,
#   and assigned_to_roll OR assigned_to_faculty_id OR assigned_to_staff_id for equipment).
# - After creating models, you may want to backfill years_exp for existing faculty/staff
#   records using compute_years_exp().
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import json

# IMPORTANT: app.py must import this db and call db.init_app(app)
db = SQLAlchemy()


# -------------------------
# Auth / Users
# -------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin, staff, faculty, student
    is_approved = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Links to profile (optional): a user may be linked to either a student, faculty OR staff profile
    student = db.relationship('Student', back_populates='user', uselist=False, cascade='all, delete')
    faculty = db.relationship('Faculty', back_populates='user', uselist=False, cascade='all, delete')
    staff = db.relationship('Staff', back_populates='user', uselist=False, cascade='all, delete')

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


# -------------------------
# Association table: Staff <-> RoomLab (lab incharge, many-to-many)
# -------------------------
staff_lab_incharge = db.Table(
    'staff_lab_incharge',
    db.Column('staff_id', db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'), primary_key=True),
    db.Column('room_lab_id', db.Integer, db.ForeignKey('room_lab.id', ondelete='CASCADE'), primary_key=True)
)


# -------------------------
# Faculty
# -------------------------
class Faculty(db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # human-friendly ID
    name = db.Column(db.String(120), nullable=False)
    doj = db.Column(db.Date, nullable=False)                        # Date of joining
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    years_exp = db.Column(db.Integer, nullable=True)                # can be computed from doj
    designation = db.Column(db.String(50), nullable=False)         # Professor, Assistant Professor, ...
    profile_photo = db.Column(db.String(200), nullable=True)       # filename/path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional link to User (if you want login for faculty accounts)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    user = db.relationship('User', back_populates='faculty')

    # Relationships to assets/assignments
    workstation_assignments = db.relationship(
        'WorkstationAssignment',
        backref='faculty_owner',
        cascade='all, delete-orphan',
        lazy=True,
        foreign_keys='WorkstationAssignment.faculty_id'
    )

    assigned_equipments = db.relationship(
        'Equipment',
        backref='assigned_faculty',
        cascade='all, delete-orphan',
        lazy=True,
        foreign_keys='Equipment.assigned_to_faculty_id'
    )

    def compute_years_exp(self):
        if not self.doj:
            return None
        today = date.today()
        years = today.year - self.doj.year - ((today.month, today.day) < (self.doj.month, self.doj.day))
        return years

    def __repr__(self) -> str:
        return f"<Faculty {self.faculty_id} {self.name} ({self.designation})>"


# -------------------------
# Staff (NEW)
# -------------------------
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., ST1234
    name = db.Column(db.String(120), nullable=False)
    doj = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    years_exp = db.Column(db.Integer, nullable=True)
    designation = db.Column(db.String(50), nullable=False)  # e.g., Lab Engineer, Staff
    profile_photo = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional user link
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    user = db.relationship('User', back_populates='staff')

    # Lab incharge: many-to-many to RoomLab
    lab_incharge = db.relationship(
        'RoomLab',
        secondary=staff_lab_incharge,
        back_populates='lab_incharges',
        lazy=True
    )

    # Relationships for assets/assignments
    workstation_assignments = db.relationship(
        'WorkstationAssignment',
        backref='staff_owner',
        cascade='all, delete-orphan',
        lazy=True,
        foreign_keys='WorkstationAssignment.staff_id'
    )

    assigned_equipments = db.relationship(
        'Equipment',
        backref='assigned_staff',
        cascade='all, delete-orphan',
        lazy=True,
        foreign_keys='Equipment.assigned_to_staff_id'
    )

    def compute_years_exp(self):
        if not self.doj:
            return None
        today = date.today()
        years = today.year - self.doj.year - ((today.month, today.day) < (self.doj.month, self.doj.day))
        return years

    def __repr__(self) -> str:
        return f"<Staff {self.staff_id} {self.name} ({self.designation})>"


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

    # backref for staff lab incharge many-to-many
    lab_incharges = db.relationship(
        'Staff',
        secondary=staff_lab_incharge,
        back_populates='lab_incharge',
        lazy=True
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
    roll = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(20))
    year = db.Column(db.String(10))
    joining_year = db.Column(db.String(10))
    faculty = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))

    profile_photo = db.Column(db.String(200), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='student')

    cubicle = db.relationship('Cubicle', backref='student', uselist=False)
    assigned_equipment = db.relationship('Equipment', backref='student', lazy=True, foreign_keys='Equipment.assigned_to_roll')
    workstation_assignments = db.relationship(
        'WorkstationAssignment',
        backref='student_owner',
        cascade='all, delete-orphan',
        lazy=True,
        foreign_keys='WorkstationAssignment.student_roll'
    )

    @property
    def active_assignment(self):
        """Return the current active workstation assignment (if any)."""
        return next((a for a in self.workstation_assignments if a.is_active), None)

    def __repr__(self) -> str:
        return f"<Student {self.roll} {self.name}>"


# -------------------------
# IT Equipment
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

    # 🧾 Procurement Info
    po_date = db.Column(db.String(20), nullable=True)
    po_number = db.Column(db.String(100), nullable=True)
    source_of_fund = db.Column(db.String(100), nullable=True)

    # 🛡️ Warranty Info
    warranty_start = db.Column(db.String(20), nullable=True)
    warranty_expiry = db.Column(db.String(20), nullable=True)

    # 🏢 Vendor Contact Info
    vendor_company = db.Column(db.String(150), nullable=True)
    vendor_contact_person = db.Column(db.String(100), nullable=True)
    vendor_mobile = db.Column(db.String(20), nullable=True)

    status = db.Column(db.String(20), default="Available")
    intender_name = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.String(200), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    department_code = db.Column(db.String(100), unique=True, nullable=True)
    mac_address = db.Column(db.String(50), nullable=True)

    # 🔗 Equipment–Student Relationship
    assigned_to_roll = db.Column(
        db.String(20),
        db.ForeignKey('student.roll', name='fk_equipment_assigned_to_roll'),
        nullable=True,
        index=True,
    )

    # Assigned to faculty (nullable)
    assigned_to_faculty_id = db.Column(
        db.Integer,
        db.ForeignKey('faculty.id', name='fk_equipment_assigned_to_faculty_id'),
        nullable=True,
        index=True,
    )

    # Assigned to staff (nullable)
    assigned_to_staff_id = db.Column(
        db.Integer,
        db.ForeignKey('staff.id', name='fk_equipment_assigned_to_staff_id'),
        nullable=True,
        index=True,
    )

    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    expected_return = db.Column(db.DateTime, nullable=True)


    def __repr__(self) -> str:
        return (
            f"<Equipment {self.name} SN={self.serial_number} "
            f"PO={self.po_number} Warranty={self.warranty_expiry}>"
        )


class EquipmentHistory(db.Model):
    __tablename__ = "equipment_history"
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, nullable=False, index=True)
    assigned_to_roll = db.Column(
        db.String(20),
        db.ForeignKey('student.roll', name='fk_equipment_history_assigned_to_roll'),
        nullable=True,
        index=True,
    )
    assigned_to_faculty_id = db.Column(db.Integer, nullable=True, index=True)
    assigned_to_staff_id = db.Column(db.Integer, nullable=True, index=True)
    assigned_by = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    expected_return = db.Column(db.DateTime, nullable=True) 
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


# -------------------------
# Workstation Inventory
# -------------------------
class WorkstationAsset(db.Model):
    __tablename__ = "workstation_asset"
    id = db.Column(db.Integer, primary_key=True)

    # Identity & specs
    manufacturer = db.Column(db.String(100))
    otherManufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))           # Workstation, Desktop, Laptop, Server, Mac
    serial = db.Column(db.String(100), unique=True, index=True)
    os = db.Column(db.String(50))
    otherOs = db.Column(db.String(50))

    # Legacy single-CPU/generic fields (kept for compatibility)
    processor = db.Column(db.String(100))
    cores = db.Column(db.Integer)              # recommended integer
    ram = db.Column(db.String(20))
    otherRam = db.Column(db.String(20))
    ram_size_gb = db.Column(db.Integer, nullable=True)
    # Storage
    storage_type1 = db.Column(db.String(50))
    storage_capacity1 = db.Column(db.Integer)  # GB
    storage_type2 = db.Column(db.String(50))
    storage_capacity2 = db.Column(db.Integer)  # GB

    # Legacy single-GPU fields (kept)
    gpu = db.Column(db.String(100))
    vram = db.Column(db.Integer)

    # Structured JSON fields for multiple processors / gpus
    # Use db.JSON where supported; fallback to Text storage of JSON string
    try:
        processors = db.Column(db.JSON, nullable=True)  # list of {"name":..., "cores":...}
        gpus = db.Column(db.JSON, nullable=True)        # list of {"name":..., "vram":...}
    except Exception:
        processors = db.Column(db.Text, nullable=True)
        gpus = db.Column(db.Text, nullable=True)

    # Peripherals
    keyboard_provided = db.Column(db.String(10))
    keyboard_details = db.Column(db.String(100))
    mouse_provided = db.Column(db.String(10))
    mouse_details = db.Column(db.String(100))
    monitor_provided = db.Column(db.String(20))
    monitor_details = db.Column(db.String(100))
    monitor_size = db.Column(db.String(10))
    monitor_serial = db.Column(db.String(100))

    # Optional MAC (not required)
    mac_address = db.Column(db.String(50), nullable=True)

    # Procurement Info
    po_date = db.Column(db.Date, nullable=True)
    po_number = db.Column(db.String(100), nullable=True)
    source_of_fund = db.Column(db.String(100), nullable=True)

    # Uploaded PO/Invoice filename (optional)
    po_invoice_filename = db.Column(db.String(250), nullable=True)

    # Warranty Info
    warranty_start = db.Column(db.Date, nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)

    # Vendor Contact Info
    vendor_company = db.Column(db.String(150), nullable=True)
    vendor_contact_person = db.Column(db.String(100), nullable=True)
    vendor_mobile = db.Column(db.String(20), nullable=True)

    # Lifecycle and ownership
    status = db.Column(db.String(20), default="Available", index=True)  # Available / Issued / Scrapped / Retired
    location = db.Column(db.String(100))
    indenter = db.Column(db.String(100))
    department_code = db.Column(db.String(200), unique=True, index=True)

    # Relationship to assignments (history). Many assignments allowed (works for servers and other assets).
    assignments = db.relationship(
        "WorkstationAssignment",
        backref="asset",
        cascade="all, delete-orphan",
        lazy=True,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkstationAsset id={self.id} serial={self.serial} model={self.model} status={self.status}>"

    # helpers to read/write JSON fallback if DB uses TEXT
    def get_processors(self):
        if not self.processors:
            return []
        if isinstance(self.processors, str):
            try:
                return json.loads(self.processors)
            except Exception:
                return []
        return self.processors

    def set_processors(self, processors_list):
        if processors_list is None:
            self.processors = None
        else:
            try:
                self.processors = processors_list
            except Exception:
                self.processors = json.dumps(processors_list)

    def get_gpus(self):
        if not self.gpus:
            return []
        if isinstance(self.gpus, str):
            try:
                return json.loads(self.gpus)
            except Exception:
                return []
        return self.gpus

    def set_gpus(self, gpus_list):
        if gpus_list is None:
            self.gpus = None
        else:
            try:
                self.gpus = gpus_list
            except Exception:
                self.gpus = json.dumps(gpus_list)


class WorkstationAssignment(db.Model):
    """
    One assignment row per assignee (student/faculty/staff). Allows multiple active assignments for servers.
    Application logic should allow multiple active rows for assets of model == 'Server'.
    For non-server assets, app should ensure only one is_active assignment exists.
    """
    __tablename__ = "workstation_assignment"
    id = db.Column(db.Integer, primary_key=True)
    workstation_id = db.Column(db.Integer, db.ForeignKey("workstation_asset.id", ondelete='CASCADE'), nullable=False, index=True)

    # Polymorphic assignee fields (exactly one should be set at insert)
    student_roll = db.Column(db.String(20), db.ForeignKey("student.roll"), nullable=True, index=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True, index=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True, index=True)

    # Use Date for issue and end dates
    issue_date = db.Column(db.Date, nullable=False)
    system_required_till = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    assigned_by = db.Column(db.String(120), nullable=True)
    remarks = db.Column(db.String(200), nullable=True)

    # Active flag: servers may have many active assignments; non-servers typically only one active
    is_active = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        owner = 'unassigned'
        if self.student_roll:
            owner = f"student={self.student_roll}"
        elif self.faculty_id:
            owner = f"faculty={self.faculty_id}"
        elif self.staff_id:
            owner = f"staff={self.staff_id}"
        return f"<WSAssign asset={self.workstation_id} {owner} active={self.is_active}>"

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


# -------------------------
# Notes on migrations
# -------------------------
# - This file adds a Staff table and updates Equipment and WorkstationAssignment
#   to reference staff (in addition to students/faculty). Use Alembic / Flask-Migrate to
#   create proper migration scripts rather than relying on create_all() in production.
# - When assigning equipment or workstations, application logic should ensure only
#   one owner field is set (student_roll OR faculty_id OR staff_id for workstation assignments,
#   and assigned_to_roll OR assigned_to_faculty_id OR assigned_to_staff_id for equipment).
# - After creating models, you may want to backfill years_exp for existing faculty/staff
#   records using compute_years_exp().
