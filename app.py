from werkzeug.utils import secure_filename
import os
import secrets
from datetime import datetime, timedelta, date

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv
import requests
from flask_mail import Mail, Message
from sqlalchemy.exc import IntegrityError

# Models
from models import (
    db,
    User,
    Equipment,
    ProvisioningRequest,
    # If you need these elsewhere, import now or inside the route files:
    RoomLab, Cubicle, Student, EquipmentHistory, WorkstationAsset, WorkstationAssignment,
    Faculty, Staff,
    AssetStatusLog
)

# ------------------- Load env -------------------
load_dotenv()

# ------------------- App & DB -------------------
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Normalize database URL (Heroku-style)
db_url = os.getenv("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'database.db')}"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')


# Upload config (set these after app is created)
app.config.setdefault('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
app.config.setdefault('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'})

# create uploads dir right away
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)
migrate = Migrate(app, db)

# ------------------- Login -------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    # SQLAlchemy 2.0 preferred way
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

if os.getenv("AUTO_CREATE_DB") == "1":
    with app.app_context():
        db.create_all()


GOOGLE_SHEET_WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
# GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwQiFsBus3K7wJkSqLtHeeeMvZFr2TObboA0v85D3BfhP4xUKYY8Qi7CFpGv04tYz_n/exec"

def send_to_google_sheet(data):
    try:
        response = requests.post(
            GOOGLE_SHEET_WEBHOOK_URL,
            json=data,
            timeout=5
        )
        print("✅ Google Sheet updated:", response.text)
    except Exception as e:
        print("❌ Error sending to Google Sheet:", e)

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def roles_required(*roles):
    """
    Restrict access to users with given roles.
    Example: @roles_required("admin", "staff")
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                flash("🚫 You are not authorized to access this page.", "danger")
                return redirect(url_for("login_home"))
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator

# =========================================================
# 📧 MAIL CONFIGURATION (Flask-Mail)
# =========================================================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  # from .env
app.config["MAIL_PASSWORD"] = os.getenv("")  # from .env (Gmail app password)
app.config["MAIL_DEFAULT_SENDER"] = ("CSE Lab Admin", os.getenv("MAIL_USERNAME"))
app.config["EMAIL_SENDING_ENABLED"] = False

mail = Mail(app)

# ---- Helper for sending email ----
import threading
from flask_mail import Message

def send_async_email(app, msg):
    """Send email in background thread"""
    with app.app_context():
        try:
            mail.send(msg)
            print(f"✅ Email sent to {msg.recipients} (CC: {msg.cc})")
        except Exception as e:
            print(f"❌ Error sending email: {e}")

def send_notification_email(to_email, subject, body, cc=None):
    """Send notification email (supports HTML + CC)"""
    if not app.config.get("EMAIL_SENDING_ENABLED", True):
        print(f"⚠️ Email sending disabled. Would have sent to: {to_email}")
        print("Subject:", subject)
        print("Body:", body)
        return
    if not to_email:
        print("⚠️ Skipping email: no recipient")
        return

    msg = Message(subject=subject, recipients=[to_email], cc=cc or [])

    # ✅ Use HTML if it looks like HTML, else plain text
    if "<html>" in body.lower():
        msg.html = body
    else:
        msg.body = body

    thr = threading.Thread(target=send_async_email, args=[app, msg])
    thr.start()


# =========================================================
# ✅ TEST ROUTE FOR EMAIL
# =========================================================
@app.route("/test_email")
def test_email():
    try:
        send_notification_email(
            "gpraveenkumargaddam369@gmail.com",
            "✅ Test Email from Lab Management System",
            "Hello!\n\nThis is a test email confirming Flask-Mail setup is working fine.\n\n– CSE Lab Admin"
        )
        return "✅ Test email sent successfully!"
    except Exception as e:
        return f"❌ Email test failed: {e}"

# List of faculty/staff office rooms
OFFICE_ROOMS = [
    "CS-102", "CS-103",
    "CS-203", "CS-205",
    "CS-302", "CS-303", "CS-304", "CS-305", "CS-306", "CS-307", "CS-308", "CS-309",
    "CS-310", "CS-311", "CS-312", "CS-313", "CS-314", "CS-315", "CS-316",
    "CS-402", "CS-403", "CS-404", "CS-405", "CS-406", "CS-407", "CS-408",
    "CS-502", "CS-503", "CS-504", "CS-505", "CS-506", "CS-507", "CS-508", "CS-509",
    "CS-510", "CS-511", "CS-512", "CS-513", "CS-514", "CS-515", "CS-516", "CS-517",
    "CS-602", "CS-603", "CS-604", "CS-606", "CS-607", "CS-608", "CS-610",
]

def build_office_status():
    """
    For each room code, return who is sitting there.
    """
    office_list = []
    for code in OFFICE_ROOMS:
        fac_list = Faculty.query.filter_by(room=code).all()
        staff_list = Staff.query.filter_by(room=code).all()
        office_list.append({
            "room": code,
            "occupied": bool(fac_list or staff_list),
            "faculty": fac_list,
            "staff": staff_list,
            "total": len(fac_list) + len(staff_list),
        })
    return office_list



def compute_years_from_date(d):
    if not d:
        return None
    today = date.today()
    years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    return max(years, 0)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login_home")
@roles_required("admin", "staff", "faculty","student")
@login_required
def login_home():
    return render_template("login_home.html")


# ---------- Faculty registration ----------
@app.route("/faculty/register", methods=["GET", "POST"])
def faculty_register():
    """
    Register a faculty profile and link/create a User with role 'faculty'.
    """
    if request.method == "POST":
        faculty_id = request.form.get("faculty_id", "").strip()
        name = request.form.get("name", "").strip()
        doj_raw = request.form.get("doj", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        room = request.form.get("room", "").strip()
        designation = request.form.get("designation", "").strip()

        # Basic validation
        if not (faculty_id and name and doj_raw and email and designation):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("faculty_register"))

        # Email domain check
        if not email.endswith("@cse.iith.ac.in"):
            flash("Faculty email must be an @cse.iith.ac.in address.", "danger")
            return redirect(url_for("faculty_register"))

        # Unique Faculty ID check
        existing_faculty = Faculty.query.filter_by(faculty_id=faculty_id).first()
        if existing_faculty:
            flash(f"Faculty ID {faculty_id} already exists.", "danger")
            return redirect(url_for("faculty_register"))

        # Faculty email uniqueness (in Faculty table)
        existing_faculty_email = Faculty.query.filter_by(email=email).first()
        if existing_faculty_email:
            flash(f"A faculty profile with email {email} already exists.", "danger")
            return redirect(url_for("faculty_register"))

        # parse date
        try:
            doj = date.fromisoformat(doj_raw)
        except Exception:
            flash("Invalid Date of Joining format (use YYYY-MM-DD).", "danger")
            return redirect(url_for("faculty_register"))

        # handle photo
        photo = request.files.get("profile_photo")
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(f"{faculty_id}_{photo.filename}")   # include faculty id
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], "faculty")
            os.makedirs(save_path, exist_ok=True)
            full_path = os.path.join(save_path, filename)
            photo.save(full_path)
            photo_path = f"uploads/faculty/{filename}"

        f = Faculty(
            faculty_id=faculty_id,
            name=name,
            doj=doj,
            email=email,
            mobile=mobile or None,
            room=room or None,
            designation=designation,
            profile_photo=photo_path,
            created_at=datetime.utcnow(),
        )
        f.years_exp = compute_years_from_date(doj)

        # find or create user
        user = User.query.filter_by(email=email).first()
        if user:
            user.role = "faculty"
            user.is_approved = True
            user.approved_at = datetime.utcnow()
            f.user = user
            db.session.add(f)
            db.session.commit()
            flash("Faculty profile created and linked to existing user.", "success")
            return redirect(url_for("faculty_register"))
        else:
            raw_pass = secrets.token_urlsafe(10)
            pw_hash = generate_password_hash(raw_pass)
            user = User(
                email=email,
                password=pw_hash,
                role="faculty",
                is_approved=True,
                approved_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # populate user.id
            f.user = user
            db.session.add(f)
            db.session.commit()
            flash(f"Faculty registered. Login created for {email}. Initial password: {raw_pass}", "info")
            return redirect(url_for("faculty_register"))

    # GET
    return render_template("faculty_form.html", faculty=None)


# ---------- Faculty edit ----------
@app.route("/faculty/edit/<int:fid>", methods=["GET", "POST"])
@login_required  # optional: require login; remove if you don't use flask-login
def faculty_edit(fid):
    f = Faculty.query.get_or_404(fid)

    # Optional: permission check (only admin or linked user can edit)
    # if not (current_user.role == 'admin' or (f.user_id and f.user_id == current_user.id)):
    #     flash("Access denied", "danger"); return redirect(url_for("profiles.faculty_list"))

    if request.method == "POST":
        # collect fields
        faculty_id = request.form.get("faculty_id", "").strip()
        name = request.form.get("name", "").strip()
        doj_raw = request.form.get("doj", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        room = request.form.get("room", "").strip()
        designation = request.form.get("designation", "").strip()

        # validations
        if not (faculty_id and name and doj_raw and email and designation):
            flash("Please fill required fields.", "danger")
            return redirect(url_for("faculty_edit", fid=fid))

        # parse doj
        try:
            doj = date.fromisoformat(doj_raw)
        except Exception:
            flash("Invalid Date of Joining (use YYYY-MM-DD).", "danger")
            return redirect(url_for("faculty_edit", fid=fid))

        # update fields
        f.faculty_id = faculty_id
        f.name = name
        f.doj = doj
        f.email = email
        f.mobile = mobile or None
        f.room = room or None
        f.designation = designation
        f.years_exp = compute_years_from_date(doj)

        # handle photo using your pattern: secure_filename(f"{id}_{file.filename}")
        file = request.files.get("profile_photo")
        if file and file.filename:
            try:
                filename = secure_filename(f"{f.faculty_id}_{file.filename}")
                save_dir = os.path.join(app.config["UPLOAD_FOLDER"], "faculty")
                os.makedirs(save_dir, exist_ok=True)
                full_path = os.path.join(save_dir, filename)
                file.save(full_path)
                # store relative path for template rendering
                f.profile_photo = f"uploads/faculty/{filename}"
            except Exception as e:
                flash(f"Photo save failed: {e}", "danger")
                return redirect(url_for("faculty_edit", fid=fid))

        # If faculty email changed, update linked User (if exists)
        if f.user:
            # check email uniqueness
            existing = User.query.filter(User.email == email, User.id != f.user.id).first()
            if existing:
                flash("Email already in use by another account.", "danger")
                return redirect(url_for("faculty_edit", fid=fid))
            f.user.email = email
            # ensure role is faculty
            f.user.role = "faculty"

        db.session.commit()
        flash("Faculty details updated.", "success")
        return redirect(url_for("faculty_register", fid=fid))

    # GET
    return render_template("edit_faculty.html", faculty=f)


# ---------- Staff registration ----------



@app.route("/staff/register", methods=["GET", "POST"])
def staff_register():
    """
    Register a staff profile and link/create a User with role 'staff'.
    Supports selecting multiple labs for 'lab incharge'.
    """
    labs = RoomLab.query.order_by(RoomLab.name).all()

    if request.method == "POST":
        staff_id = request.form.get("staff_id", "").strip()
        name = request.form.get("name", "").strip()
        doj_raw = request.form.get("doj", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        room = request.form.get("room", "").strip()
        designation = request.form.get("designation", "").strip()
        lab_ids = request.form.getlist("lab_incharge") or []

        # ---- Required fields ----
        if not (staff_id and name and doj_raw and email and designation):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("staff_register"))

        # ---- Email domain check ----
        if not email.endswith("@cse.iith.ac.in"):
            flash("Staff email must be an @cse.iith.ac.in address.", "danger")
            return redirect(url_for("staff_register"))

        # ---- Unique Staff ID check ----
        existing_staff = Staff.query.filter_by(staff_id=staff_id).first()
        if existing_staff:
            flash(f"Staff ID {staff_id} already exists.", "danger")
            return redirect(url_for("staff_register"))

        # ---- Staff email uniqueness (in Staff table) ----
        existing_staff_email = Staff.query.filter_by(email=email).first()
        if existing_staff_email:
            flash(f"A staff profile with email {email} already exists.", "danger")
            return redirect(url_for("staff_register"))

        # parse date
        try:
            doj = date.fromisoformat(doj_raw)
        except Exception:
            flash("Invalid Date of Joining format (use YYYY-MM-DD).", "danger")
            return redirect(url_for("staff_register"))

        # handle photo
        photo = request.files.get("profile_photo")
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(f"{staff_id}_{photo.filename}")   # include staff id
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], "staff")
            os.makedirs(save_path, exist_ok=True)
            full_path = os.path.join(save_path, filename)
            photo.save(full_path)
            photo_path = f"uploads/staff/{filename}"

        s = Staff(
            staff_id=staff_id,
            name=name,
            doj=doj,
            email=email,
            mobile=mobile or None,
            room=room or None,
            designation=designation,
            profile_photo=photo_path,
            created_at=datetime.utcnow(),
        )
        s.years_exp = compute_years_from_date(doj)

        # attach selected labs
        for rid in lab_ids:
            try:
                r = RoomLab.query.get(int(rid))
                if r:
                    s.lab_incharge.append(r)
            except ValueError:
                continue

        # find or create user
        user = User.query.filter_by(email=email).first()
        if user:
            # user already exists → just set as staff
            user.role = "staff"
            user.is_approved = True
            user.approved_at = datetime.utcnow()
            s.user = user
            db.session.add(s)
            db.session.commit()
            flash("Staff profile created and linked to existing user.", "success")
            return redirect(url_for("staff_register"))
        else:
            # new user
            raw_pass = secrets.token_urlsafe(10)
            pw_hash = generate_password_hash(raw_pass)
            user = User(
                email=email,
                password=pw_hash,
                role="staff",
                is_approved=True,
                approved_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()
            s.user = user
            db.session.add(s)
            db.session.commit()
            flash(f"Staff registered. Login created for {email}. Initial password: {raw_pass}", "info")
            return redirect(url_for("staff_register"))

    return render_template("staff_form.html", staff=None, labs=labs)



# ---------- Staff edit ----------
@app.route("/staff/edit/<int:sid>", methods=["GET", "POST"])
@login_required  # optional
def staff_edit(sid):
    s = Staff.query.get_or_404(sid)
    labs = RoomLab.query.order_by(RoomLab.name).all()

    # Optional permission check
    # if not (current_user.role == 'admin' or (s.user_id and s.user_id == current_user.id)):
    #     flash("Access denied", "danger"); return redirect(url_for("profiles.staff_list"))

    if request.method == "POST":
        staff_id = request.form.get("staff_id", "").strip()
        name = request.form.get("name", "").strip()
        doj_raw = request.form.get("doj", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        room = request.form.get("room", "").strip()
        designation = request.form.get("designation", "").strip()
        lab_ids = request.form.getlist("lab_incharge") or []

        if not (staff_id and name and doj_raw and email and designation):
            flash("Please fill required fields.", "danger")
            return redirect(url_for("staff_edit", sid=sid))

        try:
            doj = date.fromisoformat(doj_raw)
        except Exception:
            flash("Invalid Date of Joining (use YYYY-MM-DD).", "danger")
            return redirect(url_for("staff_edit", sid=sid))

        # update fields
        s.staff_id = staff_id
        s.name = name
        s.doj = doj
        s.email = email
        s.mobile = mobile or None
        s.room = room or None
        s.designation = designation
        s.years_exp = compute_years_from_date(doj)

        # update lab incharges (replace)
        s.lab_incharge = []
        for rid in lab_ids:
            try:
                r = RoomLab.query.get(int(rid))
                if r:
                    s.lab_incharge.append(r)
            except ValueError:
                continue

        # handle photo
        file = request.files.get("profile_photo")
        if file and file.filename:
            try:
                filename = secure_filename(f"{s.staff_id}_{file.filename}")
                save_dir = os.path.join(app.config["UPLOAD_FOLDER"], "staff")
                os.makedirs(save_dir, exist_ok=True)
                full_path = os.path.join(save_dir, filename)
                file.save(full_path)
                # store relative path consistent with staff registration
                s.profile_photo = f"uploads/staff/{filename}"
            except Exception as e:
                flash(f"Photo save failed: {e}", "danger")
                return redirect(url_for("staff_edit", sid=sid))

        # update linked user email if exists
        if s.user:
            existing = User.query.filter(User.email == email, User.id != s.user.id).first()
            if existing:
                flash("Email already in use by another account.", "danger")
                return redirect(url_for("staff_edit", sid=sid))
            s.user.email = email
            s.user.role = "staff"

        db.session.commit()
        flash("Staff details updated.", "success")
        return redirect(url_for("staff_register"))

    # GET
    return render_template("edit_staff.html", staff=s, labs=labs)


from flask import request, render_template
from math import ceil

# common pagination size
PER_PAGE = 25

# ---------- Staff directory ----------
@app.route("/staff_directory")
@login_required
def staff_directory():
    # allow admin+staff access or open to all depending on your policy
    # if current_user.role != 'admin': flash(...) etc.

    # get filters from querystring
    page = int(request.args.get("page", 1))
    selected_name = request.args.get("name", "").strip() or None
    selected_staff_id = request.args.get("staff_id", "").strip() or None
    selected_joining_year = request.args.get("joining_year", "").strip() or None
    selected_room = request.args.get("room_lab_name", "").strip() or None
    selected_designation = request.args.get("designation", "").strip() or None
    selected_lab = request.args.get("lab", "").strip() or None

    # base query
    q = Staff.query.order_by(Staff.name)

    # filters
    if selected_name:
        q = q.filter(Staff.name.ilike(f"%{selected_name}%"))
    if selected_staff_id:
        q = q.filter(Staff.staff_id.ilike(f"%{selected_staff_id}%"))
    if selected_joining_year:
        q = q.filter(extract('year', Faculty.doj) == int(selected_joining_year)) # assumes doj stored YYYY-MM-DD or cast
    if selected_room:
        q = q.filter(Staff.room.ilike(f"%{selected_room}%"))
    if selected_designation:
        q = q.filter(Staff.designation == selected_designation)
    if selected_lab:
        # Staff may have many-to-many lab relationship named lab_incharge
        q = q.join(Staff.lab_incharge).filter(RoomLab.name == selected_lab)

    # pagination (Flask-SQLAlchemy .paginate)
    pagination = q.paginate(page=page, per_page=PER_PAGE, error_out=False)

    # helpers for filter dropdowns
    joining_years = sorted({ (s.doj.year if s.doj else None) for s in Staff.query.all() if s.doj }, reverse=True)
    labs = [r.name for r in RoomLab.query.order_by(RoomLab.name).all()]
    designations = sorted({ s.designation for s in Staff.query.all() if s.designation })

    return render_template(
        "staff_directory.html",
        staff_pagination=pagination,
        selected_name=selected_name,
        selected_staff_id=selected_staff_id,
        selected_joining_year=str(selected_joining_year) if selected_joining_year else None,
        selected_room=selected_room,
        selected_designation=selected_designation,
        selected_lab=selected_lab,
        joining_years=joining_years,
        labs=labs,
        designations=designations
    )


# ---------- Faculty directory ----------
from sqlalchemy import extract
@app.route("/faculty_directory")
@login_required
def faculty_directory():
    page = int(request.args.get("page", 1))
    selected_name = request.args.get("name", "").strip() or None
    selected_faculty_id = request.args.get("faculty_id", "").strip() or None
    selected_joining_year = request.args.get("joining_year", "").strip() or None
    selected_room = request.args.get("room_lab_name", "").strip() or None
    selected_designation = request.args.get("designation", "").strip() or None

    q = Faculty.query.order_by(Faculty.name)

    if selected_name:
        q = q.filter(Faculty.name.ilike(f"%{selected_name}%"))
    if selected_faculty_id:
        q = q.filter(Faculty.faculty_id.ilike(f"%{selected_faculty_id}%"))
    if selected_joining_year:
        q = q.filter(extract('year', Faculty.doj) == int(selected_joining_year))

    if selected_room:
        q = q.filter(Faculty.room.ilike(f"%{selected_room}%"))
    if selected_designation:
        q = q.filter(Faculty.designation == selected_designation)

    pagination = q.paginate(page=page, per_page=PER_PAGE, error_out=False)

    joining_years = sorted({ (f.doj.year if f.doj else None) for f in Faculty.query.all() if f.doj }, reverse=True)
    designations = sorted({ f.designation for f in Faculty.query.all() if f.designation })
    labs = [r.name for r in RoomLab.query.order_by(RoomLab.name).all()]

    return render_template(
        "faculty_directory.html",
        faculty_pagination=pagination,
        selected_name=selected_name,
        selected_faculty_id=selected_faculty_id,
        selected_joining_year=str(selected_joining_year) if selected_joining_year else None,
        selected_room=selected_room,
        selected_designation=selected_designation,
        joining_years=joining_years,
        designations=designations,
        labs=labs
    )
@app.route("/staff/hub/<int:sid>")
@login_required
def staff_hub(sid):
    staff = Staff.query.get_or_404(sid)

    # If staff.room holds the room string, use that for display
    current_room = staff.room if getattr(staff, "room", None) else None

    # Workstation / equipment queries as before
    workstation_active = WorkstationAssignment.query.filter_by(staff_id=sid, is_active=True).all() if hasattr(WorkstationAssignment, "staff_id") else []
    workstation_history = WorkstationAssignment.query.filter_by(staff_id=sid).order_by(WorkstationAssignment.issue_date.desc()).all()
    equipment_active = Equipment.query.filter_by(assigned_to_staff_id=sid, status="Assigned").all()
    equipment_history = EquipmentHistory.query.filter_by(assigned_to_staff_id=sid).order_by(EquipmentHistory.timestamp.desc()).all()
    labs = RoomLab.query.order_by(RoomLab.name).all()

    return render_template(
        "staff_allotment.html",
        staff=staff,
        current_room=current_room,
        workstation_active=workstation_active,
        workstation_history=workstation_history,
        equipment_active=equipment_active,
        equipment_history=equipment_history,
        labs=labs
    )
@app.route("/faculty/hub/<int:fid>")
@login_required
def faculty_hub(fid):
    faculty = Faculty.query.get_or_404(fid)

    # faculty.room is a string (e.g., "CS-107") — use that
    current_room = faculty.room if getattr(faculty, "room", None) else None

    workstation_active = WorkstationAssignment.query.filter_by(faculty_id=fid, is_active=True).all() if hasattr(WorkstationAssignment, "faculty_id") else []
    workstation_history = WorkstationAssignment.query.filter_by(faculty_id=fid).order_by(WorkstationAssignment.issue_date.desc()).all()
    equipment_active = Equipment.query.filter_by(assigned_to_faculty_id=fid, status="Assigned").all()
    equipment_history = EquipmentHistory.query.filter_by(assigned_to_faculty_id=fid).order_by(EquipmentHistory.timestamp.desc()).all()
    labs = RoomLab.query.order_by(RoomLab.name).all()

    return render_template(
        "faculty_allotment.html",
        faculty=faculty,
        current_room=current_room,
        workstation_active=workstation_active,
        workstation_history=workstation_history,
        equipment_active=equipment_active,
        equipment_history=equipment_history,
        labs=labs
    )

from flask import render_template, request, redirect, url_for

from models import Student, Equipment, EquipmentHistory, RoomLab, Cubicle
from datetime import datetime



@app.route("/index", methods=["GET", "POST"])
def index():
    error = None
    success = None
    room_lab_names = [room.name for room in RoomLab.query.all()]
    all_equipment = Equipment.query.all()

    if request.method == "POST":
        form = request.form.to_dict()
        roll = form.get("roll")
        requirement_type = form.get("requirement_type")

        # Create or fetch student
        student = Student.query.filter_by(roll=roll).first()
        if not student:
            student = Student(
                name=form.get("name"),
                roll=roll,
                course=form.get("course"),
                year=form.get("year"),
                joining_year=form.get("joining_year"),
                faculty=form.get("faculty"),
                email=form.get("email"),
                phone=form.get("phone")
            )
            db.session.add(student)
            db.session.flush()

        # Option 1: Cubicle only
        if requirement_type == "cubicle_only":
            room = form.get("room_lab_name")
            cubicle = form.get("cubicle_no")
            exists = Workstation.query.filter_by(room_lab_name=room, cubicle_no=cubicle).first()
            if exists:
                error = f"⚠️ Cubicle {cubicle} in {room} is already assigned."
            else:
                ws = Workstation(roll=roll, room_lab_name=room, cubicle_no=cubicle)
                db.session.add(ws)
                success = "Cubicle assigned successfully."

        # Option 2: Workstation allocation or upgrade
        elif requirement_type == "workstation":
            room = form.get("room_lab_name")
            cubicle = form.get("cubicle_no")

            ws = Workstation.query.filter_by(roll=roll).first()
            if ws:
                # Upgrade existing cubicle-only to full workstation
                ws.room_lab_name = room
                ws.cubicle_no = cubicle
            else:
                ws = Workstation(roll=roll, room_lab_name=room, cubicle_no=cubicle)
                db.session.add(ws)

            # Update full workstation fields
            ws.manufacturer = form.get("manufacturer")
            ws.otherManufacturer = form.get("otherManufacturer")
            ws.model = form.get("model")
            ws.serial = form.get("serial")
            ws.os = form.get("os")
            ws.otherOs = form.get("otherOs")
            ws.processor = form.get("processor")
            ws.cores = form.get("cores")
            ws.ram = form.get("ram")
            ws.otherRam = form.get("otherRam")
            ws.storage_type1 = form.get("storage_type1")
            ws.storage_capacity1 = form.get("storage_capacity1")
            ws.storage_type2 = form.get("storage_type2")
            ws.storage_capacity2 = form.get("storage_capacity2")
            ws.gpu = form.get("gpu")
            ws.vram = form.get("vram")
            ws.issue_date = form.get("issue_date")
            ws.system_required_till = form.get("system_required_till")
            ws.po_date = form.get("po_date")
            ws.source_of_fund = form.get("source_of_fund")
            ws.keyboard_provided = form.get("keyboard_provided")
            ws.keyboard_details = form.get("keyboard_details")
            ws.mouse_provided = form.get("mouse_provided")
            ws.mouse_details = form.get("mouse_details")
            ws.monitor_provided = form.get("monitor_provided")
            ws.monitor_details = form.get("monitor_details")
            ws.monitor_size = form.get("monitor_size")
            ws.monitor_serial = form.get("monitor_serial")

            success = "Workstation details saved or updated."

        # Option 3: Assign IT Equipment
        elif requirement_type == "it_equipment":
            selected_items = [key for key in form if key.startswith("equipment_")]
            for item_key in selected_items:
                eq_id = form.get(item_key)
                if eq_id:
                    eq = Equipment.query.get(int(eq_id))
                    if eq and eq.status == "Available":
                        eq.assigned_to_roll = roll
                        eq.assigned_by = "System"
                        eq.assigned_date = datetime.now()
                        eq.status = "Issued"

                        history = EquipmentHistory(
                            equipment_id=eq.id,
                            assigned_to_roll=roll,
                            assigned_by="System",
                            assigned_date=datetime.now(),
                            status_snapshot="Issued"
                        )
                        db.session.add(history)
            success = "Equipment assigned successfully."

        db.session.commit()
        return render_template(
            "index.html",
            room_lab_names=room_lab_names,
            equipment_list=all_equipment,
            error=error,
            success=success
        )

    return render_template(
        "index.html",
        room_lab_names=room_lab_names,
        equipment_list=all_equipment,
        error=error,
        success=success
    )

from collections import defaultdict
from sqlalchemy.orm import joinedload

def safe(v, dash="—"):
    v = (v or "").strip() if isinstance(v, str) else v
    return v if v not in ("", None) else dash
from flask import render_template
from sqlalchemy.orm import joinedload
from collections import defaultdict
from models import db, WorkstationAsset, WorkstationAssignment, Student

from collections import defaultdict
from sqlalchemy.orm import joinedload
@app.route("/records")
def records():
    # fetch assignments with student + workstation via relationships
    assignments = (
        WorkstationAssignment.query
        .filter(WorkstationAssignment.is_active == True)
        .options(
            joinedload(WorkstationAssignment.workstation),
            joinedload(WorkstationAssignment.student)
        )
        .all()
    )

    grouped_records = defaultdict(list)

    for assignment in assignments:
        asset = assignment.workstation
        student = assignment.student

        record = {
            "name": student.name,
            "roll": student.roll,
            "course": student.course,
            "year": student.year,
            "faculty": student.faculty,
            "email": student.email,
            "phone": student.phone,
            "asset_id": asset.id,
            "serial": asset.serial,
            "manufacturer": asset.manufacturer,
            "model": asset.model,
            "indenter": asset.indenter,
            "issue_date": assignment.issue_date,
            "system_required_till": assignment.system_required_till,
            "remarks": assignment.remarks,
        }
        grouped_records[asset.location].append(record)

    # calculate lab stats (total, used, available)
    lab_stats = {}
    labs = db.session.query(WorkstationAsset.location).distinct().all()

    for lab_tuple in labs:
        lab = lab_tuple[0]
        total = WorkstationAsset.query.filter_by(location=lab).count()
        used = len(grouped_records.get(lab, []))
        available = total - used
        lab_stats[lab] = {
            "total": total,
            "used": used,
            "available": available,
            "staff_incharge": None,  # extend later if needed
        }

    return render_template(
        "records.html",
        grouped_records=grouped_records,
        lab_stats=lab_stats
    )

# routes.py (or inside app.py depending on your structure)
from flask import render_template, request
from flask_login import login_required
from models import db, Student, Equipment, WorkstationAssignment

# Optional: If you have a SlurmAccount model
# from models import SlurmAccount  



from models import SlurmAccount, Student   # import models

@app.route("/slurm_facility", methods=["GET", "POST"])
def slurm_facility():
    result = None

    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()

        if not roll_number:
            result = {"roll": None, "found": None, "error": "Roll number is required!"}
        else:
            account = SlurmAccount.query.filter_by(roll=roll_number).first()
            if account:
                result = {"roll": account.roll, "found": True, "status": account.status}
            else:
                result = {"roll": roll_number, "found": False}

    return render_template("slurm_facility.html", result=result)

@app.route("/student_dashboard", methods=["GET", "POST"])
@login_required
def student_dashboard():
    student = None
    message = None
    slurm_exists = False
    slurm_status = None
    student_equipment_history = []

    if request.method == "POST":
        roll = request.form.get("roll", "").strip()

        if not roll:
            message = "⚠️ Please enter a roll number."
        else:
            # Fetch student record
            student = Student.query.filter_by(roll=roll).first()

            if not student:
                message = f"❌ Student with roll {roll} not found."
            else:
                # Load active assignment if exists
                if student.active_assignment:
                    _ = student.active_assignment.asset  

                # Fetch student’s equipment history
                student_equipment_history = (
                    db.session.query(EquipmentHistory, Equipment)
                    .join(Equipment, Equipment.id == EquipmentHistory.equipment_id)
                    .filter(EquipmentHistory.assigned_to_roll == student.roll)
                    .order_by(EquipmentHistory.assigned_date.desc())
                    .all()
                )

                # ✅ Check Slurm account existence
                slurm = SlurmAccount.query.filter(
                    SlurmAccount.roll.ilike(student.roll)
                ).first()

                if slurm:
                    slurm_exists = True
                    slurm_status = slurm.status  # e.g., 'active' or 'inactive'

    return render_template(
        "student_dashboard.html",
        student=student,
        message=message,
        slurm_exists=slurm_exists,
        slurm_status=slurm_status,
        student_equipment_history=student_equipment_history,
    )

@app.route("/student_profile_dashboard/<roll>")
@login_required
def student_profile_dashboard(roll):
    # ✅ Only allow self-access for students
    if current_user.role == "student" and current_user.student.roll != roll:
        flash("Access denied.", "danger")
        return redirect(url_for("login_home"))

    student = Student.query.get_or_404(roll)

    # ✅ Fetch IT Equipment History
    student_equipment_history = (
        db.session.query(EquipmentHistory, Equipment)
        .join(Equipment, Equipment.id == EquipmentHistory.equipment_id)
        .filter(EquipmentHistory.assigned_to_roll == student.roll)
        .order_by(EquipmentHistory.assigned_date.desc())
        .all()
    )

    # ✅ Check Slurm Account Status
    slurm_exists = False
    slurm_status = None

    slurm = SlurmAccount.query.filter(
        SlurmAccount.roll.ilike(student.roll)
    ).first()

    if slurm:
        slurm_exists = True
        slurm_status = slurm.status

    return render_template(
        "student_profile_dashboard.html",
        student=student,
        student_equipment_history=student_equipment_history,
        slurm_exists=slurm_exists,
        slurm_status=slurm_status
    )


from flask import render_template
from collections import defaultdict
# from models import Workstation  # Adjust this import to match your structure

from flask import render_template
from collections import defaultdict
from models import Student

@app.route("/utilization")
@roles_required("admin", "staff", "faculty")
def utilization():
    rooms = RoomLab.query.all()
    merged_data = {}

    total_seats = 0
    total_used = 0

    for room in rooms:
        cubicles = Cubicle.query.filter_by(room_lab_id=room.id).all()
        seats = {}
        used = 0

        for c in cubicles:
            if c.student:  # Occupied
                active_ws = c.student.active_assignment
                workstation = None
                if active_ws and active_ws.asset:
                    workstation = {
                        "asset": active_ws.asset.serial,
                        "model": active_ws.asset.model,
                        "manufacturer": active_ws.asset.manufacturer,
                        "status": active_ws.asset.status,
                        "till": active_ws.system_required_till,
                    }

                seats[int(c.number)] = {
                    "occupied": True,
                    "student": {
                        "name": c.student.name,
                        "roll": c.student.roll,
                        "faculty": c.student.faculty if c.student.faculty else "No Faculty"
                    },
                    "workstation": workstation
                }
                used += 1
            else:  # Free
                seats[int(c.number)] = {"occupied": False}

        merged_data[room.name] = {
            "total": room.capacity,
            "used": used,
            "available": room.capacity - used,
            "used_seats": seats
        }

        total_seats += room.capacity
        total_used += used

    total_available = total_seats - total_used
    occupancy_percent = round((total_used / total_seats * 100), 1) if total_seats else 0

    return render_template(
        "utilization.html",
        lab_stats=merged_data,
        total_seats=total_seats,
        total_used=total_used,
        total_available=total_available,
        occupancy_percent=occupancy_percent
    )



from sqlalchemy.orm import joinedload

# ============= Allotted Machines (active assignments) =============
@app.route("/alloted_machines")
@login_required
def alloted_machines():
    # Active workstation assignments with asset + student
    assigns = (WorkstationAssignment.query
               .options(joinedload(WorkstationAssignment.asset))
               .filter_by(is_active=True)
               .order_by(WorkstationAssignment.id.desc())
               .all())

    # Build records compatible with your template columns:
    # Name, Roll, Lab, Cubicle, Processor, Cores, RAM, Storage, GPU, and actions
    records = []
    for a in assigns:
        asset = a.asset
        roll = a.student_roll
        # find student's cubicle (if any)
        cur_cub = Cubicle.query.filter_by(student_roll=roll).first()
        room_name = cur_cub.room_lab.name if (cur_cub and cur_cub.room_lab) else None
        cub_no = cur_cub.number if cur_cub else None

        records.append({
            "id": a.id,  # assignment id (for actions like return)
            "name": (db.session.get(Student, roll).name if db.session.get(Student, roll) else ""),
            "roll": roll,
            "course": (db.session.get(Student, roll).course if db.session.get(Student, roll) else ""),
            "year": (db.session.get(Student, roll).year if db.session.get(Student, roll) else ""),
            "room_lab_name": room_name or "-",
            "cubicle_no": cub_no or "-",
            "processor": asset.processor if asset else "",
            "cores": asset.cores if asset else "",
            "ram": asset.ram if asset else "",
            "storage_type1": asset.storage_type1 if asset else "",
            "storage_capacity1": asset.storage_capacity1 if asset else "",
            "storage_type2": asset.storage_type2 if asset else "",
            "storage_capacity2": asset.storage_capacity2 if asset else "",
            "gpu": asset.gpu if asset else "",
        })

    return render_template("allotted_machines.html", records=records)





@app.route("/registration_type")
def registration_type():
    return render_template("registration_type.html")




from models import Equipment, EquipmentHistory

from datetime import datetime
from flask import render_template, request, redirect, flash
from werkzeug.security import generate_password_hash
from models import User, db



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form.get("role")

        # Validation: only IITH emails
        if not (email.endswith("@cse.iith.ac.in") or email.endswith("@iith.ac.in") or email.endswith("@gmail.com")):
            flash("Only @cse.iith.ac.in or @iith.ac.in emails are allowed.", "danger")
            return redirect("/register")

        if not role:
            flash("Please select a role.", "danger")
            return redirect("/register")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect("/register")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect("/register")

        # Check for duplicate
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("⚠️ Email already registered. Please login.", "warning")
            return redirect("/login")

        # Role logic
        is_admin = (role == "admin" and email == "admin@cse.iith.ac.in")

        new_user = User(
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_approved=is_admin,
            approved_at=datetime.utcnow() if is_admin else None,
            registered_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        # ✅ Send email notification
        try:
            if is_admin:
                # Auto-approved Admin user
                subject = "CSE Lab Account Created — Admin Access Granted"
                body = f"""
                        Hello {email},

                        Your admin account has been successfully created and approved.

                        You can now log in using your credentials at:
                        👉 https://192.168.50.85/login

                        Regards,
                        CSE Lab Automation System
                        """
            else:
                # Normal user, awaiting admin approval
                subject = "CSE Lab Registration Received — Pending Approval"
                body = f"""
                        Hello {email},

                        Thank you for registering with CSE Lab.

                        Your account has been successfully created and is pending admin approval.
                        Once approved, you will receive another email with login details.

                        Role: {role.capitalize()}

                        Regards,
                        CSE Lab Admin Team
                        """

            # This helper already exists in your app.py
            send_notification_email(email, subject, body)
            print(f"Registration email sent to {email}")
        except Exception as e:
            print(f"Error sending registration email to {email}: {e}")

        flash("✅ Registered as {}!".format(role.capitalize()) +
              (" You're auto-approved as Admin." if is_admin else " Please wait for admin approval."),
              "success")
        return redirect("/login")

    return render_template("register.html")

from flask_login import login_required, current_user
from flask import render_template
from models import User  # Ensure User model is imported

@app.route('/registered_users')
@login_required
def registered_users():
    if current_user.email != "admin@cse.iith.ac.in":
        flash("Access denied.", "danger")
        return redirect("/login_home")

    users = User.query.order_by(User.registered_at.desc()).all()

    # ✅ Map email → matching entries
    student_map = {s.email: s for s in Student.query.all()}
    faculty_map = {f.email: f for f in Faculty.query.all()}
    staff_map   = {st.email: st for st in Staff.query.all()}

    return render_template(
        "registered_users.html",
        all_users=users,
        student_map=student_map,
        faculty_map=faculty_map,
        staff_map=staff_map,
    )



from flask import flash, redirect, url_for
from flask_login import login_user

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_approved:
                flash("⚠️ Awaiting admin approval.", "warning")
                return redirect(url_for("login"))
            if not user.is_active:
                flash("🚫 Your account has been blocked by the admin.", "danger")
                return redirect(url_for("login"))
            login_user(user)
            # flash("✅ Logged in successfully.", "success")
            return redirect(url_for("login_home"))
        else:
            flash("❌ Invalid credentials.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/about')
def about_us():
    return render_template('about_us.html') 




from flask import session

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()  # 🔁 Clears all session data
    return redirect(url_for("login"))


# ================= PASSWORD RESET =================

@app.route("/reset-request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(16)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()

            # ✅ Send reset email
            subject = "🔑 CSE Lab Password Reset Request"
            body = f"""
Hello {user.email},

We received a request to reset your password. Click the link below to reset it (valid for 15 minutes):

👉 http://127.0.0.1:5000/reset-password/{token}

If you didn't request this, please ignore this email.

Regards,
CSE Lab Admin
"""
            send_notification_email(user.email, subject, body)
            flash("Password reset link has been sent to your email.", "success")
        else:
            flash("Email not found", "danger")
        return redirect(url_for("reset_request"))

    return render_template("reset_request.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        return "Invalid or expired token"

    if request.method == "POST":
        new_password = request.form.get("password")
        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        # ✅ Send confirmation email
        subject = "✅ Your CSE Lab Password Has Been Changed"
        body = f"""
Hello {user.email},

Your password has been successfully updated. You can now log in with your new password:

👉 https://192.168.50.85/login

If you did not make this change, contact the admin immediately.

Regards,
CSE Lab Admin
"""
        send_notification_email(user.email, subject, body)

        flash("Password updated! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


# ================= ADMIN APPROVE / REJECT =================

@app.route("/admin/approve", methods=["GET", "POST"])
@login_required
def approve_panel():
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"

    if request.method == "POST":
        user_id = request.form.get("user_id")
        action = request.form.get("action")
        user = User.query.get(int(user_id))

        if user:
            if action == "approve":
                user.is_approved = True
                user.approved_at = datetime.utcnow()
                db.session.commit()

                # ✅ Send approval email
                subject = "✅ Your CSE Lab Account Has Been Approved"
                body = f"""
Hello {user.email},

Your account has been approved by the admin. You can now log in:

👉 https://192.168.50.85/login

Role: {user.role.capitalize()}

Regards,
CSE Lab Admin
"""
                send_notification_email(user.email, subject, body)
                flash(f"{user.email} approved and notified.", "success")

            elif action == "reject":
                # ✅ Send rejection email before deletion
                subject = "❌ Your CSE Lab Account Registration Was Rejected"
                body = f"""
Hello {user.email},

Your registration for CSE Lab has been rejected by the admin.

If you believe this is a mistake, please contact the admin.

Regards,
CSE Lab Admin
"""
                send_notification_email(user.email, subject, body)

                user.is_approved = False
                user.approved_at = datetime.utcnow()
                db.session.delete(user)
                db.session.commit()
                flash(f"{user.email} rejected and notified.", "danger")

        return redirect("/admin/approve")

    pending_users = User.query.filter_by(is_approved=False).all()
    return render_template("approve_users.html", users=pending_users)


@app.route("/admin/approve/<int:user_id>")
@login_required
def approve_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    
    user = User.query.get(user_id)
    if user:
        user.is_approved = True
        user.approved_at = datetime.utcnow()
        db.session.commit()

        # ✅ Send approval email
        subject = "✅ Your CSE Lab Account Has Been Approved"
        body = f"""
Hello {user.email},

Your account has been approved by the admin. You can now log in:

👉 https://192.168.50.85/login

Role: {user.role.capitalize()}

Regards,
CSE Lab Admin
"""
        send_notification_email(user.email, subject, body)

    return redirect(url_for("approve_panel"))


@app.route("/admin/reject/<int:user_id>")
@login_required
def reject_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    
    user = User.query.get(user_id)
    if user:
        # ✅ Send rejection email before deletion
        subject = "❌ Your CSE Lab Account Registration Was Rejected"
        body = f"""
Hello {user.email},

Your registration for CSE Lab has been rejected by the admin.

If you believe this is a mistake, please contact the admin.

Regards,
CSE Lab Admin
"""
        send_notification_email(user.email, subject, body)

        db.session.delete(user)
        db.session.commit()

    return redirect(url_for("approve_panel"))


# ================= ADMIN TOGGLE / DELETE USERS =================

@app.route("/admin/toggle_user/<int:user_id>")
@login_required
def toggle_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    
    user = User.query.get_or_404(user_id)
    if user.email == "admin@cse.iith.ac.in":
        flash("Admin account cannot be blocked.", "danger")
        return redirect(url_for("registered_users"))

    user.is_active = not user.is_active
    db.session.commit()

    # ✅ Send email notification
    if not user.is_active:
        subject = "🚫 Your CSE Lab Account Has Been Blocked"
        body = f"""
Hello {user.email},

Your account has been temporarily blocked by the admin. 
You will not be able to log in until it is unblocked.

If you believe this is a mistake, please contact the admin.

Regards,
CSE Lab Admin
"""
    else:
        subject = "✅ Your CSE Lab Account Has Been Unblocked"
        body = f"""
Hello {user.email},

Your account has been unblocked by the admin. 
You can now log in again:

👉 https://192.168.50.85/login

Regards,
CSE Lab Admin
"""
    send_notification_email(user.email, subject, body)
    flash(f"{'Blocked' if not user.is_active else 'Unblocked'} {user.email} and notified.", "success")
    return redirect(url_for("registered_users"))


@app.route("/admin/delete_user/<int:user_id>")
@login_required
def delete_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"

    user = User.query.get_or_404(user_id)
    if user.email == "admin@cse.iith.ac.in":
        flash("Admin account cannot be deleted.", "danger")
        return redirect(url_for("registered_users"))

    # ✅ Send deletion notification before removing
    subject = "❌ Your CSE Lab Account Has Been Deleted"
    body = f"""
Hello {user.email},

Your account has been deleted by the admin. 
You will no longer be able to log in.

If you believe this is a mistake, please contact the admin.

Regards,
CSE Lab Admin
"""
    send_notification_email(user.email, subject, body)

    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted {user.email} and notified.", "success")
    return redirect(url_for("registered_users"))


# ================= USER SETTINGS (CHANGE PASSWORD) =================

@app.route("/user/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if not check_password_hash(current_user.password, current):
            flash("Current password is incorrect.", "danger")
        elif new != confirm:
            flash("New passwords do not match.", "danger")
        else:
            current_user.password = generate_password_hash(new)
            db.session.commit()

            # ✅ Send confirmation email
            subject = "✅ Your CSE Lab Password Has Been Changed"
            body = f"""
Hello {current_user.email},

Your account password has been successfully updated. 

If you did not perform this change, please contact the admin immediately.

Regards,
CSE Lab Admin
"""
            send_notification_email(current_user.email, subject, body)

            flash("Password updated successfully! A confirmation email has been sent.", "success")
            return redirect(url_for("user_settings"))

    return render_template("user_settings.html")



from flask_login import current_user

# @app.route("/cse_labs")
# @login_required
# def cse_labs():
#     layout_template = "login_home.html" if current_user.is_authenticated else "base.html"
#     return render_template("cse_labs.html", layout=layout_template)
from flask import render_template
from flask_login import login_required, current_user
from models import RoomLab

@app.route("/cse_labs")
@login_required
def cse_labs():
    layout_template = "login_home.html" if current_user.is_authenticated else "base.html"

    # Pull rooms from DB so capacity & faculty match reality
    rooms = RoomLab.query.order_by(RoomLab.name).all()

    # Floor/color logic by room code
    floor_color = {
        '1': ('First Floor', 'blue'),
        '2': ('Second Floor', 'green'),
        '3': ('Third Floor', 'blue'),
        '4': ('Fourth Floor', 'green'),
    }

    # Optional: descriptive tags and blurbs per lab
    desc_map = {
        "CS-107": "M.Tech Teaching Assistants Lab.",
        "CS-108": "Visual Learning and Intelligence Lab (VIGIL).",
        "CS-109": "Lab dedicated for teaching and hands-on practical sessions.",
        "CS-207": "Compilers lab.",
        "CS-208": "Compilers Lab.",
        "CS-209": "Teaching & hands-on sessions.",
        "CS-317": "Practical Networking and Blockchain Lab (PRANET).",
        "CS-318": "NetX Lab.",
        "CS-319": "Networked Wireless Systems Lab (NeWS).",
        "CS-320": "Project and prototyping space.",
        "CS-411": "Natural Language and Information Processing Lab.",
        "CS-412": "Bayesian Reasoning and INtelligence Lab.",
    }
    tag_map = {
        "CS-107": ["AI", "Systems"],
        "CS-108": ["Security", "Networks"],
        "CS-109": ["ML", "Simulation"],
        "CS-207": ["Data", "Algorithms"],
        "CS-208": ["Embedded", "Design"],
        "CS-209": ["Cloud", "Big Data"],
        "CS-317": ["DevOps", "Testing"],
        "CS-318": ["IoT", "Sensors"],
        "CS-319": ["DBMS", "Transactions"],
        "CS-320": ["Prototyping", "Hardware"],
        "CS-411": ["Thesis", "Discussion"],
        "CS-412": ["Graphics", "Vision"],
    }

    labs = []
    for r in rooms:
        code = r.name  # e.g., "CS-107"
        # derive floor/color from the first digit after the hyphen
        digit = code.split("-")[1][0] if "-" in code and code.split("-")[1] else "1"
        floor, color = floor_color.get(digit, ("Unknown Floor", "gray"))

        # friendly name (keep your original style)
        number = int(code.split("-")[1]) if "-" in code and code.split("-")[1].isdigit() else 0
        kind = "Teaching Lab" if number in (107, 109, 209) else "Research Lab"
        name = f"{code} {kind}"

        labs.append({
            "code": code,
            "name": name,
            "desc": desc_map.get(code, "Lab space."),
            "tags": tag_map.get(code, []),
            "count": r.capacity,
            "floor": floor,
            "color": color,
            "faculty": r.staff_incharge or "Not Assigned",
        })

    return render_template("cse_labs.html", layout=layout_template, labs=labs)


@app.route("/contact_us")
def contact_us():
    return render_template("contact_us.html")

from flask_login import login_required, current_user

@app.route("/inventory", methods=["GET"])
@login_required
def inventory():
    return render_template("inventory.html", layout="login_home.html")

from datetime import datetime
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_required

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import date
from models import db, Equipment

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import db, Equipment, Student
from datetime import datetime

@app.route("/equipment_entry", methods=["GET", "POST"])
@login_required
def equipment_entry():
    if request.method == "POST":
        try:
            # 🔍 Debug
            print("🧾 Form Data:", request.form.to_dict())

            name = request.form["name"]
            category = request.form["category"]
            manufacturer = request.form["manufacturer"]
            model = request.form["model"]
            invoice_number = request.form.get("invoice_number")
            cost_per_unit = request.form.get("cost_per_unit", type=float)
            warranty_start = request.form.get("warranty_start")
            warranty_expiry = request.form.get("warranty_expiry")
            location = request.form["location"]
            po_date = request.form.get("po_date")
            po_number = request.form.get("po_number")
            source_of_fund = request.form.get("source_of_fund")
            vendor_company = request.form.get("vendor_company")
            vendor_contact_person = request.form.get("vendor_contact_person")
            vendor_mobile = request.form.get("vendor_mobile")
            intender_full = request.form.get("intender_name") or "Unknown"
            status = request.form.get("status")
            remarks = request.form.get("remarks")
            quantity = request.form.get("quantity", type=int)
            assigned_to_roll = request.form.get("assigned_to_roll")
            assigned_by = request.form.get("assigned_by")
            assigned_date = datetime.now() if assigned_to_roll else None

            # Current category-wise count for unique department code
            current_count = Equipment.query.filter_by(category=category).count()

            for i in range(quantity):
                serial_number = request.form.get(f"serial_number_{i+1}")
                mac_address = request.form.get(f"mac_address_{i+1}", "")

                serial = f"{current_count + i + 1:03}"  # 001, 002, etc.

                # Department code format
                po_date_clean = po_date.replace("-", "")
                intender_clean = intender_full.split()[0]  # First word
                department_code = f"CSE/{po_date_clean}/{category}/{manufacturer}/{intender_clean}/{serial}"

                equipment = Equipment(
                    name=name,
                    category=category,
                    manufacturer=manufacturer,
                    model=model,
                    serial_number=serial_number,
                    mac_address=mac_address,
                    invoice_number=invoice_number,
                    cost_per_unit=cost_per_unit,
                    warranty_start=warranty_start,
                    warranty_expiry=warranty_expiry,
                    location=location,
                    po_date=po_date,
                    po_number=po_number,
                    source_of_fund=source_of_fund,
                    vendor_company=vendor_company,
                    vendor_contact_person=vendor_contact_person,
                    vendor_mobile=vendor_mobile,
                    status=status,
                    intender_name=intender_full,
                    remarks=remarks,
                    quantity=1,  # Each entry is separate
                    department_code=department_code,
                    assigned_to_roll=assigned_to_roll if assigned_to_roll else None,
                    assigned_by=assigned_by,
                    assigned_date=assigned_date
                )

                db.session.add(equipment)

            db.session.commit()
            flash(f"{quantity} equipment entries added successfully.", "success")
            return redirect(url_for("equipment_entry"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error adding equipment: {e}", "danger")
            print("Error:", e)

    students = Student.query.all()
    return render_template("equipment_entry.html", students=students)





from flask import send_file
import pandas as pd
from io import BytesIO
from models import Equipment

from flask import request, render_template
from sqlalchemy import or_



from flask import request, render_template
from sqlalchemy import or_



from collections import defaultdict
from sqlalchemy import or_

from collections import defaultdict
from flask import request, render_template
from sqlalchemy import or_

@app.route("/equipment_list", methods=["GET"])
def equipment_list():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 25  # Adjust as needed

    query = Equipment.query

    # Search across multiple columns
    if search_query:
        query = query.filter(
            or_(
                Equipment.name.ilike(f"%{search_query}%"),
                Equipment.category.ilike(f"%{search_query}%"),
                Equipment.status.ilike(f"%{search_query}%"),
                Equipment.department_code.ilike(f"%{search_query}%"),
                Equipment.intender_name.ilike(f"%{search_query}%"),
                Equipment.model.ilike(f"%{search_query}%"),
                Equipment.location.ilike(f"%{search_query}%"),
                Equipment.manufacturer.ilike(f"%{search_query}%"),
                Equipment.serial_number.ilike(f"%{search_query}%"),
                Equipment.po_date.ilike(f"%{search_query}%"),
                Equipment.purchase_date.ilike(f"%{search_query}%"),
                Equipment.mac_address.ilike(f"%{search_query}%"),
                Equipment.vendor_company.ilike(f"%{search_query}%")
            )
        )

    # Status filter
    if status_filter:
        query = query.filter(Equipment.status == status_filter)

    # Pagination
    pagination = query.order_by(Equipment.category, Equipment.name).paginate(page=page, per_page=per_page)

    # Group by category
    grouped_equipment = defaultdict(list)
    for eq in pagination.items:
        grouped_equipment[eq.category].append(eq)

    return render_template(
        "equipment_list.html",
        grouped_equipment=grouped_equipment,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter
    )


from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Equipment, db
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Equipment # Update this line as per your actual import





@app.route('/assign_equipment/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def assign_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)

    # Block certain statuses
    if equipment.status.lower() in ['scrap', 'repaired']:
        flash(f"Cannot assign equipment with status '{equipment.status}'.", "warning")
        return redirect(url_for('equipment_list'))

    if request.method == 'POST':
        assigned_to_roll = request.form.get('assigned_to_roll')
        now = datetime.utcnow()

        if assigned_to_roll:
            student = Student.query.filter_by(roll=assigned_to_roll).first()
            if student:
                equipment.assigned_to_roll = student.roll
                equipment.assigned_by = current_user.email
                equipment.assigned_date = now
                equipment.status = 'Issued'

                # -------------------------------------------
                # UPDATE EQUIPMENT LOCATION BASED ON CUBICLE
                # -------------------------------------------
                if student.cubicle and student.cubicle.room_lab:
                    old_loc = equipment.location
                    new_loc = student.cubicle.room_lab.name
                    equipment.location = new_loc
                    print(f"Location updated to {new_loc} for student {student.roll}")
                    # Add history for location change
                    history = EquipmentHistory(
                        equipment_id=equipment.id,
                        assigned_to_roll=student.roll,
                        assigned_by=current_user.email,
                        assigned_date=now,
                        unassigned_date=None,
                        status_snapshot=f"Location changed from {old_loc or 'None'} to {new_loc}",
                        timestamp=now
                    )
                    db.session.add(history)
                else:
                    # Normal assignment history
                    history = EquipmentHistory(
                        equipment_id=equipment.id,
                        assigned_to_roll=student.roll,
                        assigned_by=current_user.email,
                        assigned_date=now,
                        unassigned_date=None,
                        status_snapshot='Issued',
                        timestamp=now
                    )
                    db.session.add(history)

                flash(f"Assigned to {student.name} ({student.roll})", "success")

            else:
                flash("Invalid student selected", "danger")

        # -----------------------
        #  UNASSIGN EQUIPMENT
        # -----------------------
        else:
            history = EquipmentHistory(
                equipment_id=equipment.id,
                assigned_to_roll=equipment.assigned_to_roll,
                assigned_by=current_user.email,
                assigned_date=equipment.assigned_date,
                unassigned_date=now,
                status_snapshot="Returned / Available",
                timestamp=now
            )
            db.session.add(history)

            equipment.assigned_to_roll = None
            equipment.assigned_by = None
            equipment.assigned_date = None
            equipment.status = 'Available'
            equipment.location = None

            flash("Equipment unassigned", "info")

        db.session.commit()
        return redirect(url_for('equipment_list'))

    # Dropdown data
    courses = [c[0] for c in db.session.query(Student.course).distinct().all()]
    years = [y[0] for y in db.session.query(Student.year).distinct().all()]

    return render_template(
        "assign_equipment.html",
        equipment=equipment,
        courses=courses,
        years=years
    )



@app.route('/equipment_history/<int:equipment_id>')
@login_required
def equipment_history(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    history = EquipmentHistory.query.filter_by(equipment_id=equipment_id).order_by(EquipmentHistory.timestamp.desc()).all()
    return render_template("equipment_history.html", equipment=equipment, history=history)


from flask import make_response
import pandas as pd
import io

@app.route("/export_equipment/<file_format>")
@login_required
def export_equipment(file_format):
    equipment = Equipment.query.all()
    
    data = [{
        "Department Code": eq.department_code,
        "PO Date": eq.po_date,
        "Intender Name": eq.intender_name,
        "Category": eq.category,
        "Status": eq.status,
        "Quantity": eq.quantity,
        "Remarks": eq.remarks,
        "Created At": eq.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for eq in equipment]

    df = pd.DataFrame(data)

    if file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Equipment")
        output.seek(0)
        return send_file(output, download_name="equipment_list.xlsx", as_attachment=True)

    elif file_format == "pdf":
        html = df.to_html(index=False)
        # Optional: convert to PDF using xhtml2pdf or similar if needed
        response = make_response(html)
        response.headers["Content-Disposition"] = "attachment; filename=equipment_list.html"
        response.headers["Content-Type"] = "text/html"
        return response

    else:
        return "❌ Unsupported file format", 400

# Static metadata for labs
lab_meta = {
    "CS-107": {"faculty": "Dr. A. Sharma", "meeting_rooms": 2, "capacity": 43, "image": "mylab/cs107.jpg"},
    "CS-108": {"faculty": "Dr. B. Rao", "meeting_rooms": 1, "capacity": 21, "image": "mylab/cs108.jpg"},
    "CS-109": {"faculty": "Dr. C. Iyer", "meeting_rooms": 1, "capacity": 114, "image": "mylab/cs109.jpg"},
    "CS-207": {"faculty": "Dr. D. Gupta", "meeting_rooms": 1, "capacity": 30, "image": "mylab/cs207.jpg"},
    "CS-208": {"faculty": "Dr. E. Nair", "meeting_rooms": 1, "capacity": 25, "image": "mylab/cs208.jpg"},
    "CS-209": {"faculty": "Dr. F. Singh", "meeting_rooms": 2, "capacity": 142, "image": "mylab/cs209.jpg"},
    "CS-317": {"faculty": "Dr. G. Patil", "meeting_rooms": 1, "capacity": 25, "image": "mylab/cs317.jpg"},
    "CS-318": {"faculty": "Dr. H. Bose", "meeting_rooms": 1, "capacity": 25, "image": "mylab/cs318.jpg"},
    "CS-319": {"faculty": "Dr. I. Rao", "meeting_rooms": 1, "capacity": 32, "image": "mylab/cs319.jpg"},
    "CS-320": {"faculty": "Dr. J. Varma", "meeting_rooms": 1, "capacity": 27, "image": "mylab/cs320.jpg"},
    "CS-411": {"faculty": "Dr. K. Desai", "meeting_rooms": 1, "capacity": 25, "image": "mylab/cs411.jpg"},
    "CS-412": {"faculty": "Dr. L. Mehta", "meeting_rooms": 1, "capacity": 33, "image": "mylab/cs412.jpg"},
}

from flask import render_template, abort
from flask_login import login_required
from sqlalchemy.orm import joinedload
from models import RoomLab

@app.route('/lab_details/<lab_code>')
@login_required
def lab_details(lab_code):
    lab_name = lab_code.upper()

    # ✅ Get lab (room) info
    room = RoomLab.query.filter_by(name=lab_name).first()
    if not room:
        abort(404, description="Lab not found")

    # ✅ Get cubicles for this lab, eager-load student
    cubicles = (Cubicle.query
                .options(joinedload(Cubicle.student))
                .filter_by(room_lab_id=room.id)
                .all())

    # Map seat numbers to cubicle objects
    assigned_seats = {}
    for c in cubicles:
        if c.number and c.number.isdigit():
            assigned_seats[int(c.number)] = c

    # Build seating grid
    seats = []
    for seat_num in range(1, (room.capacity or 0) + 1):
        c = assigned_seats.get(seat_num)
        if c and c.student:
            st = c.student
            seats.append({
                "number": seat_num,
                "occupied": True,
                "student_name": st.name,
                "roll_number": st.roll,
                "email": st.email,
                "branch": st.course,
                "year": st.year,
                "photo_url": f"/static/photos/{st.roll}.jpg"
            })
        else:
            seats.append({"number": seat_num, "occupied": False})

    # Infra meta (extend as needed)
    infra_meta = {
        "CS-107": {"meeting_rooms": 1, "whiteboards": 1, "printers": 0, "projectors": 0, "lockers": 0},
        "CS-108": {"meeting_rooms": 1, "whiteboards": 2, "printers": 1, "projectors": 0, "lockers": 0},
        "CS-109": {"meeting_rooms": 2, "whiteboards": 1, "printers": 0, "projectors": 0, "lockers": 0},
        "CS-207": {"meeting_rooms": 2, "whiteboards": 1, "printers": 1, "projectors": 0, "lockers": 0},
        "CS-208": {"meeting_rooms": 0, "whiteboards": 0, "printers": 0, "projectors": 0, "lockers": 0},
        "CS-209": {"meeting_rooms": 0, "whiteboards": 0, "printers": 0, "projectors": 0, "lockers": 0},
        "CS-317": {"meeting_rooms": 0, "whiteboards": 2, "printers": 1, "projectors": 0, "lockers": 0},
        "CS-318": {"meeting_rooms": 0, "whiteboards": 1, "printers": 1, "projectors": 0, "lockers": 32},
        "CS-319": {"meeting_rooms": 3, "whiteboards": 0, "printers": 1, "projectors": 0, "lockers": 30},
        "CS-320": {"meeting_rooms": 1, "whiteboards": 3, "printers": 2, "projectors": 1, "lockers": 0},
        "CS-411": {"meeting_rooms": 0, "whiteboards": 0, "printers": 0, "projectors": 0, "lockers": 0},
        "CS-412": {"meeting_rooms": 0, "whiteboards": 2, "printers": 0, "projectors": 0, "lockers": 32},
    }
    meta = infra_meta.get(lab_name, {})
    meeting_rooms = meta.get("meeting_rooms", 0)
    whiteboards = meta.get("whiteboards", 0)
    printers = meta.get("printers", 0)
    projectors = meta.get("projectors", 0)
    lockers = meta.get("lockers", 0)

    # ✅ Stats
    used_valid = sum(1 for s in seats if s["occupied"])
    capacity = room.capacity or 0
    available = capacity - used_valid if capacity else 0

    return render_template(
        "lab_details.html",
        lab_code=lab_name,
        capacity=capacity,
        used_seating=used_valid,
        available_seating=available,
        faculty=room.staff_incharge or "Not Assigned",
        meeting_rooms=meeting_rooms,
        whiteboards=whiteboards,
        printers=printers,
        projectors=projectors,
        lockers=lockers,
        seats=seats
    )

from flask import render_template, make_response
from flask_login import login_required
from weasyprint import HTML
from models import WorkstationAsset, Equipment, SlurmAccount



from datetime import datetime
from flask_login import current_user

@app.route("/assign_equipment_to_student/<string:roll>", methods=["POST"])
@login_required
def assign_equipment_to_student(roll):
    student = Workstation.query.filter_by(roll=roll).first_or_404()
    equipment_id = request.form.get("equipment_id")

    if not equipment_id:
        flash("Please select equipment.", "warning")
        return redirect(url_for('student_details', roll=roll))

    equipment = Equipment.query.get_or_404(equipment_id)

    # ❌ Block reassignment
    if equipment.assigned_to_roll:
        flash("⚠️ Equipment already assigned and cannot be reassigned.", "danger")
        return redirect(url_for('student_details', roll=roll))

    # ✅ Set tracking values properly
    equipment.assigned_to_roll = roll
    equipment.assigned_date = datetime.utcnow()
    equipment.assigned_by = current_user.email

    db.session.commit()

    flash(f"✅ Equipment '{equipment.name}' assigned to {student.name}", "success")
    return redirect(url_for('student_details', roll=roll))







import paramiko

def check_user_on_remote(roll):
    host = "192.168.0.113"         # Your laptop's IP
    username = "datacenterops"        # SSH login user
    password = "csedc" 
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, timeout=5)

        # Use getent to check if user exists
        stdin, stdout, stderr = client.exec_command(f"getent passwd {roll}")
        output = stdout.read().decode().strip()
        client.close()

        return bool(output)
    except Exception as e:
        print("SSH connection error:", e)
        return None

from flask import flash, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

@app.route('/install_os_form', methods=['GET'])
def install_os_form():
    return render_template('install_os_form.html')



@app.route("/provision", methods=["POST"])
def provision():
    mac = request.form.get("mac_address")
    ip = request.form.get("ip_address")
    os_image = request.form.get("os_image")

    new_request = ProvisioningRequest(mac_address=mac, ip_address=ip, os_image=os_image)
    db.session.add(new_request)
    db.session.commit()

    flash("Provisioning request submitted successfully!", "success")
    return render_template("provision_success.html", mac=mac, ip=ip, os_image=os_image)

@app.route("/provision_history")
def provision_history():
    records = ProvisioningRequest.query.order_by(ProvisioningRequest.timestamp.desc()).all()
    return render_template("provision_history.html", records=records)

@app.route("/os_related")
def os_related():
    return render_template("os_related.html")

from flask import render_template, request
# from flask import app, db  # Replace 'yourapp' with your actual app name
# from models import Workstation
from flask import render_template, request
from flask import request, render_template
from datetime import datetime
from models import db, Student, Cubicle, RoomLab

from flask import request, render_template
from datetime import datetime
from models import db, Student, Cubicle, RoomLab

@app.route('/students_directory', methods=['GET'])
def students_directory():
    # Get filter values
    course = request.args.get('course')
    year = request.args.get('year')
    joining_year = request.args.get('joining_year')
    room_lab_name = request.args.get('room_lab_name')
    roll = request.args.get('roll')
    faculty = request.args.get('faculty')
    page = request.args.get('page', 1, type=int)

    # Base query: join Student -> Cubicle -> RoomLab
    query = Student.query.outerjoin(Cubicle).outerjoin(RoomLab)

    # Apply filters
    if course:
        query = query.filter(Student.course == course)
    if year:
        query = query.filter(Student.year == year)
    if joining_year:
        query = query.filter(Student.joining_year == joining_year)
    if room_lab_name:
        query = query.filter(RoomLab.name == room_lab_name)
    if roll:
        query = query.filter(Student.roll.ilike(f"%{roll}%"))
    if faculty:
        query = query.filter(Student.faculty == faculty)

    # Paginate (10 results per page)
    students_pagination = query.paginate(page=page, per_page=10, error_out=False)

    # Dropdown filters
    faculty_list = [
        'Antony Franklin', 'Ashish Mishra', 'Bheemarjuna Reddy Tamma',
    'KrishnaMohan C', 'Saketha Nath J', 'Jyothi Vedurada',
    'Kotaro Kataoka', 'PandurangaRao M.V', 'Manish Singh',
    'Maria Francis', 'Maunendra Sankar Desarkar', 'Aravind N.R',
    'Nitin Saurabh', 'Praveen Tammana', 'Rajesh Kedia',
    'Rakesh Venkat', 'Ramakrishna Upadrasta', 'Rameshwar Pratap',
    'Rogers Mathew', 'Sathya Peri', 'Saurabh Kumar',
    'Shirshendu Das', 'Sobhan Babu', 'Srijith P. K.',
    'Subrahmanyam Kalyanasundaram', 'Vineeth N. Balasubramanian',
    'Abhijit Das', 'Sandipan D', 'Anupam Sanghi'
    ]

    labs = [room.name for room in RoomLab.query.all()]
    joining_years = [str(y) for y in range(2015, datetime.now().year + 1)]  # dynamic

    return render_template("students_directory.html",
                           students_pagination=students_pagination,
                           faculty_list=faculty_list,
                           labs=labs,
                           joining_years=joining_years,
                           # pass filters back for dropdowns
                           selected_course=course,
                           selected_year=year,
                           selected_joining_year=joining_year,
                           selected_lab=room_lab_name,
                           selected_faculty=faculty,
                           selected_roll=roll)


from models import Student  # make sure you have this imported

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
def edit_equipment(id):
    item = Equipment.query.get_or_404(id)
    students = Student.query.order_by(Student.roll).all()  # fetch all students for dropdown

    if request.method == 'POST':
        item.name = request.form['name']
        item.category = request.form['category']
        item.manufacturer = request.form['manufacturer']
        item.model = request.form['model']
        item.serial_number = request.form['serial_number']
        item.invoice_number = request.form['invoice_number']
        item.cost_per_unit = request.form['cost_per_unit'] or None
        item.location = request.form['location']
        # item.purchase_date = request.form['purchase_date']
        item.status = request.form['status']
        item.po_date = request.form['po_date']
        item.po_number = request.form['po_number']
        item.source_of_fund = request.form['source_of_fund']
        item.warranty_start = request.form['warranty_start']
        item.warranty_expiry = request.form['warranty_expiry']
        item.intender_name = request.form['intender_name']
        item.quantity = request.form['quantity'] or None
        item.department_code = request.form['department_code']
        item.mac_address = request.form['mac_address']
        item.vendor_company = request.form['vendor_company']
        item.vendor_contact_person = request.form['vendor_contact_person']
        item.vendor_mobile = request.form['vendor_mobile']
        item.remarks = request.form['remarks']

        # Handle assigned fields safely
        item.assigned_to_roll = request.form.get('assigned_to_roll') or None
        item.assigned_by = request.form.get('assigned_by') or None

        db.session.commit()
        return redirect(url_for('equipment_list'))

    return render_template('edit_equipment.html', item=item, students=students)


@app.route('/equipment/delete/<int:id>', methods=['POST'])
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    
    # If equipment is assigned, optionally restrict deletion
    if equipment.student:
        flash("Cannot delete equipment that is currently assigned to a student.", "error")
        return redirect(url_for('equipment_list'))

    db.session.delete(equipment)
    db.session.commit()
    flash("Equipment deleted successfully.", "success")
    return redirect(url_for('equipment_list'))


@app.route("/inventory_search", methods=["GET"])
@login_required
def inventory_search():
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    serial_number = request.args.get("serial_number", "").strip()

    query = Equipment.query

    if category:
        query = query.filter(Equipment.category == category)
    if status:
        query = query.filter(Equipment.status == status)
    if serial_number:
        query = query.filter(Equipment.serial_number.ilike(f"%{serial_number}%"))

    equipment_list = query.all()

    return render_template("inventory_search.html", equipment_list=equipment_list)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403

@app.errorhandler(500)
def internal_error(e):
    return render_template("errors/500.html"), 500

from flask import make_response, render_template
from weasyprint import HTML

from flask import render_template, make_response
import pdfkit

from flask import make_response, render_template
from weasyprint import HTML
from models import WorkstationAsset, Equipment, SlurmAccount





from flask import request, render_template, redirect, flash
from google_calendar import create_event
from datetime import datetime, timedelta
from flask import render_template, request, redirect, flash
from datetime import datetime
from google_calendar import create_event  # ✅ make sure this points to your working module

@app.route("/book_lab", methods=["GET", "POST"])
@login_required
def book_lab():
    if request.method == "POST":
        room = request.form.get("room")
        start = request.form.get("start")
        end = request.form.get("end")
        reason = request.form.get("reason")

        # Format as RFC3339
        from datetime import datetime
        start_iso = datetime.fromisoformat(start).isoformat()
        end_iso = datetime.fromisoformat(end).isoformat()

        # Use service function to create the event
        event = create_event(summary=f"{room} Reserved by {current_user.email}",
                             description=reason,
                             start=start_iso,
                             end=end_iso)
        try:
            lab = request.form["lab"]
            user = request.form["user"]
            purpose = request.form["purpose"]
            start_time = request.form["start_time"]
            end_time = request.form["end_time"]

            # Parse datetime inputs
            start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")

            # Create the calendar event
            event_link = create_event(
                lab=lab,
                summary=f"Lab Booking: {lab} by {user}",
                description=purpose,
                start_time=start_dt,
                end_time=end_dt
            )

            if event_link:
                flash("✅ Lab booked successfully!", "success")
                return redirect(event_link)
            else:
                flash("❌ Failed to book the lab. Please check calendar configuration.", "danger")
                return redirect("/book_lab")

        except Exception as e:
            print("🚨 Booking Error:", e)
            flash("❌ Internal error while booking the lab.", "danger")
            return redirect("/book_lab")

        flash("✅ Lab booked and synced with Google Calendar.", "success")
        return redirect("/login_home")
    
    return render_template("book_lab.html")

from google_calendar import get_upcoming_events

@app.route("/lab_schedule/<lab>")
@login_required
def lab_calender(lab):
    calendar_embed_urls = {
        "CS-109": "https://calendar.google.com/calendar/embed?src=31b285e2a089b57ecbfbfc2f879c16406d7a4f3d26d0eb5703cd94a86b4805ff%40group.calendar.google.com&ctz=Asia%2FKolkata",
        "CS-209": "https://calendar.google.com/calendar/embed?src=31b285e2a089b57ecbfbfc2f879c16406d7a4f3d26d0eb5703cd94a86b4805ff%40group.calendar.google.com&ctz=Asia%2FKolkata"
    }

    if lab not in calendar_embed_urls:
        flash("❌ Invalid lab selected.")
        return redirect("/login_home")

    calendar_url = calendar_embed_urls[lab]
    return render_template("lab_schedule.html", lab=lab, calendar_url=calendar_url)




@app.route('/get_students_by_course_year', methods=['GET'])
@login_required
def get_students_by_course_year():
    course = request.args.get('course')
    year = request.args.get('year')
    students = Workstation.query.filter_by(course=course, year=year).all()
    data = [{'roll': s.roll, 'name': s.name, 'email': s.email} for s in students]
    return jsonify(data)

from flask import render_template, request
from models import db
@app.route("/allocate_space", methods=["GET", "POST"])
def allocate_space():
    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        roll = form_data.get("roll", "").strip()
        room = form_data.get("room_lab_name", "").strip()
        cubicle = form_data.get("cubicle_no", "").strip()

        if Workstation.query.filter_by(roll=roll).first():
            error = f"⚠️ Roll number {roll} already exists in the database."
            return render_template("allocate_space.html", error=error, form_data=form_data)

        if Workstation.query.filter_by(room_lab_name=room, cubicle_no=cubicle).first():
            error = f"⚠️ Cubicle {cubicle} in {room} has already been allotted."
            return render_template("allocate_space.html", error=error, form_data=form_data)

        workstation = Workstation(
            name=form_data.get("name"),
            roll=roll,
            course=form_data.get("course"),
            year=form_data.get("year"),
            faculty=form_data.get("faculty"),
            staff_incharge=form_data.get("staff_incharge"),
            email=form_data.get("email"),
            phone=form_data.get("phone"),
            room_lab_name=room,
            cubicle_no=cubicle
        )
        db.session.add(workstation)
        db.session.commit()
        return render_template("allocate_space.html", success=True, form_data={})

    return render_template("allocate_space.html", form_data={})



from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, RoomLab, Cubicle, Equipment
from datetime import datetime





from werkzeug.security import generate_password_hash
import random, string

def random_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))





@app.route("/student_info", methods=["GET", "POST"])
def student_info():
    prefill_roll = (request.args.get("roll") or "").strip()

    if request.method == "POST":
        roll = request.form['roll'].strip()
        email = request.form['email'].strip()

        # Validate profile photo
        # Validate profile photo
# Handle optional profile photo
        file = request.files.get("profile_photo")
        filename = None

        if file and file.filename != "":
            # Validate format
            if not (file.filename.lower().endswith((".jpg", ".jpeg", ".png"))):
                flash("Only JPG or PNG images allowed!", "danger")
                return redirect(url_for("student_info"))

            # Validate size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            if size > 50 * 1024:
                flash("Image must be less than 50 KB!", "danger")
                return redirect(url_for("student_info"))
            file.seek(0)

            # Save image
            filename = secure_filename(f"{roll}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        else:
            # No photo uploaded — skip without error
            filename = None


        # Duplicate check
        if Student.query.get(roll):
            flash("Student already exists!", "warning")
            return redirect(url_for("student_info", roll=roll))

        # Create or Fetch User
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            user = existing_user
            temp_pw = None
        else:
            temp_pw = random_password()
            user = User(
                email=email,
                password=generate_password_hash(temp_pw),
                role="student",
                is_approved=False,
                registered_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()

        # Create Student
        student = Student(
            roll=roll,
            name=request.form['name'],
            course=request.form['course'],
            year=request.form['year'],
            joining_year=request.form['joining_year'],
            faculty=request.form['faculty'],
            email=email,
            phone=request.form.get('phone'),
            user_id=user.id,
            profile_photo=filename   # ✅ Save photo file name
        )
        db.session.add(student)
        db.session.commit()

        # ✅ Send Email Notification
        subject = "CSE Lab Management – Student Registration Successful"
        body = f"""
Dear {student.name},

Your registration in the CSE Lab Management System has been successfully completed.

Student Details:
• Roll No: {student.roll}
• Course: {student.course}
• Year: {student.year}
• Faculty: {student.faculty}
• Email (Username): {student.email}
{"• Temporary Password: " + temp_pw if temp_pw else ""}

Please note:
Your account requires admin approval before you can log in.
Once approved, you will be prompted to change your password during your first login.

Regards,  
CSE Lab Management Team
"""
        send_notification_email(student.email, subject, body)  # ✅ your existing function

        flash("Student successfully registered and Wait for admin approval before you can log in.", "success")
        if current_user.is_authenticated:
            return redirect(url_for("student_info"))
        else:
            return redirect(url_for("login"))

    return render_template("student_info.html", prefill_roll=prefill_roll)
    
@app.route("/Profile_update")
@login_required
def profile_update():
    student = Student.query.filter_by(email=current_user.email).first()
    return render_template("Profile_update.html",
                           student=student,
                           current_year=datetime.now().year)


# ------------------------
# 2. Cubicle Allocation
# ------------------------

# Add at top of app.py if not present
from sqlalchemy.orm import joinedload
from flask import render_template, request, redirect, url_for, flash

# ---------- Helper to build room -> free cubicles map ----------

def build_room_map():
    """
    Returns: { "CS-107": [ {"id": 1, "number": "3"}, ... only free cubicles ], ... }
    """
    rooms = RoomLab.query.options(joinedload(RoomLab.cubicles)).all()
    room_map = {}
    for r in rooms:
        free = [{"id": c.id, "number": c.number} for c in r.cubicles if c.student_roll is None]
        room_map[r.name] = free
    return rooms, room_map

# ============= Cubicle Allocation Page (Create/Change) =============
@app.route("/cubicle_allocation", methods=["GET", "POST"])
@app.route("/cubicle_allocation/<roll>", methods=["GET", "POST"])
@login_required
def cubicle_allocation(roll=None):
    # Pre-fill POST data if redirected
    form_data = None
    error = None
    success = False

    # For dynamic room->free cubicles (and to preselect current cubicle for the roll)
    rooms, room_map = build_room_map(selected_for_roll=roll)

    if request.method == "POST":
        f = request.form
        name = (f.get("name") or "").strip()
        roll_post = (f.get("roll") or "").strip()
        course = f.get("course")
        year = f.get("year")
        faculty = f.get("faculty")
        email = f.get("email")
        phone = f.get("phone")
        room_lab_name = f.get("room_lab_name")  # as string name
        cubicle_no = f.get("cubicle_no")

        form_data = f  # re-render if error

        if not (name and roll_post and room_lab_name and cubicle_no):
            error = "Please fill all required fields (Name, Roll, Room/Lab, Cubicle)."
        else:
            # Ensure student exists or create/update
            student = db.session.get(Student, roll_post)
            if not student:
                student = Student(
                    roll=roll_post, name=name, course=course, year=year,
                    faculty=faculty, email=email, phone=phone
                )
                db.session.add(student)
            else:
                # light update
                student.name = name
                student.course = course
                student.year = year
                student.faculty = faculty
                student.email = email
                student.phone = phone

            # Find room & cubicle
            room = RoomLab.query.filter_by(name=room_lab_name).first()
            if not room:
                error = f"Room {room_lab_name} not found."
            else:
                cub = Cubicle.query.filter_by(room_lab_id=room.id, number=str(cubicle_no)).first()
                if not cub:
                    error = f"Cubicle {cubicle_no} in room {room_lab_name} not found."
                else:
                    # If cub is occupied by someone else, block
                    if cub.student_roll and cub.student_roll != roll_post:
                        error = f"Cubicle {cubicle_no} in room {room_lab_name} is already assigned."
                    else:
                        # If student had previous cubicle, release it
                        prev = Cubicle.query.filter_by(student_roll=roll_post).first()
                        if prev and prev.id != cub.id:
                            prev.student_roll = None

                        # Assign this one
                        cub.student_roll = roll_post
                        try:
                            db.session.commit()
                            success = True
                            form_data = None
                        except Exception as e:
                            db.session.rollback()
                            error = f"Error saving allocation: {e}"

    # For GET (or after POST), pre-fill form with student data if roll provided
    student_obj = db.session.get(Student, roll) if roll else None
    if not form_data and student_obj:
        # fill form_data-like dict for template
        cur_cub = Cubicle.query.filter_by(student_roll=student_obj.roll).first()
        cur_room = cur_cub.room_lab.name if cur_cub else ""
        form_data = {
            "name": student_obj.name,
            "roll": student_obj.roll,
            "course": student_obj.course,
            "year": student_obj.year,
            "faculty": student_obj.faculty,
            "email": student_obj.email,
            "phone": student_obj.phone,
            "room_lab_name": cur_room,
            "cubicle_no": cur_cub.number if cur_cub else "",
        }

    # Pass rooms & JS room_map to template
    return render_template(
        "allocate_space.html",
        form_data=form_data,
        error=error,
        success=success,
        rooms=rooms,
        room_map=room_map,
    )


# ============= Release Cubicle =============
@app.route("/release_cubicle/<int:cubicle_id>", methods=["POST"])
@login_required
def release_cubicle(cubicle_id):
    cub = db.session.get(Cubicle, cubicle_id)
    if not cub or not cub.student_roll:
        flash("Cubicle not found or already free.", "warning")
        return redirect(request.referrer or url_for("allotment_roll_check"))

    roll = cub.student_roll
    try:
        cub.student_roll = None
        db.session.commit()
        flash("Cubicle released.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error releasing cubicle: {e}", "danger")

    return redirect(url_for("allotment_options", roll=roll))

# add near your other imports
from sqlalchemy.orm import joinedload

@app.route("/workstation_allocation", methods=["GET", "POST"])
@app.route("/workstation_allocation/<roll>", methods=["GET", "POST"])
def workstation_allocation(roll=None):
    # 1) Read prefill roll from URL or param
    roll_prefill = (roll or request.args.get("roll", "")).strip() or None

    # 2) Load rooms with cubicles (needed for dropdown + room_map)
    rooms = RoomLab.query.options(joinedload(RoomLab.cubicles)).all()

    # 2a) Build JSON-safe room_map {room_name: [{id, number}, ...free only]}
    room_map = {}
    for r in rooms:
        free = [{"id": c.id, "number": c.number}
                for c in r.cubicles if c.student_roll is None]
        room_map[r.name] = free

    # 3) Pre-selected room/cubicle if this roll already has a cubicle
    room_lab_name, cubicle_no = None, None
    if roll_prefill:
        cub = (Cubicle.query
               .options(joinedload(Cubicle.room_lab))
               .filter(Cubicle.student_roll == roll_prefill)
               .order_by(Cubicle.id.asc())
               .first())
        if cub:
            room_lab_name = cub.room_lab.name
            cubicle_no = cub.number

    # 4) Handle POST (save a workstation record)
    if request.method == "POST":
        f = request.form
        roll_post = (f.get("roll") or "").strip()
        if not roll_post:
            flash("Roll number is required.", "warning")
            return redirect(request.url)

        # Ensure student exists
        if not Student.query.get(roll_post):
            flash("Student does not exist. Please register first.", "warning")
            return redirect(url_for("student_info", prefill_roll=roll_post))

        # If room/cubicle not provided, auto-fill from existing assignment (if any)
        room_val = (f.get("room_lab_name") or "").strip()
        cub_val  = (f.get("cubicle_no") or "").strip()
        if not room_val or not cub_val:
            cub = (Cubicle.query
                   .options(joinedload(Cubicle.room_lab))
                   .filter(Cubicle.student_roll == roll_post)
                   .order_by(Cubicle.id.asc())
                   .first())
            if cub:
                room_val = room_val or cub.room_lab.name
                cub_val  = cub_val  or cub.number

        ws = Workstation(
            roll=roll_post,
            room_lab_name=room_val or None,
            cubicle_no=cub_val or None,
            manufacturer=f.get("manufacturer"),
            otherManufacturer=f.get("otherManufacturer"),
            model=f.get("model"),
            serial=f.get("serial"),
            os=f.get("os"),
            otherOs=f.get("otherOs"),
            processor=f.get("processor"),
            cores=f.get("cores"),
            ram=f.get("ram"),
            otherRam=f.get("otherRam"),
            storage_type1=f.get("storage_type1"),
            storage_capacity1=f.get("storage_capacity1"),
            storage_type2=f.get("storage_type2"),
            storage_capacity2=f.get("storage_capacity2"),
            gpu=f.get("gpu"),
            vram=f.get("vram"),
            issue_date=f.get("issue_date"),
            system_required_till=f.get("system_required_till"),
            po_date=f.get("po_date"),
            source_of_fund=f.get("source_of_fund"),
            keyboard_provided=f.get("keyboard_provided"),
            keyboard_details=f.get("keyboard_details"),
            mouse_provided=f.get("mouse_provided"),
            mouse_details=f.get("mouse_details"),
            monitor_provided=f.get("monitor_provided"),
            monitor_details=f.get("monitor_details"),
            monitor_size=f.get("monitor_size"),
            monitor_serial=f.get("monitor_serial"),
            mac_address=f.get("mac_address"),
        )
        try:
            db.session.add(ws)
            db.session.commit()
            flash("Workstation allocated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Could not save workstation: {e}", "danger")

        return redirect(url_for("workstation_allocation", roll=roll_post))

    # 5) Render
    return render_template(
        "workstation_allocation.html",
        rooms=rooms,
        roll_prefill=roll_prefill,
        room_lab_name=room_lab_name,
        cubicle_no=cubicle_no,
        room_map=room_map,   # <-- important for template 
        
    )


# routes.py (or app.py)
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Student, Equipment, EquipmentHistory
# --- IT Equipment Assignment + Return ---
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_

# @app.route("/it_equipment_assign/<roll>", methods=["GET", "POST"])
# @login_required
# def it_equipment_assign(roll):
#     student = Student.query.filter_by(roll=roll).first_or_404()

    # if request.method == "POST" and "return_equipment_id" in request.form:
    #     equipment_id = request.form.get("return_equipment_id", type=int)
    #     eq = Equipment.query.get_or_404(equipment_id)

    #     if not eq.assigned_to_roll:
    #         flash("This equipment is not currently assigned.", "warning")
    #     else:
          
    #         assigned_date = eq.assigned_date
    #         expected_return = getattr(eq, "expected_return", None)
    #         return_date = datetime.utcnow()

    #         eq.assigned_to_roll = None
    #         eq.status = "Available"

            
    #         last_hist = EquipmentHistory.query.filter_by(
    #             equipment_id=eq.id,
    #             assigned_to_roll=student.roll
    #         ).order_by(EquipmentHistory.id.desc()).first()
    #         if last_hist and last_hist.unassigned_date is None:
    #             last_hist.unassigned_date = return_date
    #             last_hist.status_snapshot = "Returned"

    #         db.session.commit()
    #         flash(f"Returned {eq.serial_number} successfully.", "success")

           
    #         faculty_incharge = student.faculty or "Not Assigned"
    #         staff_incharge = student.cubicle.room_lab.staff_incharge \
    #             if student.cubicle and student.cubicle.room_lab else "Not Assigned"

    #         email_subject = f"Equipment Returned: {eq.manufacturer} {eq.model}"
    #         email_body = f"""
    # <html>
    # <body>
    # <p>Hello {student.name},</p>
    # <p>The following equipment has been returned:</p>
    # <table border="1" cellpadding="6">
    # <tr><th>Field</th><th>Value</th></tr>
    # <tr><td>Category</td><td>{eq.category}</td></tr>
    # <tr><td>Serial</td><td>{eq.serial_number}</td></tr>
    # <tr><td>Model</td><td>{eq.manufacturer} {eq.model}</td></tr>
    # <tr><td>Location</td><td>{eq.location}</td></tr>
    # <tr><td>Assigned Date</td><td>{assigned_date.strftime('%Y-%m-%d %H:%M') if assigned_date else '-'}</td></tr>
    # <tr><td>Expected Return Date</td><td>{expected_return if expected_return else '-'}</td></tr>
    # <tr><td>Actual Return Date</td><td>{return_date.strftime('%Y-%m-%d %H:%M')}</td></tr>
    # <tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
    # <tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
    # </table>
    # <p>Regards,<br>CSE Lab Admin</p>
    # </body>
    # </html>
    # """
    #         msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
    #         threading.Thread(target=send_async_email, args=[app, msg]).start()


    
    # if request.method == "POST" and "equipment_id" in request.form:
    #     equipment_id = request.form.get("equipment_id", type=int)
    #     issue_date = request.form.get("ifEQUIPMENTssue_date")        
    #     expected_return = request.form.get("expected_return")  
    #     eq = Equipment.query.get_or_404(equipment_id)

    #     if eq.assigned_to_roll:
    #         flash("Equipment already assigned.", "danger")
    #     else:
    #         eq.assigned_to_roll = student.roll
    #         eq.assigned_by = getattr(current_user, "email", None)
    #         eq.assigned_date = datetime.strptime(issue_date, "%Y-%m-%d") if issue_date else datetime.utcnow()
    #         eq.expected_return = expected_return
    #         eq.status = "Issued"

    #         hist = EquipmentHistory(
    #             equipment_id=eq.id,
    #             assigned_to_roll=student.roll,
    #             assigned_by=eq.assigned_by,
    #             assigned_date=eq.assigned_date,
    #             status_snapshot=eq.status,
    #         )
    #         db.session.add(hist)
    #         db.session.commit()
    #         flash(f"Assigned {eq.serial_number} to {student.name}.", "success")

           
    #         faculty_incharge = student.faculty or "Not Assigned"
    #         staff_incharge = student.cubicle.room_lab.staff_incharge \
    #             if student.cubicle and student.cubicle.room_lab else "Not Assigned"

    #         email_subject = f"Equipment Assigned: {eq.manufacturer} {eq.model}"
    #         email_body = f"""
    # <html>
    # <body>
    # <p>Hello {student.name},</p>
    # <p>The following equipment has been assigned to you:</p>
    # <table border="1" cellpadding="6">
    # <tr><th>Field</th><th>Value</th></tr>
    # <tr><td>Category</td><td>{eq.category}</td></tr>
    # <tr><td>Serial</td><td>{eq.serial_number}</td></tr>
    # <tr><td>Model</td><td>{eq.manufacturer} {eq.model}</td></tr>
    # <tr><td>Location</td><td>{eq.location}</td></tr>
    # <tr><td>Assigned Date</td><td>{eq.assigned_date.strftime('%Y-%m-%d %H:%M')}</td></tr>
    # <tr><td>Expected Return Date</td><td>{expected_return if expected_return else '-'}</td></tr>
    # <tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
    # <tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
    # </table>
    # <p>Please contact your faculty or staff in-charge for any questions.</p>
    # <p>Regards,<br>CSE Lab Admin</p>
    # </body>
    # </html>
    # """
    #         msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
    #         threading.Thread(target=send_async_email, args=[app, msg]).start()


    # location = (request.args.get("location") or "").strip()
    # intender_name = (request.args.get("intender_name") or "").strip()

    # base_q = Equipment.query
    # if location:
    #     base_q = base_q.filter(Equipment.location == location)
    # if intender_name:
    #     base_q = base_q.filter(Equipment.intender_name == intender_name)

    # available_equipment = base_q.filter(
    #     Equipment.assigned_to_roll.is_(None),
    #     or_(Equipment.status.is_(None), Equipment.status == "Available")
    # ).order_by(Equipment.manufacturer, Equipment.model).all()

    # student_equipment = Equipment.query.filter_by(assigned_to_roll=student.roll) \
    #     .order_by(Equipment.assigned_date.desc().nullslast()) \
    #     .all()

    # return render_template(
    #     "it_equipment_assign.html",
    #     student=student,
    #     available_equipment=available_equipment,
    #     student_equipment=student_equipment,
    # )


  
    # location = (request.args.get("location") or "").strip()
    # intender_name = (request.args.get("intender_name") or "").strip()

    # base_q = Equipment.query
    # if location:
    #     base_q = base_q.filter(Equipment.location == location)
    # if intender_name:
    #     base_q = base_q.filter(Equipment.intender_name == intender_name)

    # available_equipment = base_q.filter(
    #     Equipment.assigned_to_roll.is_(None),
    #     or_(Equipment.status.is_(None), Equipment.status == "Available")
    # ).order_by(Equipment.manufacturer, Equipment.model).all()

 
    # student_equipment = Equipment.query.filter_by(assigned_to_roll=student.roll) \
    #     .order_by(Equipment.assigned_date.desc().nullslast()) \
    #     .all()

    # return render_template(
    #     "it_equipment_assign.html",
    #     student=student,
    #     available_equipment=available_equipment,
    #     student_equipment=student_equipment,
    # )

# STUDENT
@app.route("/it_equipment_assign/<roll>", methods=["GET", "POST"])
@login_required
def it_equipment_assign(roll):
    return it_equipment_assign_generic("student", roll)

# STAFF
@app.route("/staff/equipment/<int:pid>", methods=["GET", "POST"])
@login_required
def it_equipment_assign_staff(pid):
    return it_equipment_assign_generic("staff", pid)

# FACULTY
@app.route("/faculty/equipment/<int:pid>", methods=["GET", "POST"])
@login_required
def it_equipment_assign_faculty(pid):
    return it_equipment_assign_generic("faculty", pid)

from sqlalchemy import or_
from datetime import datetime
from flask import request, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

def it_equipment_assign_generic(owner_type, key):
    """
    owner_type: 'student' | 'staff' | 'faculty'
    key:
        - student: roll (string)
        - staff:   staff.id (int)
        - faculty: faculty.id (int)
    """

    # ------- Resolve person & helpers -------
    if owner_type == "student":
        person = Student.query.filter_by(roll=key).first_or_404()
        id_value = person.roll
        id_label = "Roll"
        back_url = url_for("allotment_options", roll=person.roll)

        def is_owner(eq):
            return eq.assigned_to_roll == person.roll

        def clear_owner(eq):
            eq.assigned_to_roll = None

        def set_owner(eq):
            eq.assigned_to_roll = person.roll

        def hist_filter_for(eid):
            return EquipmentHistory.query.filter_by(
                equipment_id=eid,
                assigned_to_roll=person.roll
            )

        def make_history(eq):
            return EquipmentHistory(
                equipment_id=eq.id,
                assigned_to_roll=person.roll,
                assigned_by=eq.assigned_by,
                assigned_date=eq.assigned_date,
                expected_return=eq.expected_return,
                status_snapshot=eq.status,
            )

        current_q = Equipment.query.filter_by(assigned_to_roll=person.roll)

    elif owner_type == "staff":
        person = Staff.query.get_or_404(key)
        id_value = person.staff_id
        id_label = "Staff ID"
        back_url = url_for("allotment_options_staff", sid=person.id)

        def is_owner(eq):
            return eq.assigned_to_staff_id == person.id

        def clear_owner(eq):
            eq.assigned_to_staff_id = None

        def set_owner(eq):
            eq.assigned_to_staff_id = person.id

        def hist_filter_for(eid):
            return EquipmentHistory.query.filter_by(
                equipment_id=eid,
                assigned_to_staff_id=person.id
            )

        def make_history(eq):
            return EquipmentHistory(
                equipment_id=eq.id,
                assigned_to_staff_id=person.id,
                assigned_by=eq.assigned_by,
                assigned_date=eq.assigned_date,
                expected_return=eq.expected_return,
                status_snapshot=eq.status,
            )

        current_q = Equipment.query.filter_by(assigned_to_staff_id=person.id)

    elif owner_type == "faculty":
        person = Faculty.query.get_or_404(key)
        id_value = person.faculty_id
        id_label = "Faculty ID"
        back_url = url_for("allotment_options_faculty", fid=person.id)

        def is_owner(eq):
            return eq.assigned_to_faculty_id == person.id

        def clear_owner(eq):
            eq.assigned_to_faculty_id = None

        def set_owner(eq):
            eq.assigned_to_faculty_id = person.id

        def hist_filter_for(eid):
            return EquipmentHistory.query.filter_by(
                equipment_id=eid,
                assigned_to_faculty_id=person.id
            )

        def make_history(eq):
            return EquipmentHistory(
                equipment_id=eq.id,
                assigned_to_faculty_id=person.id,
                assigned_by=eq.assigned_by,
                assigned_date=eq.assigned_date,
                expected_return=eq.expected_return,
                status_snapshot=eq.status,
            )

        current_q = Equipment.query.filter_by(assigned_to_faculty_id=person.id)

    else:
        abort(400)

    # ---------- RETURN equipment ----------
    if request.method == "POST" and "return_equipment_id" in request.form:
        equipment_id = request.form.get("return_equipment_id", type=int)
        eq = Equipment.query.get_or_404(equipment_id)

        if not is_owner(eq):
            flash("This equipment is not currently assigned to this person.", "warning")
        else:
            assigned_date = eq.assigned_date
            expected_return = eq.expected_return
            return_date = datetime.utcnow()

            # Clear owner + mark available
            clear_owner(eq)
            eq.status = "Available"

            # Close last history row for this person + equipment
            last_hist = hist_filter_for(eq.id).order_by(EquipmentHistory.id.desc()).first()
            if last_hist and last_hist.unassigned_date is None:
                last_hist.unassigned_date = return_date
                last_hist.status_snapshot = "Returned"

            db.session.commit()
            flash(f"Returned {eq.serial_number} successfully.", "success")

            # Email: only for student
            if owner_type == "student":
                student = person
                faculty_incharge = student.faculty or "Not Assigned"
                staff_incharge = (
                    student.cubicle.room_lab.staff_incharge
                    if student.cubicle and student.cubicle.room_lab
                    else "Not Assigned"
                )

                email_subject = f"Equipment Returned: {eq.manufacturer} {eq.model}"
                email_body = f"""
<html>
<body>
<p>Hello {student.name},</p>
<p>The following equipment has been returned:</p>
<table border="1" cellpadding="6">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Category</td><td>{eq.category}</td></tr>
<tr><td>Serial</td><td>{eq.serial_number}</td></tr>
<tr><td>Model</td><td>{eq.manufacturer} {eq.model}</td></tr>
<tr><td>Location</td><td>{eq.location}</td></tr>
<tr><td>Assigned Date</td><td>{assigned_date.strftime('%Y-%m-%d %H:%M') if assigned_date else '-'}</td></tr>
<tr><td>Expected Return Date</td><td>{expected_return or '-'}</td></tr>
<tr><td>Actual Return Date</td><td>{return_date.strftime('%Y-%m-%d %H:%M')}</td></tr>
<tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
<tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
</table>
<p>Regards,<br>CSE Lab Admin</p>
</body>
</html>
"""
                msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
                threading.Thread(target=send_async_email, args=[app, msg]).start()

    # ---------- ASSIGN equipment ----------
    if request.method == "POST" and "equipment_id" in request.form:
        equipment_id = request.form.get("equipment_id", type=int)
        issue_date_str = request.form.get("issue_date")
        expected_return = request.form.get("expected_return")
        eq = Equipment.query.get_or_404(equipment_id)

        # Already assigned to someone?
        if eq.assigned_to_roll or eq.assigned_to_staff_id or eq.assigned_to_faculty_id:
            flash("Equipment already assigned.", "danger")
        else:
            set_owner(eq)
            eq.assigned_by = getattr(current_user, "email", None)

            if issue_date_str:
                eq.assigned_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
            else:
                eq.assigned_date = datetime.utcnow()

            eq.expected_return = expected_return
            eq.status = "Issued"

            # History row
            hist = make_history(eq)
            db.session.add(hist)
            db.session.commit()
            flash(f"Assigned {eq.serial_number} to {person.name}.", "success")

            # Email only for students
            if owner_type == "student":
                student = person
                faculty_incharge = student.faculty or "Not Assigned"
                staff_incharge = (
                    student.cubicle.room_lab.staff_incharge
                    if student.cubicle and student.cubicle.room_lab
                    else "Not Assigned"
                )

                email_subject = f"Equipment Assigned: {eq.manufacturer} {eq.model}"
                email_body = f"""
<html>
<body>
<p>Hello {student.name},</p>
<p>The following equipment has been assigned to you:</p>
<table border="1" cellpadding="6">
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Category</td><td>{eq.category}</td></tr>
<tr><td>Serial</td><td>{eq.serial_number}</td></tr>
<tr><td>Model</td><td>{eq.manufacturer} {eq.model}</td></tr>
<tr><td>Location</td><td>{eq.location}</td></tr>
<tr><td>Assigned Date</td><td>{eq.assigned_date.strftime('%Y-%m-%d %H:%M')}</td></tr>
<tr><td>Expected Return Date</td><td>{expected_return or '-'}</td></tr>
<tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
<tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
</table>
<p>Please contact your faculty or staff in-charge for any questions.</p>
<p>Regards,<br>CSE Lab Admin</p>
</body>
</html>
"""
                msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
                threading.Thread(target=send_async_email, args=[app, msg]).start()

    # ---------- Filters ----------
    location = (request.args.get("location") or "").strip()
    intender_name = (request.args.get("intender_name") or "").strip()

    base_q = Equipment.query
    if location:
        base_q = base_q.filter(Equipment.location == location)
    if intender_name:
        base_q = base_q.filter(Equipment.intender_name == intender_name)

    # Only Available equipment and not assigned to anyone
    available_equipment = base_q.filter(
        Equipment.assigned_to_roll.is_(None),
        Equipment.assigned_to_staff_id.is_(None),
        Equipment.assigned_to_faculty_id.is_(None),
        or_(Equipment.status.is_(None), Equipment.status == "Available")
    ).order_by(Equipment.manufacturer, Equipment.model).all()

    current_equipment = current_q.order_by(Equipment.assigned_date.desc().nullslast()).all()

    return render_template(
        "it_equipment_assign.html",
        owner_type=owner_type,
        person=person,
        id_label=id_label,
        id_value=id_value,
        available_equipment=available_equipment,
        current_equipment=current_equipment,
        back_url=back_url,
    )


# --- IT Equipment by Location + Intender ---
@app.route("/it_equipment_by_location_faculty_staff", methods=["GET"])
@login_required
def it_equipment_by_location_faculty_staff():
    # Filters
    location = (request.args.get("location") or "").strip()
    intender_name = (request.args.get("intender_name") or "").strip()

    # Base query with optional filters
    base_q = Equipment.query
    if location:
        base_q = base_q.filter(Equipment.location == location)
    if intender_name:
        base_q = base_q.filter(Equipment.intender_name == intender_name)

    # Results by status
    available_equipment = base_q.filter(
        Equipment.assigned_to_roll.is_(None),
        or_(Equipment.status.is_(None), Equipment.status == "Available")
    ).order_by(Equipment.manufacturer, Equipment.model).all()

    issued_equipment = base_q.filter(
        Equipment.assigned_to_roll.isnot(None)
    ).order_by(Equipment.manufacturer, Equipment.model).all()

    scrapped_equipment = base_q.filter(Equipment.status == "Scrapped") \
        .order_by(Equipment.manufacturer, Equipment.model).all()

    retired_equipment = base_q.filter(Equipment.status == "Retired") \
        .order_by(Equipment.manufacturer, Equipment.model).all()

    return render_template(
        "it_equipment_by_location_faculty_staff.html",
        location=location,
        intender_name=intender_name,
        available_equipment=available_equipment,
        issued_equipment=issued_equipment,
        scrapped_equipment=scrapped_equipment,
        retired_equipment=retired_equipment,
    )


@app.route("/allotted_roll_check", methods=["GET", "POST"])
def allotted_roll_check():
    if request.method == "POST":
        roll = request.form.get("roll", "").strip()

        student = Student.query.get(roll)
        if not student:
            flash("No student found with this roll number.", "danger")
            return redirect(url_for("allotted_roll_check"))

        # Success → send to hub
        return redirect(url_for("allotment_options", roll=roll))

    return render_template("allotted_roll_check.html")

@app.route("/allotment_options/<roll>")
@login_required
def allotment_options(roll):
    student = Student.query.get(roll)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("allotted_roll_check"))

    # --- Current Cubicle ---
    current_cubicle = Cubicle.query.filter_by(student_roll=roll).first()

    # --- Cubicle History (optional, for now just current) ---
    cubicle_history = [current_cubicle] if current_cubicle else []

    # --- Workstations ---
    workstation_active = (
        WorkstationAssignment.query
        .filter_by(student_roll=roll, is_active=True)
        .order_by(WorkstationAssignment.issue_date.desc())
        .all()
    )
    workstation_history = (
        WorkstationAssignment.query
        .filter_by(student_roll=roll)
        .order_by(WorkstationAssignment.issue_date.desc())
        .all()
    )

    # --- Equipment ---
    equipment_active = (
        Equipment.query
        .filter_by(assigned_to_roll=roll)
        .all()
    )
    # attach Equipment object for each history entry
    equipment_history = (
        EquipmentHistory.query
        .filter_by(assigned_to_roll=roll)
        .order_by(EquipmentHistory.assigned_date.desc())
        .all()
    )
    for eq in equipment_history:
        eq.equipment_obj = Equipment.query.get(eq.equipment_id)
        # optional: get lab staff incharge
        student_assigned = Student.query.filter_by(roll=eq.assigned_to_roll).first()
        cubicle = student_assigned.cubicle if student_assigned else None
        eq.staff_incharge = cubicle.room_lab.staff_incharge if cubicle else "—"

    return render_template(
        "allotment_options.html",
        roll=roll,
        student=student,
        current_cubicle=current_cubicle,
        cubicle_history=cubicle_history,
        workstation_active=workstation_active,
        workstation_history=workstation_history,
        equipment_active=equipment_active,
        equipment_history=equipment_history,
    )


# ============= Return/Delete a Workstation Assignment =============
@app.route("/workstation_delete/<int:ws_id>", methods=["POST"])
@login_required
def workstation_delete(ws_id):
    """Interpret as 'return' the workstation assignment (end & free)."""
    asg = db.session.get(WorkstationAssignment, ws_id)
    if not asg or not asg.is_active:
        flash("Assignment not found or already returned.", "warning")
        return redirect(request.referrer or url_for("allotted_roll_check"))

    try:
        # mark returned
        asg.end_date = date.today().isoformat()
        asg.is_active = False
        # free asset
        asset = db.session.get(WorkstationAsset, asg.workstation_id)
        if asset:
            asset.status = "Available"
        db.session.commit()
        flash("Workstation returned successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error returning workstation: {e}", "danger")

    return redirect(url_for("allotment_options", roll=asg.student_roll))


# ============= Unassign IT equipment =============
@app.route("/unassign_equipment/<int:eq_id>", methods=["POST"])
@login_required
def unassign_equipment(eq_id):
    eq = db.session.get(Equipment, eq_id)
    if not eq or not eq.assigned_to_roll:
        flash("Equipment not assigned or not found.", "warning")
        return redirect(request.referrer or url_for("allotted_roll_check"))

    roll = eq.assigned_to_roll

    try:
        # ✅ Find the active history entry
        hist = EquipmentHistory.query.filter_by(
            equipment_id=eq.id,
            unassigned_date=None  # Active record
        ).first()

        if hist:
            hist.unassigned_date = datetime.utcnow()  # ✅ Mark return timestamp

        # ✅ Clear current assignment in Equipment table
        eq.assigned_to_roll = None
        eq.assigned_date = None
        eq.status = "Available"

        db.session.commit()
        flash("Equipment returned successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error unassigning equipment: {e}", "danger")

    return redirect(url_for("allotment_options", roll=roll))


# =========================
# Workstation Inventory (Assets)
# =========================

from sqlalchemy.orm import joinedload
from datetime import date
from flask import request, render_template, redirect, url_for, flash

@app.route("/assets")
def assets_list():
    q = WorkstationAsset.query

    # Get filters from query string
    status = request.args.get("status")
    search = request.args.get("search", "").strip()
    location = request.args.get("location")
    indenter = request.args.get("indenter")

    # Apply filters
    if status:
        q = q.filter(WorkstationAsset.status == status)
    if location:
        q = q.filter(WorkstationAsset.location == location)
    if indenter:
        q = q.filter(WorkstationAsset.indenter == indenter)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (WorkstationAsset.serial.ilike(like)) |
            (WorkstationAsset.model.ilike(like)) |
            (WorkstationAsset.manufacturer.ilike(like))
        )

    assets = q.order_by(WorkstationAsset.id.desc()).all()

    # Distinct values for dropdown filters
    locations = [l[0] for l in db.session.query(WorkstationAsset.location).distinct().all() if l[0]]
    indenters = [i[0] for i in db.session.query(WorkstationAsset.indenter).distinct().all() if i[0]]

    return render_template(
        "assets_list.html",
        assets=assets,
        status=status,
        search=search,
        location=location,
        indenter=indenter,
        locations=locations,
        indenters=indenters,
    )

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from random import randint
@app.route("/clone_workstation/<int:asset_id>", methods=["GET", "POST"])
def clone_workstation(asset_id):
    src = WorkstationAsset.query.get_or_404(asset_id)

    # local helper, independent of other routes
    def safe_int(val):
        try:
            return int(val)
        except Exception:
            return None

    if request.method == "POST":
        f = request.form

        # Basic fields (take from form, not from src, so user can change them)
        manufacturer = (f.get("manufacturer") or "").strip()
        otherManufacturer = (f.get("otherManufacturer") or "").strip()
        model = (f.get("model") or "").strip()
        location = (f.get("location") or "").strip()
        indenter_full = (f.get("indenter") or "").strip()
        serial = (f.get("serial") or "").strip()
        status = (f.get("status") or "Available").strip()

        os_val = (f.get("os") or None)
        otherOs_val = (f.get("otherOs") or None)
        mac_address = (f.get("mac_address") or "").strip() or None
        source_of_funds = (f.get("source_of_funds") or "").strip() or None

        # Required checks
        if not manufacturer:
            flash("Manufacturer is required", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        if manufacturer == "Others" and not otherManufacturer:
            flash("Please specify other manufacturer", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        if not model:
            flash("Model is required", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        if not location:
            flash("Location is required", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        if not indenter_full:
            flash("Indenter is required", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        if not serial:
            flash("Serial number is required.", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        # Serial must be unique
        if WorkstationAsset.query.filter_by(serial=serial).first():
            flash("Serial already exists. Enter a unique serial number.", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        # MAC must also be unique if provided
        if mac_address and WorkstationAsset.query.filter_by(mac_address=mac_address).first():
            flash("MAC address already exists. Please provide a unique MAC.", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        # Dates
        po_date_raw = f.get("po_date") or ""
        po_date = parse_date_safe(po_date_raw)
        if po_date_raw and not po_date:
            flash("PO date invalid. Use YYYY-MM-DD.", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        warranty_start = parse_date_safe(f.get("warranty_start"))
        warranty_expiry = parse_date_safe(f.get("warranty_expiry"))
        if warranty_start and warranty_expiry and warranty_expiry < warranty_start:
            flash("Warranty expiry must be same or after warranty start.", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

        # RAM & storage
        ram = (f.get("ram") or "").strip() or None
        otherRam = (f.get("otherRam") or "").strip() or None
        ram_size_gb = safe_int(f.get("ram_size_gb"))

        storage_type1 = f.get("storage_type1") or None
        storage_capacity1 = safe_int(f.get("storage_capacity1"))
        storage_type2 = f.get("storage_type2") or None
        storage_capacity2 = safe_int(f.get("storage_capacity2"))

        # Processor JSON from form
        processor_count = int(f.get("processor_count") or 0)
        processors = []
        for i in range(1, processor_count + 1):
            name = (f.get(f"processor_{i}_name") or "").strip()
            cores = safe_int(f.get(f"processor_{i}_cores"))
            if name or cores is not None:
                processors.append({"name": name or None, "cores": cores})

        # GPU JSON from form
        has_gpu = (f.get("has_gpu") or "no") == "yes"
        gpus = []
        if has_gpu:
            gpu_count = int(f.get("gpu_count") or 1)
            for i in range(1, gpu_count + 1):
                gname = (f.get(f"gpu_{i}_name") or "").strip()
                vram = safe_int(f.get(f"gpu_{i}_vram"))
                if gname or vram is not None:
                    gpus.append({"name": gname or None, "vram": vram})

        # Department code (based on NEW values, like asset_new)
        po_token = po_date_raw.replace("-", "") if po_date_raw else "NA"
        indenter_clean = indenter_full.replace("Dr. ", "").replace("Prof. ", "")
        indenter_first = indenter_clean.split()[0] if indenter_clean else "Unknown"
        dep_base = f"CSE/{po_token}/{model}/{manufacturer}/{indenter_first}/{serial}"
        department_code = dep_base
        suffix = 1
        while WorkstationAsset.query.filter_by(department_code=department_code).first():
            suffix += 1
            department_code = f"{dep_base}-{suffix}"

        # Build cloned asset
        new_asset = WorkstationAsset(
            manufacturer=manufacturer,
            otherManufacturer=otherManufacturer or None,
            model=model,
            serial=serial,

            os=os_val,
            otherOs=otherOs_val,
            mac_address=mac_address,

            # Keep legacy single CPU/GPU for compatibility (copy from src)
            processor=src.processor,
            cores=src.cores,
            gpu=src.gpu,
            vram=src.vram,

            # RAM / storage
            ram=ram,
            otherRam=otherRam,
            ram_size_gb=ram_size_gb,
            storage_type1=storage_type1,
            storage_capacity1=storage_capacity1,
            storage_type2=storage_type2,
            storage_capacity2=storage_capacity2,

            # Procurement / fund
            po_number=f.get("po_number") or None,
            po_date=po_date,
            source_of_fund=f.get("source_of_fund") or None,
            warranty_start=warranty_start,
            warranty_expiry=warranty_expiry,
            # Vendor
            vendor_company=f.get("vendor_company") or None,
            vendor_contact_person=f.get("vendor_contact_person") or None,
            vendor_mobile=f.get("vendor_mobile") or None,

            # Lifecycle
            status=status,
            location=location,
            indenter=indenter_full,
            department_code=department_code,

            # Reuse same PO / invoice file (no need to re-upload)
            po_invoice_filename=src.po_invoice_filename,
        )

        # Processors / GPUs JSON
        try:
            # if form gave nothing, fall back to src JSON
            if not processors:
                processors = src.get_processors()
            if not gpus:
                gpus = src.get_gpus()

            new_asset.set_processors(processors if processors else None)
            new_asset.set_gpus(gpus if gpus else None)
        except Exception:
            new_asset.processors = json.dumps(processors) if processors else None
            new_asset.gpus = json.dumps(gpus) if gpus else None

        # Commit
        try:
            db.session.add(new_asset)
            db.session.commit()
            flash(f"✅ Asset cloned successfully — Department Code: {department_code}", "success")
            return redirect(url_for("assets_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error cloning asset: {e}", "danger")
            return render_template(
                "asset_form.html",
                asset=src,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list(),
                clone_mode=True,
            )

    # GET: reuse asset_form, but in clone mode
    return render_template(
        "asset_form.html",
        asset=src,
        faculty_list=get_faculty_list(),
        staff_list=get_staff_list(),
        clone_mode=True,
    )



import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import  request, render_template, redirect, url_for, flash, send_from_directory
from models import db, WorkstationAsset

# Ensure UPLOAD_FOLDER and ALLOWED_EXTENSIONS are set in app config earlier
# app.config.setdefault('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
# app.config.setdefault('ALLOWED_EXTENSIONS', {'pdf','png','jpg','jpeg'})
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def parse_date_safe(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def safe_int(val):
    try:
        return int(val)
    except Exception:
        return None

# explicit static lists (as requested)
def get_faculty_list():
    return [
      'Antony Franklin','Ashish Mishra','Bheemarjuna Reddy Tamma',
      'KrishnaMohan C','Saketha Nath J','Jyothi Vedurada',
      'Kotaro Kataoka','PandurangaRao M.V','Manish Singh',
      'Maria Francis','Maunendra Sankar Desarkar','Aravind N.R',
      'Nitin Saurabh','Praveen Tammana','Rajesh Kedia',
      'Rakesh Venkat','Ramakrishna Upadrasta','Rameshwar Pratap',
      'Rogers Mathew','Sathya Peri','Saurabh Kumar',
      'Shirshendu Das','Sobhan Babu','Srijith P. K.',
      'Subrahmanyam Kalyanasundaram','Vineeth N. Balasubramanian',
      'Abhijit Das','Sandipan D','Anupam Sanghi'
    ]

def get_staff_list():
    return [
      'Praveen Kumar G','Shiva Kumar Reddy','Sunitha M',
      'Nikith Reddy','Vijay Chakravarthy','Syam N','Jathin S'
    ]

@app.route("/assets/new", methods=["GET", "POST"])
def asset_new():
    if request.method == "POST":
        f = request.form

        # Basic required fields
        manufacturer = (f.get("manufacturer") or "").strip()
        otherManufacturer = (f.get("otherManufacturer") or "").strip()
        model = (f.get("model") or "").strip()
        location = (f.get("location") or "").strip()
        indenter_full = (f.get("indenter") or "").strip()
        serial = (f.get("serial") or "").strip()
        status = (f.get("status") or "Available").strip()

        # Required checks
        if not manufacturer:
            flash("Manufacturer is required", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())
        if manufacturer == "Others" and not otherManufacturer:
            flash("Please specify other manufacturer", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())
        if not model:
            flash("Model is required", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())
        if not location:
            flash("Location is required", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())
        if not indenter_full:
            flash("Indenter is required", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())
        if not serial:
            flash("Serial number is required.", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())

        # Serial uniqueness
        if WorkstationAsset.query.filter_by(serial=serial).first():
            flash("Serial already exists. Enter a unique serial number.", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())

        # Safe integer parser
        def safe_int(val):
            try:
                return int(val)
            except Exception:
                return None

        # Dates
        po_date_raw = f.get("po_date") or ""
        po_date = parse_date_safe(po_date_raw)
        if po_date_raw and not po_date:
            flash("PO date invalid. Use YYYY-MM-DD.", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())

        warranty_start = parse_date_safe(f.get("warranty_start"))
        warranty_expiry = parse_date_safe(f.get("warranty_expiry"))
        if warranty_start and warranty_expiry and warranty_expiry < warranty_start:
            flash("Warranty expiry must be same or after warranty start.", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())

        # RAM & storage
        ram = (f.get("ram") or "").strip() or None
        otherRam = (f.get("otherRam") or "").strip() or None
        ram_size_gb = safe_int(f.get("ram_size_gb"))

        storage_type1 = f.get("storage_type1") or None
        storage_capacity1 = safe_int(f.get("storage_capacity1"))
        storage_type2 = f.get("storage_type2") or None
        storage_capacity2 = safe_int(f.get("storage_capacity2"))

        # Processor JSON
        processor_count = int(f.get("processor_count") or 0)
        processors = []
        for i in range(1, processor_count + 1):
            name = (f.get(f"processor_{i}_name") or "").strip()
            cores = safe_int(f.get(f"processor_{i}_cores"))
            if name or cores is not None:
                processors.append({"name": name or None, "cores": cores})

        # GPU JSON
        has_gpu = (f.get("has_gpu") or "no") == "yes"
        gpus = []
        if has_gpu:
            gpu_count = int(f.get("gpu_count") or 1)
            for i in range(1, gpu_count + 1):
                gname = (f.get(f"gpu_{i}_name") or "").strip()
                vram = safe_int(f.get(f"gpu_{i}_vram"))
                if gname or vram is not None:
                    gpus.append({"name": gname or None, "vram": vram})

        # Department code
        po_token = po_date_raw.replace("-", "") if po_date_raw else "NA"
        indenter_clean = indenter_full.replace("Dr. ", "").replace("Prof. ", "")
        indenter_first = indenter_clean.split()[0] if indenter_clean else "Unknown"
        dep_base = f"CSE/{po_token}/{model}/{manufacturer}/{indenter_first}/{serial}"
        department_code = dep_base
        suffix = 1
        while WorkstationAsset.query.filter_by(department_code=department_code).first():
            suffix += 1
            department_code = f"{dep_base}-{suffix}"

        # PO Invoice file upload
        po_file = request.files.get("po_invoice")
        po_filename = None
        if po_file and po_file.filename:
            if not allowed_file(po_file.filename):
                flash("Uploaded file type not allowed. Allowed: pdf, jpg, jpeg, png", "danger")
                return render_template("asset_form.html", asset=None,
                                       faculty_list=get_faculty_list(),
                                       staff_list=get_staff_list())
            filename = secure_filename(po_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{serial}_{timestamp}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                po_file.save(save_path)
                po_filename = filename
            except Exception as e:
                flash(f"Error saving file: {e}", "danger")
                return render_template("asset_form.html", asset=None,
                                       faculty_list=get_faculty_list(),
                                       staff_list=get_staff_list())

        # Build asset
        asset = WorkstationAsset(
            manufacturer=manufacturer,
            otherManufacturer=otherManufacturer or None,
            model=model,
            serial=serial,
            os=(f.get("os") or None),
            otherOs=(f.get("otherOs") or None),
            mac_address=(f.get("mac_address") or None),

            # RAM & storage
            ram=ram,
            otherRam=otherRam,
            ram_size_gb=ram_size_gb,
            storage_type1=storage_type1,
            storage_capacity1=storage_capacity1,
            storage_type2=storage_type2,
            storage_capacity2=storage_capacity2,

            # Procurement / fund
            po_number=(f.get("po_number") or None),
            po_date=po_date,
            source_of_fund=(f.get("source_of_fund") or None),

            # Vendor
            vendor_company=(f.get("vendor_company") or None),
            vendor_contact_person=(f.get("vendor_contact_person") or None),
            vendor_mobile=(f.get("vendor_mobile") or None),
            warranty_start=warranty_start,
            warranty_expiry=warranty_expiry,
            po_date_raw=po_date,
            # Lifecycle
            status=status,
            location=location,
            indenter=indenter_full,
            department_code=department_code,

            # Attachments
            po_invoice_filename=po_filename,
        )

        # Save processors / GPUs JSON
        try:
            asset.set_processors(processors if processors else None)
            asset.set_gpus(gpus if gpus else None)
        except Exception:
            asset.processors = json.dumps(processors) if processors else None
            asset.gpus = json.dumps(gpus) if gpus else None

        # Commit
        try:
            db.session.add(asset)
            db.session.commit()
            flash(f"Asset added successfully — Department Code: {department_code}", "success")
            return redirect(url_for("asset_new"))
        except Exception as e:
            db.session.rollback()
            if po_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], po_filename))
                except Exception:
                    pass
            flash(f"Error saving asset: {e}", "danger")
            return render_template("asset_form.html", asset=None,
                                   faculty_list=get_faculty_list(),
                                   staff_list=get_staff_list())

    # GET
    return render_template("asset_form.html",
                           asset=None,
                           faculty_list=get_faculty_list(),
                           staff_list=get_staff_list())



# Download uploaded PO/Invoice file
@app.route('/assets/po/<path:filename>')
def download_po_invoice(filename):
    # safe direct send from configured folder
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)



@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
def asset_edit(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)

    if request.method == "POST":
        f = request.form

        # Required fields
        manufacturer = (f.get("manufacturer") or "").strip()
        otherManufacturer = (f.get("otherManufacturer") or "").strip()
        model = (f.get("model") or "").strip()
        location = (f.get("location") or "").strip()
        indenter_full = (f.get("indenter") or "").strip()
        serial_new = (f.get("serial") or "").strip()
        status = (f.get("status") or "Available").strip()

        if not serial_new:
            flash("Serial number is required.", "danger")
            return render_template("asset_form.html",
                asset=asset,
                faculty_list=get_faculty_list(),
                staff_list=get_staff_list()
            )

        # Serial uniqueness check (only if changed)
        if serial_new != asset.serial:
            if WorkstationAsset.query.filter_by(serial=serial_new).first():
                flash("Serial already exists. Enter a unique serial number.", "danger")
                return render_template("asset_form.html",
                    asset=asset,
                    faculty_list=get_faculty_list(),
                    staff_list=get_staff_list()
                )

        # Date parsing
        po_date_raw = f.get("po_date") or ""
        po_date = parse_date_safe(po_date_raw)
        if po_date_raw and not po_date:
            flash("PO date invalid.", "danger")
            return render_template("asset_form.html",
                asset=asset, faculty_list=get_faculty_list(), staff_list=get_staff_list())

        warranty_start = parse_date_safe(f.get("warranty_start"))
        warranty_expiry = parse_date_safe(f.get("warranty_expiry"))
        if warranty_start and warranty_expiry and warranty_expiry < warranty_start:
            flash("Warranty expiry must be on or after warranty start.", "danger")
            return render_template("asset_form.html",
                asset=asset, faculty_list=get_faculty_list(), staff_list=get_staff_list())

        # Processor parsing
        processor_count = int(f.get("processor_count") or 0)
        processors = []
        for i in range(1, processor_count + 1):
            name = (f.get(f"processor_{i}_name") or "").strip()
            cores = safe_int(f.get(f"processor_{i}_cores"))
            if name or cores is not None:
                processors.append({"name": name or None, "cores": cores})

        # GPU parsing
        has_gpu = (f.get("has_gpu") or "no") == "yes"
        gpus = []
        if has_gpu:
            gpu_count = int(f.get("gpu_count") or 1)
            for i in range(1, gpu_count + 1):
                gname = (f.get(f"gpu_{i}_name") or "").strip()
                vram = safe_int(f.get(f"gpu_{i}_vram"))
                if gname or vram is not None:
                    gpus.append({"name": gname or None, "vram": vram})

        # Detect department_code change conditions
        department_changed = (
            serial_new != asset.serial or
            manufacturer != asset.manufacturer or
            model != asset.model or
            indenter_full != asset.indenter or
            po_date != asset.po_date
        )

        if department_changed:
            po_token = po_date_raw.replace("-", "") if po_date_raw else "NA"
            indenter_clean = indenter_full.replace("Dr. ", "").replace("Prof. ", "")
            indenter_first = indenter_clean.split()[0] if indenter_clean else "Unknown"
            dep_base = f"CSE/{po_token}/{model}/{manufacturer}/{indenter_first}/{serial_new}"

            department_code = dep_base
            suffix = 1
            while WorkstationAsset.query.filter_by(department_code=department_code).first():
                suffix += 1
                department_code = f"{dep_base}-{suffix}"
        else:
            department_code = asset.department_code

        # PO Invoice file upload
        po_file = request.files.get("po_invoice")
        if po_file and po_file.filename:
            if not allowed_file(po_file.filename):
                flash("Invalid file type.", "danger")
                return render_template("asset_form.html", asset=asset,
                                       faculty_list=get_faculty_list(),
                                       staff_list=get_staff_list())

            filename = secure_filename(po_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{serial_new}_{timestamp}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            po_file.save(save_path)
            asset.po_invoice_filename = filename  # update file

        # Update asset fields
        # Update asset fields
        asset.manufacturer = manufacturer
        asset.otherManufacturer = otherManufacturer or None
        asset.model = model
        asset.serial = serial_new
        asset.status = status
        asset.location = location
        asset.indenter = indenter_full
        asset.po_number = f.get("po_number") or None
        asset.po_date = po_date
        asset.warranty_start = warranty_start
        asset.warranty_expiry = warranty_expiry
        asset.department_code = department_code

        # NEW / ensure these are present:
        asset.os = f.get("os") or None
        asset.otherOs = f.get("otherOs") or None
        asset.source_of_fund = f.get("source_of_fund") or None

        asset.vendor_company = f.get("vendor_company") or None
        asset.vendor_contact_person = f.get("vendor_contact_person") or None
        asset.vendor_mobile = f.get("vendor_mobile") or None
        asset.mac_address = f.get("mac_address") or None

        # RAM fields
        asset.ram = f.get("ram") or None
        asset.otherRam = f.get("otherRam") or None
        asset.ram_size_gb = safe_int(f.get("ram_size_gb"))

        # Storage
        asset.storage_type1 = f.get("storage_type1") or None
        asset.storage_capacity1 = safe_int(f.get("storage_capacity1"))
        asset.storage_type2 = f.get("storage_type2") or None
        asset.storage_capacity2 = safe_int(f.get("storage_capacity2"))

        # Save processors & GPUs
        try:
            asset.set_processors(processors if processors else None)
            asset.set_gpus(gpus if gpus else None)
        except:
            asset.processors = json.dumps(processors) if processors else None
            asset.gpus = json.dumps(gpus) if gpus else None

        # Commit update
        try:
            db.session.commit()
            flash("Asset updated successfully.", "success")
            return redirect(url_for("asset_edit", asset_id=asset.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating asset: {e}", "danger")

    # GET request
    return render_template("asset_form.html",
                           asset=asset,
                           faculty_list=get_faculty_list(),
                           staff_list=get_staff_list())


# @app.route("/assets/<int:asset_id>/retire", methods=["POST"])
# def asset_retire(asset_id):
#     a = WorkstationAsset.query.get_or_404(asset_id)
#     if a.status == "Issued":
#         flash("Cannot retire an assigned asset. Return it first.", "warning")
#     elif a.status == "Retired":
#         flash("Asset is already retired.", "info")
#     else:
#         a.status = "Retired"
#         db.session.commit()
#         flash("Asset retired.", "success")
#     return redirect(url_for("assets_list"))


# @app.route("/assets/<int:asset_id>/unretire", methods=["POST"])
# def asset_unretire(asset_id):
#     a = WorkstationAsset.query.get_or_404(asset_id)
#     if a.status == "Retired":
#         a.status = "Available"
#         db.session.commit()
#         flash("Asset un-retired and now Available.", "success")
#     else:
#         flash("Asset is not retired.", "info")
#     return redirect(url_for("assets_list"))


# @app.route("/assets/<int:asset_id>/delete", methods=["POST"])
# def asset_delete(asset_id):
#     a = WorkstationAsset.query.get_or_404(asset_id)
#     if a.assignments and len(a.assignments) > 0:
#         flash("Cannot delete: this asset has assignment history. Consider retire.", "warning")
#         return redirect(url_for("assets_list"))
#     try:
#         db.session.delete(a)
#         db.session.commit()
#         flash("Asset deleted.", "success")
#     except Exception as e:
#         db.session.rollback()
#         flash(f"Error deleting asset: {e}", "danger")
#     return redirect(url_for("assets_list"))

from flask import redirect, url_for, flash, abort
from flask_login import login_required, current_user
import os

# Make sure app and WorkstationAsset, db are already imported above.


def _ensure_can_manage_assets():
    """Block students or unauthorized users from mutating assets."""
    # Adjust this condition if you have different role logic
    if not current_user.is_authenticated:
        abort(401)
    if getattr(current_user, "role", None) == "student":
        flash("You do not have permission to modify assets.", "danger")
        abort(403)

def log_status_change(asset, new_status, reason=None):
    from models import AssetStatusLog  # or adjust import based on your structure

    log = AssetStatusLog(
        asset_id=asset.id,
        old_status=asset.status,
        new_status=new_status,
        reason=reason,
        changed_by=getattr(current_user, "email", None) if hasattr(current_user, "is_authenticated") and current_user.is_authenticated else None,
    )
    asset.status = new_status
    db.session.add(log)

@app.route("/assets/<int:asset_id>/retire", methods=["POST"])
@login_required
def asset_retire(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)
    reason = (request.form.get("reason") or "").strip()

    if not reason:
        flash("Reason for retiring the asset is required.", "danger")
        return redirect(url_for("assets_list"))

    if asset.status == "Issued":
        flash("Cannot retire an assigned asset. Return it first.", "warning")
        return redirect(url_for("assets_list"))
    if asset.status == "Retired":
        flash("Asset is already retired.", "info")
        return redirect(url_for("assets_list"))
    if asset.status == "Scrapped":
        flash("Scrapped asset cannot be retired.", "warning")
        return redirect(url_for("assets_list"))

    try:
        log_status_change(asset, "Retired", reason)
        db.session.commit()
        flash("Asset retired successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error retiring asset: {e}", "danger")

    return redirect(url_for("assets_list"))


@app.route("/assets/<int:asset_id>/unretire", methods=["POST"])
@login_required
def asset_unretire(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)

    if asset.status != "Retired":
        flash("Only retired assets can be un-retired.", "info")
        return redirect(url_for("assets_list"))

    try:
        log_status_change(asset, "Available", "Un-retired (made Available again)")
        db.session.commit()
        flash("Asset un-retired and now Available.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error un-retiring asset: {e}", "danger")

    return redirect(url_for("assets_list"))


@app.route("/assets/<int:asset_id>/scrap", methods=["POST"])
@login_required
def asset_scrap(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)
    reason = (request.form.get("reason") or "").strip()

    if not reason:
        flash("Reason for scrapping the asset is required.", "danger")
        return redirect(url_for("assets_list"))

    if asset.status == "Issued":
        flash("Cannot scrap an assigned asset. Return it first.", "warning")
        return redirect(url_for("assets_list"))
    if asset.status == "Scrapped":
        flash("Asset is already scrapped.", "info")
        return redirect(url_for("assets_list"))

    try:
        log_status_change(asset, "Scrapped", reason)
        db.session.commit()
        flash("Asset marked as Scrapped.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error scrapping asset: {e}", "danger")

    return redirect(url_for("assets_list"))


@app.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def asset_delete(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)

    # Safety checks
    if asset.assignments and len(asset.assignments) > 0:
        flash("Cannot delete: this asset has assignment history. Consider retire/scrap instead.", "warning")
        return redirect(url_for("assets_list"))

    if asset.status in ("Issued", "Scrapped"):
        flash("Cannot delete assets that are Issued or Scrapped.", "warning")
        return redirect(url_for("assets_list"))

    try:
        db.session.delete(asset)
        db.session.commit()
        flash("Asset deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting asset: {e}", "danger")

    return redirect(url_for("assets_list"))

@app.route("/assets/<int:asset_id>/history")
@login_required
def machines_history(asset_id):
    asset = WorkstationAsset.query.get_or_404(asset_id)

    # Optional: restrict students
    # if current_user.role == "student":
    #     flash("Access denied.", "danger")
    #     return redirect(url_for("assets_list"))

    # latest first
    logs = (
        AssetStatusLog.query
        .filter_by(asset_id=asset.id)
        .order_by(AssetStatusLog.changed_at.desc())
        .all()
    )

    return render_template(
        "machines_history.html",
        asset=asset,
        logs=logs
    )

# =========================
# Assign / Return
# =========================

# @app.route("/assignments")
# def assignments_list():
#     q = (WorkstationAssignment.query
#          .options(joinedload(WorkstationAssignment.asset))
#          .filter(WorkstationAssignment.is_active == True))
#     roll = request.args.get("roll", "").strip()
#     serial = request.args.get("serial", "").strip()
#     if roll:
#         q = q.filter(WorkstationAssignment.student_roll == roll)
#     if serial:
#         q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))
#     assignments = q.order_by(WorkstationAssignment.id.desc()).all()
#     return render_template("assignments_list.html", assignments=assignments, roll=roll, serial=serial)

###end ofcode ###

# @app.route("/assignments/new", methods=["GET", "POST"])
# def assignment_new():
#     # --- Filters ---
#     location = request.args.get("location", "")
#     indenter = request.args.get("indenter", "")
#     prefill_roll = request.args.get("student_roll", "").strip()
#     prefill_lab = request.args.get("lab", "").strip()

#     q = WorkstationAsset.query.filter_by(status="Available")
#     if location:
#         q = q.filter(WorkstationAsset.location == location)
#     if indenter:
#         q = q.filter(WorkstationAsset.indenter == indenter)
#     Available_assets = q.order_by(WorkstationAsset.id.desc()).all()

#     locations = [l[0] for l in db.session.query(WorkstationAsset.location).distinct().all() if l[0]]
#     indenters = [i[0] for i in db.session.query(WorkstationAsset.indenter).distinct().all() if i[0]]

#     if request.method == "POST":
#         f = request.form
#         roll = (f.get("student_roll") or "").strip()
#         asset_id = f.get("workstation_id")
#         issue_date = f.get("issue_date")
#         till = f.get("system_required_till")
#         remarks = f.get("remarks") or None

#         # Validation
#         if not roll or not asset_id or not issue_date or not till:
#             flash("Roll, asset, issue date and required till are mandatory.", "warning")
#             return render_template(
#                 "assignment_form.html",
#                 assets=Available_assets,
#                 locations=locations,
#                 indenters=indenters,
#                 location=location,
#                 indenter=indenter,
#                 prefill_roll=prefill_roll,
#                 prefill_lab=prefill_lab
#             )

#         student = Student.query.filter_by(roll=roll).first()
#         if not student:
#             flash("Student not found. Register student first.", "warning")
#             return render_template(
#                 "assignment_form.html",
#                 assets=Available_assets,
#                 locations=locations,
#                 indenters=indenters,
#                 location=location,
#                 indenter=indenter,
#                 prefill_roll=prefill_roll,
#                 prefill_lab=prefill_lab
#             )

#         asset = WorkstationAsset.query.get(asset_id)
#         if not asset or asset.status != "Available":
#             flash("Selected asset is not available for assignment.", "warning")
#             return render_template(
#                 "assignment_form.html",
#                 assets=Available_assets,
#                 locations=locations,
#                 indenters=indenters,
#                 location=location,
#                 indenter=indenter,
#                 prefill_roll=prefill_roll,
#                 prefill_lab=prefill_lab
#             )

#         # Create assignment
#         assign = WorkstationAssignment(
#             workstation_id=asset.id,
#             student_roll=roll,
#             issue_date=issue_date,
#             system_required_till=till,
#             remarks=remarks,
#             is_active=True
#         )
#         try:
#             db.session.add(assign)
#             asset.status = "Issued"
#             student = Student.query.filter_by(roll=roll).first()
#             if student and student.cubicle and student.cubicle.room_lab:
#                asset.location = student.cubicle.room_lab.name
#             db.session.commit()
#             flash("Workstation assigned.", "success")

#             # ---------- Send Email ----------
#             # faculty_incharge = student.faculty or "Not Assigned"
#             # staff_incharge = asset.indenter or "Not Assigned"
#             student = Student.query.filter_by(roll=assign.student_roll).first()
#             if student:
#                 faculty_incharge = student.faculty or "Not Assigned"
#                 staff_incharge = (
#                     student.cubicle.room_lab.staff_incharge
#                     if student.cubicle and student.cubicle.room_lab
#                     else "Not Assigned"
#                 )
#             email_subject = f"Workstation Assigned to {roll}"
#             email_body = f"""
# <html>
# <body style="font-family:Arial,sans-serif; line-height:1.5; color:#333;">
# <h2>Hello {student.name},</h2>
# <p>A workstation has been assigned to you. Details are below:</p>
# <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
# <tr><th>Field</th><th>Value</th></tr>
# <tr><td>Roll Number</td><td>{student.roll}</td></tr>
# <tr><td>Name</td><td>{student.name}</td></tr>
# <tr><td>Workstation</td><td>{asset.manufacturer} {asset.model} (Serial: {asset.serial})</td></tr>
# <tr><td>Location</td><td>{asset.location}</td></tr>
# <tr><td>Issue Date</td><td>{issue_date}</td></tr>
# <tr><td>Required Till</td><td>{till}</td></tr>
# <tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
# <tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
# <tr><td>Remarks</td><td>{remarks or 'None'}</td></tr>
# </table>
# <p>Please contact your faculty or staff incharge for any questions.</p>
# <p>Regards,<br>CSE Lab Admin</p>
# </body>
# </html>
# """
#             msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
#             threading.Thread(target=send_async_email, args=[app, msg]).start()

#             return redirect(url_for("assignments_list"))

#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error assigning workstation: {e}", "danger")

#     return render_template(
#         "assignment_form.html",
#         assets=Available_assets,
#         locations=locations,
#         indenters=indenters,
#         location=location,
#         indenter=indenter,
#         prefill_roll=prefill_roll,
#         prefill_lab=prefill_lab
#     )
###end of code1###
# @app.route("/assignments")
# def assignments_list():
#     q = (WorkstationAssignment.query
#          .options(joinedload(WorkstationAssignment.asset))
#          .filter(WorkstationAssignment.is_active == True))

#     owner_filter = request.args.get("owner", "").strip()
#     serial = request.args.get("serial", "").strip()
#     context_owner_type = request.args.get("context_owner_type", "").strip() or None

#     # Backward compatible: old ?roll=... still works
#     roll = request.args.get("roll", "").strip()
#     if roll and not owner_filter:
#         owner_filter = roll
#         context_owner_type = "student"

#     if owner_filter:
#         if context_owner_type == "faculty":
#             q = q.join(WorkstationAssignment.faculty_owner).filter(
#                 (Faculty.faculty_id.ilike(f"%{owner_filter}%")) | (Faculty.name.ilike(f"%{owner_filter}%"))
#             )
#         elif context_owner_type == "staff":
#             q = q.join(WorkstationAssignment.staff_owner).filter(
#                 (Staff.staff_id.ilike(f"%{owner_filter}%")) | (Staff.name.ilike(f"%{owner_filter}%"))
#             )
#         else:
#             # student
#             q = q.filter(WorkstationAssignment.student_roll == owner_filter)

#     if serial:
#         q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))

#     assignments = q.order_by(WorkstationAssignment.id.desc()).all()

#     # owner_param/back_url are mainly used for role-specific routes (below).
#     return render_template(
#         "assignments_list.html",
#         assignments=assignments,
#         context_owner_type=context_owner_type,
#         owner_filter=owner_filter or roll,
#         serial=serial,
#         owner_param=None,
#         back_url=None,
#     )
# =========================
# Workstation Assign / Return (generic list)
# =========================

from sqlalchemy.orm import joinedload

def assignments_list_generic(owner_type=None, owner_key=None):
    """
    Generic active assignments list.

    owner_type:
        - None      -> global list (admin)
        - 'student' -> owner_key is roll
        - 'staff'   -> owner_key is staff.id
        - 'faculty' -> owner_key is faculty.id
    """
    from models import Student, Staff, Faculty, WorkstationAssignment, WorkstationAsset

    q = (WorkstationAssignment.query
         .options(joinedload(WorkstationAssignment.asset))
         .filter(WorkstationAssignment.is_active == True))

    # Filters from query string (still support 'roll' + 'serial')
    roll_filter = (request.args.get("roll") or "").strip()
    serial = (request.args.get("serial") or "").strip()

    owner = None   # person object (Student/Staff/Faculty) for context
    effective_roll = None  # what we pass back for student views

    # ------ Owner scoping ------
    if owner_type == "student":
        # owner_key is student's roll (from /assignments?roll=... OR allotment)
        if owner_key:
            owner = Student.query.filter_by(roll=owner_key).first_or_404()
            effective_roll = owner.roll
            q = q.filter(WorkstationAssignment.student_roll == owner.roll)
        else:
            # fallback: use roll_filter only
            if roll_filter:
                effective_roll = roll_filter
                q = q.filter(WorkstationAssignment.student_roll == roll_filter)

    elif owner_type == "staff":
        owner = Staff.query.get_or_404(owner_key)
        q = q.filter(WorkstationAssignment.staff_id == owner.id)

    elif owner_type == "faculty":
        owner = Faculty.query.get_or_404(owner_key)
        q = q.filter(WorkstationAssignment.faculty_id == owner.id)

    else:
        # Global list (admin view): optional filter by student roll
        if roll_filter:
            q = q.filter(WorkstationAssignment.student_roll == roll_filter)

    # ------ Serial filter ------
    if serial:
        q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))

    assignments = q.order_by(WorkstationAssignment.id.desc()).all()

    return render_template(
        "assignments_list.html",
        assignments=assignments,
        owner_type=owner_type,
        owner=owner,
        roll=effective_roll if owner_type in ("student", None) else None,
        serial=serial,
    )


# @app.route("/assignments")
# def assignments_list():
#     """
#     - /assignments              -> all active assignments (admin/global)
#     - /assignments?roll=CSxx    -> active assignments for that student
#     """
#     roll = (request.args.get("roll") or "").strip()
#     if roll:
#         # student-specific view
#         return assignments_list_generic("student", roll)
#     # global view
#     return assignments_list_generic(None, None)







@app.route("/faculty/<int:fid>/assignments")
@login_required
def faculty_assignments(fid):
    faculty = Faculty.query.get_or_404(fid)
    serial = request.args.get("serial", "").strip()

    q = (WorkstationAssignment.query
         .options(joinedload(WorkstationAssignment.asset))
         .filter(WorkstationAssignment.is_active == True,
                 WorkstationAssignment.faculty_id == fid))

    if serial:
        q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))

    assignments = q.order_by(WorkstationAssignment.id.desc()).all()

    return render_template(
        "assignments_list.html",
        assignments=assignments,
        # 🔴 these two are what the template uses
        owner_type="faculty",
        owner=faculty,
        # these are still used by filters / display
        roll=None,
        serial=serial,
    )

@app.route("/staff/<int:sid>/assignments")
@login_required
def staff_assignments(sid):
    staff = Staff.query.get_or_404(sid)
    serial = request.args.get("serial", "").strip()

    q = (WorkstationAssignment.query
         .options(joinedload(WorkstationAssignment.asset))
         .filter(WorkstationAssignment.is_active == True,
                 WorkstationAssignment.staff_id == sid))

    if serial:
        q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))

    assignments = q.order_by(WorkstationAssignment.id.desc()).all()

    return render_template(
        "assignments_list.html",
        assignments=assignments,
        owner_type="staff",   # 🔴 used by template
        owner=staff,          # 🔴 used by template
        roll=None,
        serial=serial,
    )



@app.route("/assignments/new", methods=["GET", "POST"])
def assignment_new():
    # --- Filters ---
    location = request.args.get("location", "")
    indenter = request.args.get("indenter", "")

    prefill_roll = request.args.get("student_roll", "").strip() or None
    prefill_faculty_id = request.args.get("faculty_id", "").strip() or None
    prefill_staff_id = request.args.get("staff_id", "").strip() or None

    owner_type = request.args.get("owner_type", "").strip().lower()
    if not owner_type:
        # backward compatible: if student_roll present and no owner_type, assume student
        owner_type = "student" if prefill_roll else "student"

    # Query available assets
    q = WorkstationAsset.query.filter_by(status="Available")
    if location:
        q = q.filter(WorkstationAsset.location == location)
    if indenter:
        q = q.filter(WorkstationAsset.indenter == indenter)
    Available_assets = q.order_by(WorkstationAsset.id.desc()).all()

    locations = [l[0] for l in db.session.query(WorkstationAsset.location).distinct().all() if l[0]]
    indenters = [i[0] for i in db.session.query(WorkstationAsset.indenter).distinct().all() if i[0]]

    # Prefill objects
    prefill_faculty = Faculty.query.get(prefill_faculty_id) if prefill_faculty_id else None
    prefill_staff = Staff.query.get(prefill_staff_id) if prefill_staff_id else None

    if request.method == "POST":
        f = request.form
        owner_type = (f.get("owner_type") or "student").lower()
        roll = (f.get("student_roll") or "").strip()
        faculty_id = (f.get("faculty_id") or "").strip()
        staff_id = (f.get("staff_id") or "").strip()

        asset_id = f.get("workstation_id")
        issue_date = f.get("issue_date")
        till = f.get("system_required_till")
        remarks = f.get("remarks") or None

        # Basic validation
        if not asset_id or not issue_date or not till:
            flash("Asset, issue date and required till are mandatory.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type=owner_type,
                prefill_roll=prefill_roll,
                prefill_faculty=prefill_faculty,
                prefill_staff=prefill_staff,
            )

        # Determine owner and validate
        student = faculty = staff = None
        ws_kwargs = {}

        if owner_type == "faculty":
            if not faculty_id:
                flash("Faculty ID missing for faculty assignment.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type=owner_type,
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            faculty = Faculty.query.get(faculty_id)
            if not faculty:
                flash("Faculty not found.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type=owner_type,
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            ws_kwargs["faculty_id"] = faculty.id

        elif owner_type == "staff":
            if not staff_id:
                flash("Staff ID missing for staff assignment.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type=owner_type,
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            staff = Staff.query.get(staff_id)
            if not staff:
                flash("Staff not found.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type=owner_type,
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            ws_kwargs["staff_id"] = staff.id

        else:  # student (default)
            if not roll:
                flash("Student roll is mandatory for student assignment.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type="student",
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            student = Student.query.filter_by(roll=roll).first()
            if not student:
                flash("Student not found. Register student first.", "warning")
                return render_template("assignment_form.html", assets=Available_assets,
                                       locations=locations, indenters=indenters,
                                       location=location, indenter=indenter,
                                       owner_type="student",
                                       prefill_roll=prefill_roll,
                                       prefill_faculty=prefill_faculty,
                                       prefill_staff=prefill_staff)
            ws_kwargs["student_roll"] = student.roll

        asset = WorkstationAsset.query.get(asset_id)
        if not asset or asset.status != "Available":
            flash("Selected asset is not available for assignment.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type=owner_type,
                prefill_roll=prefill_roll,
                prefill_faculty=prefill_faculty,
                prefill_staff=prefill_staff,
            )

        # Create assignment
        assign = WorkstationAssignment(
            workstation_id=asset.id,
            issue_date=issue_date,
            system_required_till=till,
            remarks=remarks,
            is_active=True,
            **ws_kwargs
        )
        try:
            db.session.add(assign)
            asset.status = "Issued"
            db.session.commit()
            flash("Workstation assigned.", "success")

            # Email only for student case (for now)
            if student:
                faculty_incharge = student.faculty or "Not Assigned"
                staff_incharge = (
                    student.cubicle.room_lab.staff_incharge
                    if student.cubicle and student.cubicle.room_lab
                    else "Not Assigned"
                )
                email_subject = f"Workstation Assigned to {student.roll}"
                email_body = f"""<html>...same HTML as before...</html>"""
                msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
                threading.Thread(target=send_async_email, args=[app, msg]).start()

            return redirect(url_for("assignments_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error assigning workstation: {e}", "danger")

    return render_template(
        "assignment_form.html",
        assets=Available_assets,
        locations=locations,
        indenters=indenters,
        location=location,
        indenter=indenter,
        owner_type=owner_type,
        prefill_roll=prefill_roll,
        prefill_faculty=prefill_faculty,
        prefill_staff=prefill_staff,
    )

# =========================
# Workstation Assign / Return (generic list)
# =========================

from sqlalchemy.orm import joinedload

def assignments_list_generic(owner_type=None, owner_key=None):
    """
    Generic active assignments list.

    owner_type:
        - None      -> global list (admin)
        - 'student' -> owner_key is roll
        - 'staff'   -> owner_key is staff.id
        - 'faculty' -> owner_key is faculty.id
    """
    from models import Student, Staff, Faculty, WorkstationAssignment, WorkstationAsset

    q = (WorkstationAssignment.query
         .options(joinedload(WorkstationAssignment.asset))
         .filter(WorkstationAssignment.is_active == True))

    # Filters from query string (still support 'roll' + 'serial')
    roll_filter = (request.args.get("roll") or "").strip()
    serial = (request.args.get("serial") or "").strip()

    owner = None   # person object (Student/Staff/Faculty) for context
    effective_roll = None  # what we pass back for student views

    # ------ Owner scoping ------
    if owner_type == "student":
        # owner_key is student's roll (from /assignments?roll=... OR allotment)
        if owner_key:
            owner = Student.query.filter_by(roll=owner_key).first_or_404()
            effective_roll = owner.roll
            q = q.filter(WorkstationAssignment.student_roll == owner.roll)
        else:
            # fallback: use roll_filter only
            if roll_filter:
                effective_roll = roll_filter
                q = q.filter(WorkstationAssignment.student_roll == roll_filter)

    elif owner_type == "staff":
        owner = Staff.query.get_or_404(owner_key)
        q = q.filter(WorkstationAssignment.staff_id == owner.id)

    elif owner_type == "faculty":
        owner = Faculty.query.get_or_404(owner_key)
        q = q.filter(WorkstationAssignment.faculty_id == owner.id)

    else:
        # Global list (admin view): optional filter by student roll
        if roll_filter:
            q = q.filter(WorkstationAssignment.student_roll == roll_filter)

    # ------ Serial filter ------
    if serial:
        q = q.join(WorkstationAsset).filter(WorkstationAsset.serial.ilike(f"%{serial}%"))

    assignments = q.order_by(WorkstationAssignment.id.desc()).all()

    return render_template(
        "assignments_list.html",
        assignments=assignments,
        owner_type=owner_type,
        owner=owner,
        roll=effective_roll if owner_type in ("student", None) else None,
        serial=serial,
    )


@app.route("/assignments")
def assignments_list():
    """
    - /assignments              -> all active assignments (admin/global)
    - /assignments?roll=CSxx    -> active assignments for that student
    """
    roll = (request.args.get("roll") or "").strip()
    if roll:
        # student-specific view
        return assignments_list_generic("student", roll)
    # global view
    return assignments_list_generic(None, None)

# @app.route("/assignments/<int:assign_id>/return", methods=["POST"])
# def assignment_return(assign_id):
#     assign = WorkstationAssignment.query.options(joinedload(WorkstationAssignment.asset)).get_or_404(assign_id)

#     if not assign.is_active:
#         flash("This assignment is already returned.", "info")
#         return redirect(url_for("assignments_list"))

#     try:
#         assign.is_active = False
#         assign.end_date = date.today().isoformat()
#         if assign.asset and assign.asset.status == "Issued":
#             assign.asset.status = "Available"
#         db.session.commit()
#         flash("Workstation returned.", "success")

#         # ---------- Send Email ----------
#         # student = Student.query.filter_by(roll=assign.student_roll).first()
#         # if student:
#         #     faculty_incharge = student.faculty or "Not Assigned"
#         #     # staff_incharge = assign.asset.indenter if assign.asset else "Not Assigned"
#         #     staff_incharge = assign.asset.indenter or "Not Assigned"
#         student = Student.query.filter_by(roll=assign.student_roll).first()
#         if student:
#             faculty_incharge = student.faculty or "Not Assigned"
#             staff_incharge = (
#                 student.cubicle.room_lab.staff_incharge
#                 if student.cubicle and student.cubicle.room_lab
#                 else "Not Assigned"
#             )





#             email_subject = f"Workstation Returned: {assign.asset.manufacturer} {assign.asset.model}" if assign.asset else "Workstation Returned"
#             email_body = f"""
# <html>
# <body style="font-family:Arial,sans-serif; line-height:1.5; color:#333;">
# <h2>Hello {student.name},</h2>
# <p>Your assigned workstation has been returned. Details:</p>
# <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
# <tr><th>Field</th><th>Value</th></tr>
# <tr><td>Roll Number</td><td>{student.roll}</td></tr>
# <tr><td>Name</td><td>{student.name}</td></tr>
# <tr><td>Workstation</td><td>{assign.asset.manufacturer if assign.asset else '-'} {assign.asset.model if assign.asset else '-'} (Serial: {assign.asset.serial if assign.asset else '-'})</td></tr>
# <tr><td>Return Date</td><td>{assign.end_date}</td></tr>
# <tr><td>Faculty In-charge</td><td>{faculty_incharge}</td></tr>
# <tr><td>Staff In-charge</td><td>{staff_incharge}</td></tr>
# </table>
# <p>Thank you for returning the workstation.</p>
# <p>Regards,<br>CSE Lab Admin</p>
# </body>
# </html>
# """
#             msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
#             threading.Thread(target=send_async_email, args=[app, msg]).start()

#     except Exception as e:
#         db.session.rollback()
#         flash(f"Error returning workstation: {e}", "danger")

#     return redirect(url_for("assignments_list"))

###endo of code###
# @app.route("/assignments/<int:assign_id>/return", methods=["POST"])
# def assignment_return(assign_id):
#     assign = WorkstationAssignment.query.options(joinedload(WorkstationAssignment.asset)).get_or_404(assign_id)

#     if not assign.is_active:
#         flash("This assignment is already returned.", "info")
#         return redirect(url_for("assignments_list"))

#     try:
#         assign.is_active = False
#         assign.end_date = date.today().isoformat()
#         if assign.asset and assign.asset.status == "Issued":
#             assign.asset.status = "Available"
#         db.session.commit()
#         flash("Workstation returned.", "success")

#         # Email only for student case
#         if assign.student_roll:
#             student = Student.query.filter_by(roll=assign.student_roll).first()
#             if student:
#                 faculty_incharge = student.faculty or "Not Assigned"
#                 staff_incharge = (
#                     student.cubicle.room_lab.staff_incharge
#                     if student.cubicle and student.cubicle.room_lab
#                     else "Not Assigned"
#                 )
#                 email_subject = f"Workstation Returned: {assign.asset.manufacturer} {assign.asset.model}" if assign.asset else "Workstation Returned"
#                 email_body = f"""<html>...your existing HTML body...</html>"""
#                 msg = Message(subject=email_subject, recipients=[student.email], html=email_body)
#                 threading.Thread(target=send_async_email, args=[app, msg]).start()

#     except Exception as e:
#         db.session.rollback()
#         flash(f"Error returning workstation: {e}", "danger")

#     return redirect(url_for("assignments_list"))



def sync_asset_locations_with_cubicle(roll):
    cubicle = Cubicle.query.filter_by(student_roll=roll).first()
    if not cubicle:
        return  # Nothing to update if cubicle not assigned

    new_location = cubicle.room_lab.name

    # Update Workstations
    active_assignments = WorkstationAssignment.query.filter_by(student_roll=roll, is_active=True).all()
    for assign in active_assignments:
        ws = WorkstationAsset.query.get(assign.workstation_id)
        if ws and ws.location != new_location:
            ws.location = new_location

    # Update IT Equipment
    assigned_items = Equipment.query.filter_by(assigned_to_roll=roll).all()
    for item in assigned_items:
        if item.location != new_location:
            item.location = new_location

    db.session.commit()




from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from models import db, RoomLab, Cubicle, Student  # adjust imports if needed

@app.route("/space_allocation", methods=["GET", "POST"])
@login_required
def space_allocation():
    rooms = RoomLab.query.all()
    roll_prefill = request.args.get("roll", "").strip()

    current_cubicle = None
    if roll_prefill:
        current_cubicle = Cubicle.query.filter_by(student_roll=roll_prefill).first()

    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        cubicle_id = request.form.get("cubicle_id")

        if not roll:
            flash("Roll number is required.", "danger")
            return redirect(url_for("space_allocation"))

        cubicle = Cubicle.query.get(cubicle_id)
        if not cubicle:
            flash("Invalid cubicle selected.", "danger")
            return redirect(url_for("space_allocation", roll=roll))

        if cubicle.student_roll:
            flash(f"Cubicle {cubicle.number} is already allocated.", "danger")
            return redirect(url_for("space_allocation", roll=roll))

        # Release old cubicle if any
        prev_cubicle = Cubicle.query.filter_by(student_roll=roll).first()
        if prev_cubicle:
            prev_cubicle.student_roll = None

                # Assign new cubicle
        cubicle.student_roll = roll
        db.session.commit()

        # ✅ Determine new location from cubicle (ex: CS-108)
        new_location = cubicle.room_lab.name

        # ==============================
        # ✅ UPDATE ASSIGNED WORKSTATIONS
        # ==============================
        active_assignments = WorkstationAssignment.query.filter_by(student_roll=roll, is_active=True).all()
        for assign in active_assignments:
            ws = WorkstationAsset.query.get(assign.workstation_id)
            if ws and ws.location != new_location:
                old_loc = ws.location
                ws.location = new_location

                # Log history
                history_entry = EquipmentHistory(
                    equipment_id=ws.id,
                    assigned_to_roll=roll,
                    assigned_by=current_user.email,
                    status_snapshot=f"{old_loc or 'None'} to {new_location}",
                    timestamp=datetime.utcnow()
                )
                db.session.add(history_entry)

        # ==============================
        # ✅ UPDATE ASSIGNED IT EQUIPMENT
        # ==============================
        assigned_items = Equipment.query.filter_by(assigned_to_roll=roll).all()
        for item in assigned_items:
            if item.location != new_location:
                old_loc = item.location
                item.location = new_location

                # Log history
                history_entry = EquipmentHistory(
                    equipment_id=item.id,
                    assigned_to_roll=roll,
                    assigned_by=current_user.email,
                    status_snapshot=f"[Equipment] Location changed from {old_loc or 'None'} to {new_location}",
                    timestamp=datetime.utcnow()
                )
                db.session.add(history_entry)

        db.session.commit()
        print(f"✅ All workstation + IT equipment updated to location: {new_location}")




        # ============= 📧 EMAIL NOTIFICATION SECTION =============
        student = Student.query.filter_by(roll=roll).first()
        student_name = student.name if student else "Unknown Student"
        student_email = student.email if student and student.email else None
        faculty_incharge = student.faculty if student and student.faculty else "Not Assigned"

        # If you also store faculty email, you can fetch:
        faculty_email = getattr(student, "faculty_email", None)
        cc_list = [faculty_email] if faculty_email else []

        subject = f"Space Allocation Confirmation — {cubicle.room_lab.name}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
         <h1> Dear {student_name},</h1>
         <br>
        <h3>Space Allocation Details</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
          <tr><th align="left">Student Name</th><td>{student_name}</td></tr>
          <tr><th align="left">Email</th><td>{student_email or 'N/A'}</td></tr>
          <tr><th align="left">Roll Number</th><td>{roll}</td></tr>
          <tr><th align="left">Room / Lab</th><td>{cubicle.room_lab.name}</td></tr>
          <tr><th align="left">Cubicle Number</th><td>{cubicle.number}</td></tr>
          <tr><th align="left">Faculty Incharge</th><td>{faculty_incharge}</td></tr>
          <tr><th align="left">Assigned By</th><td>{current_user.email}</td></tr>
          <tr><th align="left">Allocation Date</th><td>{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</td></tr>
        </table>
        <p style="margin-top:20px;">Regards,<br><b>CSE Lab Management System</b></p>
        </body>
        </html>
        """

        if student_email:
            send_notification_email(student_email, subject, body, cc=cc_list)
            print(f"📩 Email sent to {student_email} (CC: {cc_list})")
        else:
            print(f"⚠️ No email found for student roll {roll}")

        flash(f"Space {cubicle.number} allocated to {roll}", "success")
        return redirect(url_for("space_allocation", roll=roll))

    return render_template(
        "space_allocation.html",
        rooms=rooms,
        roll_prefill=roll_prefill,
        current_cubicle=current_cubicle
    )


# ---- Staff space allocation (office) ----
@app.route("/space_allocation/staff/<int:pid>", methods=["GET", "POST"])
@login_required
def space_allocation_staff(pid):
    staff = Staff.query.get_or_404(pid)
    office_rooms = build_office_status()
    current_room = staff.room

    if request.method == "POST":
        new_room = (request.form.get("room_code") or "").strip()

        if not new_room:
            flash("Please select a room.", "danger")
            return redirect(url_for("space_allocation_staff", pid=pid))

        if new_room not in OFFICE_ROOMS:
            flash("Invalid room selected.", "danger")
            return redirect(url_for("space_allocation_staff", pid=pid))

        # ---------- business rules ----------
        if new_room == "CS-103":
            # CS-103: can have multiple staff, but no faculty
            fac_occupant = Faculty.query.filter_by(room=new_room).first()
            if fac_occupant:
                flash(f"Room {new_room} is reserved for staff; faculty already present.", "danger")
                return redirect(url_for("space_allocation_staff", pid=pid))
        else:
            # All other rooms: at most one person (staff or faculty)
            fac_occupant = Faculty.query.filter_by(room=new_room).first()
            other_staff = Staff.query.filter(
                Staff.room == new_room,
                Staff.id != staff.id
            ).first()

            if fac_occupant or other_staff:
                flash(f"Room {new_room} is already assigned to someone.", "danger")
                return redirect(url_for("space_allocation_staff", pid=pid))

        # ---------- assign / reassign ----------
        old_room = staff.room
        staff.room = new_room
        db.session.commit()

        # Optional: update locations of workstations + equipment
        new_location = new_room

        active_assignments = WorkstationAssignment.query.filter_by(
            staff_id=staff.id, is_active=True
        ).all()
        for assign in active_assignments:
            ws = WorkstationAsset.query.get(assign.workstation_id)
            if ws and ws.location != new_location:
                ws.location = new_location

        assigned_items = Equipment.query.filter_by(assigned_to_staff_id=staff.id).all()
        for item in assigned_items:
            if item.location != new_location:
                item.location = new_location

        db.session.commit()

        flash(f"Room {new_room} assigned to {staff.name}.", "success")
        return redirect(url_for("space_allocation_staff", pid=pid))

    return render_template(
        "space_allocation_office.html",
        owner_type="staff",
        person=staff,
        office_rooms=office_rooms,
        current_room=current_room,
    )

    
@app.route("/space/release/staff/<int:pid>", methods=["POST"])
@login_required
def space_release_staff(pid):
    staff = Staff.query.get_or_404(pid)
    old_room = staff.room

    if not old_room:
        flash("This staff member has no room assigned.", "warning")
        return redirect(url_for("space_allocation_staff", pid=pid))

    # Clear the room assignment
    staff.room = None
    db.session.commit()

    flash(f"Released room {old_room} from {staff.name}.", "success")
    return redirect(url_for("space_allocation_staff", pid=pid))



@app.route("/space/release/faculty/<int:pid>", methods=["POST"])
@login_required
def space_release_faculty(pid):
    faculty = Faculty.query.get_or_404(pid)
    old_room = faculty.room
    if not old_room:
        flash("Faculty has no room assigned.", "warning")
        return redirect(url_for("space_allocation_faculty", pid=pid))

    faculty.room = None
    db.session.commit()
    flash(f"Released room {old_room} from {faculty.name}.", "success")
    return redirect(url_for("space_allocation_faculty", pid=pid))


# STAFF
@app.route("/allotment_options/staff/<int:sid>")
@login_required
def allotment_options_staff(sid):
    staff = Staff.query.get_or_404(sid)

    # current room (string) - staff have room not cubicle
    current_room = staff.room if getattr(staff, "room", None) else None

    # workstations assigned to staff (if you have staff_id column)
    ws_active = WorkstationAssignment.query.filter_by(staff_id=sid, is_active=True).order_by(WorkstationAssignment.issue_date.desc()).all()
    ws_history = WorkstationAssignment.query.filter_by(staff_id=sid).order_by(WorkstationAssignment.issue_date.desc()).all()

    # equipment
    equipment_active = Equipment.query.filter_by(assigned_to_staff_id=sid).all()
    equipment_history = EquipmentHistory.query.filter_by(assigned_to_staff_id=sid).order_by(EquipmentHistory.assigned_date.desc()).all()
    for eq in equipment_history:
        eq.equipment_obj = Equipment.query.get(eq.equipment_id)
        eq.staff_incharge = staff.room or '—'

    return render_template(
        "allotment_options.html",
        staff=staff,
        current_room=current_room,
        workstation_active=ws_active,
        workstation_history=ws_history,
        equipment_active=equipment_active,
        equipment_history=equipment_history,
    )

# FACULTY
@app.route("/allotment_options/faculty/<int:fid>")
@login_required
def allotment_options_faculty(fid):
    faculty = Faculty.query.get_or_404(fid)
    current_room = faculty.room if getattr(faculty, "room", None) else None

    ws_active = WorkstationAssignment.query.filter_by(faculty_id=fid, is_active=True).order_by(WorkstationAssignment.issue_date.desc()).all()
    ws_history = WorkstationAssignment.query.filter_by(faculty_id=fid).order_by(WorkstationAssignment.issue_date.desc()).all()

    equipment_active = Equipment.query.filter_by(assigned_to_faculty_id=fid).all()
    equipment_history = EquipmentHistory.query.filter_by(assigned_to_faculty_id=fid).order_by(EquipmentHistory.assigned_date.desc()).all()
    for eq in equipment_history:
        eq.equipment_obj = Equipment.query.get(eq.equipment_id)
        eq.staff_incharge = faculty.room or '—'

    return render_template(
        "allotment_options.html",
        faculty=faculty,
        current_room=current_room,
        workstation_active=ws_active,
        workstation_history=ws_history,
        equipment_active=equipment_active,
        equipment_history=equipment_history,
    )


from models import Staff, Faculty, WorkstationAsset, WorkstationAssignment, Student

@app.route("/staff/assignments/new/<int:pid>", methods=["GET", "POST"])
@login_required
def assignment_new_staff(pid):
    staff = Staff.query.get_or_404(pid)

    # --- Filters ---
    location = request.args.get("location", "")
    indenter = request.args.get("indenter", "")

    q = WorkstationAsset.query.filter_by(status="Available")
    if location:
        q = q.filter(WorkstationAsset.location == location)
    if indenter:
        q = q.filter(WorkstationAsset.indenter == indenter)
    Available_assets = q.order_by(WorkstationAsset.id.desc()).all()

    locations = [l[0] for l in db.session.query(WorkstationAsset.location).distinct().all() if l[0]]
    indenters = [i[0] for i in db.session.query(WorkstationAsset.indenter).distinct().all() if i[0]]

    if request.method == "POST":
        f = request.form
        asset_id = f.get("workstation_id")
        issue_date = f.get("issue_date")
        till = f.get("system_required_till")
        remarks = f.get("remarks") or None

        if not asset_id or not issue_date or not till:
            flash("Asset, issue date and required till are mandatory.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type="staff",
                person=staff,
            )

        asset = WorkstationAsset.query.get(asset_id)
        if not asset or asset.status != "Available":
            flash("Selected asset is not available for assignment.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type="staff",
                person=staff,
            )

        assign = WorkstationAssignment(
            workstation_id=asset.id,
            staff_id=staff.id,
            issue_date=issue_date,
            system_required_till=till,
            remarks=remarks,
            is_active=True,
            assigned_by=getattr(current_user, "email", None),
        )
        try:
            db.session.add(assign)
            asset.status = "Issued"
            db.session.commit()
            flash("Workstation assigned.", "success")
            return redirect(url_for("assignments_list_staff", pid=staff.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error assigning workstation: {e}", "danger")

    return render_template(
        "assignment_form.html",
        assets=Available_assets,
        locations=locations,
        indenters=indenters,
        location=location,
        indenter=indenter,
        owner_type="staff",
        person=staff,
    )


@app.route("/faculty/assignments/new/<int:pid>", methods=["GET", "POST"])
@login_required
def assignment_new_faculty(pid):
    faculty = Faculty.query.get_or_404(pid)

    # --- Filters ---
    location = request.args.get("location", "")
    indenter = request.args.get("indenter", "")

    q = WorkstationAsset.query.filter_by(status="Available")
    if location:
        q = q.filter(WorkstationAsset.location == location)
    if indenter:
        q = q.filter(WorkstationAsset.indenter == indenter)
    Available_assets = q.order_by(WorkstationAsset.id.desc()).all()

    locations = [l[0] for l in db.session.query(WorkstationAsset.location).distinct().all() if l[0]]
    indenters = [i[0] for i in db.session.query(WorkstationAsset.indenter).distinct().all() if i[0]]

    if request.method == "POST":
        f = request.form
        asset_id = f.get("workstation_id")
        issue_date = f.get("issue_date")
        till = f.get("system_required_till")
        remarks = f.get("remarks") or None

        if not asset_id or not issue_date or not till:
            flash("Asset, issue date and required till are mandatory.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type="faculty",
                person=faculty,
            )

        asset = WorkstationAsset.query.get(asset_id)
        if not asset or asset.status != "Available":
            flash("Selected asset is not available for assignment.", "warning")
            return render_template(
                "assignment_form.html",
                assets=Available_assets,
                locations=locations,
                indenters=indenters,
                location=location,
                indenter=indenter,
                owner_type="faculty",
                person=faculty,
            )

        assign = WorkstationAssignment(
            workstation_id=asset.id,
            faculty_id=faculty.id,
            issue_date=issue_date,
            system_required_till=till,
            remarks=remarks,
            is_active=True,
            assigned_by=getattr(current_user, "email", None),
        )
        try:
            db.session.add(assign)
            asset.status = "Issued"
            db.session.commit()
            flash("Workstation assigned.", "success")
            return redirect(url_for("assignments_list_faculty", pid=faculty.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error assigning workstation: {e}", "danger")

    return render_template(
        "assignment_form.html",
        assets=Available_assets,
        locations=locations,
        indenters=indenters,
        location=location,
        indenter=indenter,
        owner_type="faculty",
        person=faculty,
    )


@app.route("/assignments/<int:assign_id>/return", methods=["POST"])
def assignment_return(assign_id):
    assign = WorkstationAssignment.query.options(joinedload(WorkstationAssignment.asset)).get_or_404(assign_id)

    if not assign.is_active:
        flash("This assignment is already returned.", "info")
        return redirect(url_for("assignments_list"))

    try:
        assign.is_active = False
        assign.end_date = date.today().isoformat()
        if assign.asset and assign.asset.status == "Issued":
            assign.asset.status = "Available"
        db.session.commit()
        flash("Workstation returned.", "success")

        # (your email code for student can stay here as-is)

    except Exception as e:
        db.session.rollback()
        flash(f"Error returning workstation: {e}", "danger")

    # 🔁 Redirect back to the appropriate view
    if assign.student_roll:
        return redirect(url_for("assignments_list", roll=assign.student_roll))
    elif assign.staff_id:
        return redirect(url_for("staff_assignments", sid=assign.staff_id))
    elif assign.faculty_id:
        return redirect(url_for("faculty_assignments", fid=assign.faculty_id))
    else:
        return redirect(url_for("assignments_list"))







# @app.route("/staff/equipment/<int:pid>")
# @login_required
# def it_equipment_assign_staff(pid):
#     # If you have a generic view named like it_equipment_assign_generic(role,pid):
#     try:
#         return it_equipment_assign_generic("staff", pid)
#     except NameError:
#         # fallback - show assignments page (or change to whichever is appropriate)
#         return redirect(url_for("staff_assignments", sid=pid))

# @app.route("/faculty/equipment/<int:pid>")
# @login_required
# def it_equipment_assign_faculty(pid):
#     try:
#         return it_equipment_assign_generic("faculty", pid)
#     except NameError:
#         return redirect(url_for("faculty_assignments", fid=pid))


# ---- Faculty space allocation (office) ----
@app.route("/space_allocation/faculty/<int:pid>", methods=["GET", "POST"])
@login_required
def space_allocation_faculty(pid):
    faculty = Faculty.query.get_or_404(pid)
    office_rooms = build_office_status()
    current_room = faculty.room

    if request.method == "POST":
        new_room = (request.form.get("room_code") or "").strip()

        if not new_room:
            flash("Please select a room.", "danger")
            return redirect(url_for("space_allocation_faculty", pid=pid))

        if new_room not in OFFICE_ROOMS:
            flash("Invalid room selected.", "danger")
            return redirect(url_for("space_allocation_faculty", pid=pid))

        # ---------- strict one-to-one ----------
        other_faculty = Faculty.query.filter(
            Faculty.room == new_room,
            Faculty.id != faculty.id
        ).first()
        any_staff = Staff.query.filter_by(room=new_room).first()

        if other_faculty or any_staff:
            flash(f"Room {new_room} is already assigned.", "danger")
            return redirect(url_for("space_allocation_faculty", pid=pid))

        # ---------- assign / reassign ----------
        old_room = faculty.room
        faculty.room = new_room
        db.session.commit()

        new_location = new_room

        active_assignments = WorkstationAssignment.query.filter_by(
            faculty_id=faculty.id, is_active=True
        ).all()
        for assign in active_assignments:
            ws = WorkstationAsset.query.get(assign.workstation_id)
            if ws and ws.location != new_location:
                ws.location = new_location

        assigned_items = Equipment.query.filter_by(assigned_to_faculty_id=faculty.id).all()
        for item in assigned_items:
            if item.location != new_location:
                item.location = new_location

        db.session.commit()

        flash(f"Room {new_room} assigned to {faculty.name}.", "success")
        return redirect(url_for("space_allocation_faculty", pid=pid))

    return render_template(
        "space_allocation_office.html",
        owner_type="faculty",
        person=faculty,
        office_rooms=office_rooms,
        current_room=current_room,
    )



@app.route("/space/release/<int:cubicle_id>", methods=["POST"])
@login_required
def space_release(cubicle_id):
    cubicle = Cubicle.query.get_or_404(cubicle_id)
    roll = cubicle.student_roll

    if not roll:
        flash("No student assigned to this cubicle.", "warning")
        return redirect(url_for("space_allocation"))

    # Fetch student info
    student = Student.query.filter_by(roll=roll).first()
    student_name = student.name if student else "Unknown Student"
    student_email = student.email if student and student.email else None
    faculty_incharge = student.faculty if student and student.faculty else "Not Assigned"

    # If you later store faculty email, you can CC here
    faculty_email = getattr(student, "faculty_email", None)
    cc_list = [faculty_email] if faculty_email else []

    # Release cubicle
    cubicle.student_roll = None
    db.session.commit()

    # Prepare email
    subject = f"Space Released — {cubicle.room_lab.name}"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
    <h1> Dear {student_name},</h1>
    <br>


    <h3>Space Release Notification</h3>
    <p>The following space allocation has been released:</p>

    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
      <tr><th align="left">Student Name</th><td>{student_name}</td></tr>
      <tr><th align="left">Email</th><td>{student_email or 'N/A'}</td></tr>
      <tr><th align="left">Roll Number</th><td>{roll}</td></tr>
      <tr><th align="left">Room / Lab</th><td>{cubicle.room_lab.name}</td></tr>
      <tr><th align="left">Faculty Incharge</th><td>{faculty_incharge}</td></tr>
      <tr><th align="left">Released By</th><td>{current_user.email}</td></tr>
      <tr><th align="left">Release Date</th><td>{datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</td></tr>
    </table>

    <p style="margin-top:20px;">Regards,<br><b>CSE Lab Management System</b></p>
    </body>
    </html>
    """

    # Send email
    if student_email:
        send_notification_email(student_email, subject, body, cc=cc_list)
        print(f"📩 Release email sent to {student_email} (CC: {cc_list})")
    else:
        print(f"⚠️ No email found for student roll {roll}")

    flash(f"Released cubicle {cubicle.number} from roll {roll}", "success")
    return redirect(url_for("space_allocation", roll=roll))


@app.route("/labs/<lab_code>/allotments")
@login_required
@roles_required('admin', 'staff' , 'faculty')
def lab_allotments(lab_code):
    lab = RoomLab.query.filter_by(name=lab_code).first_or_404()

    # 1️⃣ Students assigned to cubicles (even if no workstation assigned)
    cubicle_records = (
        db.session.query(
            Student.name, Student.roll, Student.course, Student.year,
            Student.faculty, Student.email, Student.phone,
            Cubicle.id.label("cubicle_id"),
            Cubicle.number.label("cubicle_number")
        )
        .join(Cubicle, Cubicle.student_roll == Student.roll)
        .join(RoomLab, RoomLab.id == Cubicle.room_lab_id)
        .filter(RoomLab.name == lab_code)
        .all()
    )

    # 2️⃣ Students with workstation (machine) allotments
    machine_records = (
       db.session.query(
            WorkstationAssignment.id.label("assignment_id"),
            WorkstationAssignment.is_active,
            WorkstationAssignment.issue_date,
            WorkstationAssignment.system_required_till,
            WorkstationAssignment.remarks,
            Student.name, Student.roll, Student.course, Student.year,
            Student.faculty, Student.email, Student.phone,
            Cubicle.number.label("cubicle_number"),
            WorkstationAsset.id.label("asset_id"),
            WorkstationAsset.serial,
            WorkstationAsset.manufacturer,
            WorkstationAsset.model,
            WorkstationAsset.indenter
        )
        .join(WorkstationAssignment, WorkstationAssignment.student_roll == Student.roll)
        .join(WorkstationAsset, WorkstationAsset.id == WorkstationAssignment.workstation_id)
        .join(Cubicle, Cubicle.student_roll == Student.roll)
        .join(RoomLab, RoomLab.id == Cubicle.room_lab_id)
        .filter(RoomLab.name == lab_code)
        .filter(WorkstationAssignment.is_active == True)
        .all()
    )

    # 🔹 Stats
    total_cubicles = db.session.query(Cubicle).filter(Cubicle.room_lab_id == lab.id).count()
    cubicle_assigned = len(cubicle_records)
    workstation_assigned = len(machine_records)

    stats = {
        "total_cubicles": total_cubicles,
        "cubicle_assigned": cubicle_assigned,
        "available_cubicles": total_cubicles - cubicle_assigned,
        "workstations_assigned": workstation_assigned,
        "staff_incharge": lab.staff_incharge
    }

    return render_template(
        "lab_allotments.html",
        lab=lab,
        cubicle_records=cubicle_records,
        machine_records=machine_records,
        stats=stats
    )

from flask import request, redirect, render_template, url_for, flash
from werkzeug.utils import secure_filename
import os

#
@app.route("/edit_student/<roll>", methods=["GET", "POST"])
@login_required
def edit_student(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    user = User.query.filter_by(email=student.email).first()

    # Ensure joining_year is int for template matching
    if isinstance(student.joining_year, str):
        student.joining_year = int(student.joining_year)
    if student.faculty:
        student.faculty = student.faculty.strip()
    if request.method == "POST":
        student.name = request.form["name"]
        student.course = request.form["course"]
        student.year = request.form["year"]
        student.joining_year = int(request.form["joining_year"])
        student.faculty = request.form["faculty"]
        student.phone = request.form.get("phone")

        new_photo = request.files.get("profile_photo")
        if new_photo and new_photo.filename != "":
            filename = secure_filename(new_photo.filename)
            new_photo.save(os.path.join("static/uploads", filename))
            student.profile_photo = filename

        user.email = student.email  # sync

        db.session.commit()
        flash("Student details updated successfully", "success")
        return redirect(url_for("allotment_options", roll=student.roll))

    return render_template("edit_student.html", student=student)

   
@app.route("/student/<string:roll>", methods=["GET", "POST"])
@login_required
@roles_required('admin', 'staff' , 'faculty')
def student_details(roll):
    # Fetch student record
    student = Student.query.filter_by(roll=roll).first_or_404()

    # Equipment assigned to this student
    assigned_equipment = Equipment.query.filter_by(assigned_to_roll=roll).all()

    # Unassigned equipment (for dropdown if needed)
    unassigned_equipment = Equipment.query.filter_by(assigned_to_roll=None).all()

    # Slurm account status
    slurm_account = SlurmAccount.query.filter_by(roll=roll).first()
    slurm_status = slurm_account.status if slurm_account else None
    slurm_exists = bool(slurm_account)

    return render_template(
        "student_details.html",
        student=student,
        assigned_equipment=assigned_equipment,
        unassigned_equipment=unassigned_equipment,
        slurm_exists=slurm_exists,
        slurm_status=slurm_status
    )




from flask import make_response, render_template
from weasyprint import HTML
from flask_login import login_required
from models import Student, Equipment, SlurmAccount

@app.route("/student_details/<roll>")
@login_required
def generate_student_pdf(roll):
    # 1️⃣ Fetch student record
    student = Student.query.filter_by(roll=roll).first_or_404()
    
    
    workstation_assignments=student.workstation_assignments

    # 2️⃣ Workstation assignments (already via relationship)
    workstation_assignments_sorted = sorted(
    student.workstation_assignments,
    key=lambda x: not x.is_active  # Active=True first
    )

    # 3️⃣ Assigned equipment (current)
    assigned_equipment = student.assigned_equipment

    # 4️⃣ Equipment history (query full objects)
    equipment_history = EquipmentHistory.query.filter_by(assigned_to_roll=student.roll).all()
    equipment_history_sorted = sorted(
    equipment_history,
    key=lambda h: h.unassigned_date is not None  # Active first (unassigned_date=None)
    )
# Attach equipment object and staff incharge dynamically
    for h in equipment_history:
        h.equipment_obj = Equipment.query.get(h.equipment_id)  # actual Equipment object
    # staff in-charge of the lab where the equipment belongs
        if h.equipment_obj and h.equipment_obj.assigned_to_roll:
            cubicle = Cubicle.query.filter_by(student_roll=h.equipment_obj.assigned_to_roll).first()
            h.staff_incharge = cubicle.room_lab.staff_incharge if cubicle else '—'
        else:
        # fallback: if equipment has location mapped to lab
            h.staff_incharge = '—'


    # 5️⃣ Slurm account info
    slurm = SlurmAccount.query.filter_by(roll=roll).first()
    slurm_exists = bool(slurm)
    slurm_status = slurm.status if slurm else None

    # 6️⃣ Render HTML
    rendered = render_template(
        "student_details.html",  # your PDF-specific template
        student=student,
        workstation_assignments=workstation_assignments_sorted,
        assigned_equipment=assigned_equipment,
        equipment_history=equipment_history_sorted,
        slurm_exists=slurm_exists,
        slurm_status=slurm_status
    )

    # 7️⃣ Generate PDF using WeasyPrint
    pdf = HTML(string=rendered).write_pdf()

    # 8️⃣ Return PDF as response (inline view)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={student.roll}_report.pdf'
    return response


@app.route('/faculty_assets', methods=['GET'])
@login_required
def faculty_assets():
    # Get selected faculty name from GET params
    selected_indenter = request.args.get('indenter', None)

    equipment_list = []
    workstation_list = []

    if selected_indenter:
        # Filter equipment by intender_name
        equipment_list = Equipment.query.filter_by(intender_name=selected_indenter).all()

        # Filter workstations by indenter
        workstation_list = WorkstationAsset.query.filter_by(indenter=selected_indenter).all()

    return render_template(
        'faculty_assets.html',
        selected_indenter=selected_indenter,
        equipment_list=equipment_list,
        workstation_list=workstation_list
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
