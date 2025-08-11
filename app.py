from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request
from models import db, User, Workstation, Equipment, ProvisioningRequest
import pandas as pd
import os
from datetime import date


from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
print("🔐 ENV Secret Key:", os.getenv("SECRET_KEY"))



import requests

from collections import defaultdict
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import secrets
from flask import flash, redirect, url_for
from flask import flash, redirect, url_for

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# app.secret_key = "PPPAAA@RRRTTT"


app.secret_key = os.getenv("SECRET_KEY")



#db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
from models import Workstation, Equipment
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login_home")
@login_required
def login_home():
    return render_template("login_home.html")


from flask import render_template, request, redirect, url_for

from models import Student, Workstation, Equipment, EquipmentHistory, RoomLab, Cubicle
from datetime import datetime

# @app.route("/index", methods=["GET", "POST"])
# def index_student_form():
#     error = None
#     success = None
#     room_lab_names = [room.name for room in RoomLab.query.all()]
#     all_equipment = Equipment.query.all()

#     if request.method == "POST":
#         form = request.form.to_dict()
#         roll = form.get("roll")
#         requirement_type = form.get("requirement_type")

#         # Create or fetch student
#         student = Student.query.filter_by(roll=roll).first()
#         if not student:
#             student = Student(
#                 name=form.get("name"),
#                 roll=roll,
#                 course=form.get("course"),
#                 year=form.get("year"),
#                 joining_year=form.get("joining_year"),
#                 faculty=form.get("faculty"),
#                 email=form.get("email"),
#                 phone=form.get("phone")
#             )
#             db.session.add(student)
#             db.session.flush()

#         # Option 1: Cubicle only
#         if requirement_type == "cubicle_only":
#             room = form.get("room_lab_name")
#             cubicle = form.get("cubicle_no")
#             exists = Workstation.query.filter_by(room_lab_name=room, cubicle_no=cubicle).first()
#             if exists:
#                 error = f"⚠️ Cubicle {cubicle} in {room} is already assigned."
#             else:
#                 ws = Workstation(roll=roll, room_lab_name=room, cubicle_no=cubicle)
#                 db.session.add(ws)
#                 success = "Cubicle assigned successfully."

#         # Option 2: Workstation allocation
#         elif requirement_type == "workstation":
#             room = form.get("room_lab_name")
#             cubicle = form.get("cubicle_no")
#             exists = Workstation.query.filter_by(room_lab_name=room, cubicle_no=cubicle).first()
#             if exists:
#                 error = f"⚠️ Cubicle {cubicle} in {room} is already assigned."
#             else:
#                 ws = Workstation(
#                     roll=roll,
#                     room_lab_name=room,
#                     cubicle_no=cubicle,
#                     manufacturer=form.get("manufacturer"),
#                     otherManufacturer=form.get("otherManufacturer"),
#                     model=form.get("model"),
#                     serial=form.get("serial"),
#                     os=form.get("os"),
#                     otherOs=form.get("otherOs"),
#                     processor=form.get("processor"),
#                     cores=form.get("cores"),
#                     ram=form.get("ram"),
#                     otherRam=form.get("otherRam"),
#                     storage_type1=form.get("storage_type1"),
#                     storage_capacity1=form.get("storage_capacity1"),
#                     storage_type2=form.get("storage_type2"),
#                     storage_capacity2=form.get("storage_capacity2"),
#                     gpu=form.get("gpu"),
#                     vram=form.get("vram"),
#                     issue_date=form.get("issue_date"),
#                     system_required_till=form.get("system_required_till"),
#                     po_date=form.get("po_date"),
#                     source_of_fund=form.get("source_of_fund"),
#                     keyboard_provided=form.get("keyboard_provided"),
#                     keyboard_details=form.get("keyboard_details"),
#                     mouse_provided=form.get("mouse_provided"),
#                     mouse_details=form.get("mouse_details"),
#                     monitor_provided=form.get("monitor_provided"),
#                     monitor_details=form.get("monitor_details"),
#                     monitor_size=form.get("monitor_size"),
#                     monitor_serial=form.get("monitor_serial")
#                 )
#                 db.session.add(ws)
#                 success = "Workstation details saved."

#         # Option 3: Assign IT Equipment
#         elif requirement_type == "it_equipment":
#             selected_items = [key for key in form if key.startswith("equipment_")]
#             for item_key in selected_items:
#                 eq_id = form.get(item_key)
#                 if eq_id:
#                     eq = Equipment.query.get(int(eq_id))
#                     if eq and eq.status == "Available":
#                         eq.assigned_to_roll = roll
#                         eq.assigned_by = "System"
#                         eq.assigned_date = datetime.now()
#                         eq.status = "Assigned"

#                         # Log to history
#                         history = EquipmentHistory(
#                             equipment_id=eq.id,
#                             assigned_to_roll=roll,
#                             assigned_by="System",
#                             assigned_date=datetime.now(),
#                             status_snapshot="Assigned"
#                         )
#                         db.session.add(history)
#             success = "Equipment assigned successfully."

#         db.session.commit()
#         return render_template(
#             "index.html",
#             room_lab_names=room_lab_names,
#             equipment_list=all_equipment,
#             error=error,
#             success=success
#         )

#     return render_template(
#         "index.html",
#         room_lab_names=room_lab_names,
#         equipment_list=all_equipment,
#         error=error,
#         success=success
#     )



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
                        eq.status = "Assigned"

                        history = EquipmentHistory(
                            equipment_id=eq.id,
                            assigned_to_roll=roll,
                            assigned_by="System",
                            assigned_date=datetime.now(),
                            status_snapshot="Assigned"
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
@app.route("/records")
def view_records():
    all_records = Workstation.query.all()

    # Lab-wise capacity definition
    lab_capacities = {
        "CS-107": 43,
        "CS-108": 21,
        "CS-109": 114,
        "CS-207": 30,
        "CS-208": 25,
        "CS-209": 142,
        "CS-317": 25,
        "CS-318": 25,
        "CS-319": 32,
        "CS-320": 27,
        "CS-411": 25,
        "CS-412": 33
    }

    from collections import defaultdict
    grouped_records = defaultdict(list)

    # Group records by lab
    for r in all_records:
        grouped_records[r.room_lab_name].append(r)

    # Calculate stats per lab
    lab_stats = {}
    for lab, records in grouped_records.items():
        total = lab_capacities.get(lab, 0)
        used = len(records)
        available = total - used
        lab_stats[lab] = {"total": total, "used": used, "available": available}

    # Sort labs by name
    grouped_records = dict(sorted(grouped_records.items()))

    return render_template("records.html", grouped_records=grouped_records, lab_stats=lab_stats)

from flask_login import login_required, current_user

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    result = None
    message = None

    if request.method == "POST":
        roll = request.form.get("roll").strip()

        # Check if the workstation is allocated
        result = Workstation.query.filter_by(roll=roll).first()

        if result:
            # Redirect to detailed student info page
            return redirect(url_for('student_details', roll=roll))
        else:
            # Show not found message
            message = f"❌ No machine has been allocated for Roll Number: {roll}"

    return render_template("search.html", result=result, message=message, layout="login_home.html")



from flask import render_template
from collections import defaultdict
from models import Workstation  # Adjust this import to match your structure



from flask import render_template
from collections import defaultdict

@app.route("/utilization")
def utilization():
    all_records = Workstation.query.all()

    lab_capacities = {
        "CS-107": 43,
        "CS-108": 21,
        "CS-109": 114,
        "CS-207": 30,
        "CS-208": 25,
        "CS-209": 142,
        "CS-317": 25,
        "CS-318": 25,
        "CS-319": 32,
        "CS-320": 27,
        "CS-411": 25,
        "CS-412": 33
    }

    lab_counts = defaultdict(int)
    used_seats_map = defaultdict(list)

    for r in all_records:
        lab_counts[r.room_lab_name] += 1
        try:
            seat_no = int(r.cubicle_no)
            hover_name = "Occupied"
            if r.name and r.roll:
                hover_name = f"{r.name} ({r.roll})"
            elif r.name:
                hover_name = r.name
            elif r.roll:
                hover_name = r.roll

            used_seats_map[r.room_lab_name].append((seat_no, hover_name))
        except (ValueError, TypeError):
            pass  # Invalid seat number; skip

    lab_stats = {}
    total_seats = 0
    total_used = 0

    for lab, total in lab_capacities.items():
        used = lab_counts.get(lab, 0)
        available = total - used
        used_seats = dict(used_seats_map.get(lab, []))  # {seat_no: hover_text}

        lab_stats[lab] = {
            "total": total,
            "used": used,
            "available": available,
            "used_seats": used_seats
        }

        total_seats += total
        total_used += used

    total_available = total_seats - total_used
    occupancy_percent = round((total_used / total_seats * 100), 1) if total_seats else 0
    print("======== DEBUG: LAB STATS ========")
    for lab, stats in lab_stats.items():
        print(f"{lab}: total={stats['total']}, used={stats['used']}, available={stats['available']}")
    print(f"TOTAL: {total_seats}, USED: {total_used}, AVAILABLE: {total_available}, OCCUPANCY: {occupancy_percent}%")
    print("===================================")

    return render_template(
        "utilization.html",
        lab_stats=lab_stats,
        total_seats=total_seats,
        total_used=total_used,
        total_available=total_available,
        occupancy_percent=occupancy_percent
    )

@app.route("/alloted_machines")
def alloted_machines():
    # Get only records where student name or roll is not null (i.e., allotted)
     allotted_records = Workstation.query.filter(
        (Workstation.name != None) | (Workstation.roll != None)
    ).all()
     allotted_records.sort(key=lambda r: (r.room_lab_name or "", r.cubicle_no or ""))


     return render_template("alloted_machines.html", records=allotted_records)

from models import Equipment, Workstation, EquipmentHistory

from datetime import datetime
from flask import render_template, request, redirect, flash
from werkzeug.security import generate_password_hash
from models import User, db


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validation
        if not email.endswith("@cse.iith.ac.in"):
            flash("Only @cse.iith.ac.in emails are allowed.", "danger")
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

        is_admin = email.lower() == "admin@cse.iith.ac.in"

        new_user = User(
            email=email,
            password=generate_password_hash(password),
            is_approved=is_admin,
            approved_at=datetime.utcnow() if is_admin else None,
            registered_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        flash("✅ Registered!" + (" You're auto-approved as Admin." if is_admin else " Please wait for admin approval."))
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
    return render_template("registered_users.html", all_users=users)




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
            # In production, send email. Here, show URL
            flash(f"Reset link: http://127.0.0.1:5006/reset-password/{token}")
        else:
            flash("Email not found")
        return redirect(url_for("reset_request"))
    return render_template("reset_request.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        return "Invalid or expired token"

    if request.method == "POST":
        new_password = request.form.get("password")
        user.password = generate_password_hash(new_password)  # ✅ hash password
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash("Password updated! You can now log in.")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

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
                flash(f"{user.email} approved.", "success")
            elif action == "reject":
                user.is_approved = False
                user.approved_at = datetime.utcnow()
                flash(f"{user.email} rejected.", "danger")
            db.session.commit()

        return redirect("/admin/approve")

    # Show all pending users
    pending_users = User.query.filter_by(is_approved=False).all()
    return render_template("approve_users.html", users=pending_users)

@app.route("/admin/toggle_user/<int:user_id>")
@login_required
def toggle_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    
    user = User.query.get_or_404(user_id)
    if user.email == "admin@cse.iith.ac.in":
        flash("Admin account cannot be blocked.")
        return redirect(url_for("registered_users"))

    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{'Blocked' if not user.is_active else 'Unblocked'} {user.email}")
    return redirect(url_for("registered_users"))


@app.route("/admin/delete_user/<int:user_id>")
@login_required
def delete_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"

    user = User.query.get_or_404(user_id)
    if user.email == "admin@cse.iith.ac.in":
        flash("Admin account cannot be deleted.")
        return redirect(url_for("registered_users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted user: {user.email}")
    return redirect(url_for("registered_users"))


@app.route("/admin/approve/<int:user_id>")
@login_required
def approve_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    user = User.query.get(user_id)
    if user:
        user.is_approved = True
        db.session.commit()
    return redirect(url_for("approve_panel"))


@app.route("/admin/reject/<int:user_id>")
@login_required
def reject_user(user_id):
    if current_user.email != "admin@cse.iith.ac.in":
        return "Access Denied"
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("approve_panel"))

from flask_login import current_user

@app.route("/cse_labs")
@login_required
def cse_labs():
    layout_template = "login_home.html" if current_user.is_authenticated else "base.html"
    return render_template("cse_labs.html", layout=layout_template)

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
from models import db, Equipment, Workstation

@app.route("/equipment_entry", methods=["GET", "POST"])
@login_required
def equipment_entry():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        manufacturer = request.form["manufacturer"]
        model = request.form["model"]
        invoice_number = request.form.get("invoice_number")
        cost_per_unit = request.form.get("cost_per_unit", type=float)
        warranty_expiry = request.form.get("warranty_expiry")
        location = request.form["location"]
        purchase_date = request.form["purchase_date"]
        status = request.form["status"]
        po_date = request.form["po_date"]
        intender_name = request.form["intender_name"]
        quantity = request.form.get("quantity", type=int)
        assigned_to_roll = request.form.get("assigned_to_roll")

        today = date.today()
        date_str = today.strftime("%Y-%m-%d")
        current_count = Equipment.query.filter_by(category=category).count()

        for i in range(quantity):
            serial_number = request.form.get(f"serial_number_{i+1}")
            serial = f"{current_count + i + 1:03}"
            department_code = f"CSE/{date_str}/{category}/{serial}"

            equipment = Equipment(
                name=name,
                category=category,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                invoice_number=invoice_number,
                cost_per_unit=cost_per_unit,
                warranty_expiry=warranty_expiry,
                location=location,
                purchase_date=purchase_date,
                status=status,
                po_date=po_date,
                intender_name=intender_name,
                quantity=1,  # each entry represents one unit
                department_code=department_code,
                assigned_to_roll=assigned_to_roll if assigned_to_roll else None
            )
            db.session.add(equipment)

        db.session.commit()
        flash(f"{quantity} equipment entries added successfully.", "success")
        return redirect(url_for("equipment_list"))

    students = Workstation.query.all()
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

@app.route("/equipment_list", methods=["GET"])
def equipment_list():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Adjust as needed

    query = Equipment.query

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
                Equipment.purchase_date.ilike(f"%{search_query}%")
            )
        )

    if status_filter:
        query = query.filter(Equipment.status == status_filter)

    pagination = query.order_by(Equipment.category, Equipment.name).paginate(page=page, per_page=per_page)

    # Group the paginated items by category
    grouped_equipment = defaultdict(list)
    for eq in pagination.items:
        grouped_equipment[eq.category].append(eq)

    return render_template("equipment_list.html",
                           grouped_equipment=grouped_equipment,
                           pagination=pagination,
                           search_query=search_query,
                           status_filter=status_filter)


from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Equipment, Workstation, db
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Equipment, Workstation  # Update this line as per your actual import





@app.route('/assign_equipment/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def assign_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)

    if equipment.status.lower() in ['scrap', 'repaired']:
        flash(f"Cannot assign equipment with status '{equipment.status}'.", "warning")
        return redirect(url_for('equipment_list'))

    if request.method == 'POST':
        assigned_to_roll = request.form.get('assigned_to_roll')
        now = datetime.utcnow()

        if assigned_to_roll:
            student = Workstation.query.filter_by(roll=assigned_to_roll).first()
            if student:
                equipment.assigned_to_roll = student.roll
                equipment.assigned_by = current_user.email
                equipment.assigned_date = now
                equipment.status = 'Issued'

                history = EquipmentHistory(
                    equipment_id=equipment.id,
                    assigned_to_roll=student.roll,
                    assigned_by=current_user.email,
                    assigned_date=now,
                    unassigned_date=None,
                    status_snapshot='Issued'
                )
                db.session.add(history)

                flash(f"Assigned to {student.name} ({student.roll})", "success")
            else:
                flash("Invalid student selected", "danger")
        else:
            # Unassignment
            history = EquipmentHistory(
                equipment_id=equipment.id,
                assigned_to_roll=equipment.assigned_to_roll,
                assigned_by=current_user.email,
                assigned_date=equipment.assigned_date,
                unassigned_date=now,
                status_snapshot='Available'
            )
            db.session.add(history)

            equipment.assigned_to_roll = None
            equipment.assigned_by = None
            equipment.assigned_date = None
            equipment.status = 'Available'

            flash("Equipment unassigned", "info")

        db.session.commit()
        return redirect(url_for('equipment_list'))

    courses = [c[0] for c in db.session.query(Workstation.course).distinct().all()]
    years = [y[0] for y in db.session.query(Workstation.year).distinct().all()]
    return render_template("assign_equipment.html", equipment=equipment, courses=courses, years=years)

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




@app.route('/lab_details/<lab_code>')
@login_required
def lab_details(lab_code):
    from models import Workstation  # Ensure this is the correct model

    total_capacity = {
        "CS-107": 43,
        "CS-108": 21,
        "CS-109": 114,
        "CS-207": 30,
        "CS-208": 25,
        "CS-209": 142,
        "CS-317": 25,
        "CS-318": 25,
        "CS-319": 32,
        "CS-320": 27,
        "CS-411": 25,
        "CS-412": 33
    }

    lab_meta = {
        "CS-107": {"faculty": "Dr. Aravind", "meeting_rooms": 1},
        "CS-108": {"faculty": "Dr. Shravan", "meeting_rooms": 1},
        "CS-109": {"faculty": "Dr. Geetha", "meeting_rooms": 2},
        "CS-207": {"faculty": "Dr. Rajeev", "meeting_rooms": 1},
        "CS-208": {"faculty": "Dr. Sneha", "meeting_rooms": 1},
        "CS-209": {"faculty": "Dr. Ramesh", "meeting_rooms": 3},
        "CS-317": {"faculty": "Dr. Anjali", "meeting_rooms": 1},
        "CS-318": {"faculty": "Dr. Vinay", "meeting_rooms": 1},
        "CS-319": {"faculty": "Dr. Divya", "meeting_rooms": 1},
        "CS-320": {"faculty": "Dr. Manoj", "meeting_rooms": 1},
        "CS-411": {"faculty": "Dr. Isha", "meeting_rooms": 2},
        "CS-412": {"faculty": "Dr. Aditya", "meeting_rooms": 2}
    }

    lab_name = lab_code.upper()
    capacity = total_capacity.get(lab_name, 0)
    faculty = lab_meta.get(lab_name, {}).get("faculty", "Not Assigned")
    meeting_rooms = lab_meta.get(lab_name, {}).get("meeting_rooms", 0)

    workstations = Workstation.query.filter_by(room_lab_name=lab_name).all()

    # Create seat map
    assigned_seats = {}
    for ws in workstations:
        if ws.cubicle_no:
            cleaned = ws.cubicle_no.strip()
            if cleaned.isdigit():
                assigned_seats[int(cleaned)] = ws

    seats = []
    for seat_num in range(1, capacity + 1):
        if seat_num in assigned_seats:
            student = assigned_seats[seat_num]
            seats.append({
                "number": seat_num,
                "occupied": True,
                "student_name": student.name,
                "roll_number": student.roll,
                "email": student.email,
                "branch": student.course,
                "year": student.year,
                "photo_url": f"/static/photos/{student.roll}.jpg"
            })
        else:
            seats.append({
                "number": seat_num,
                "occupied": False
            })

    return render_template(
        "lab_details.html",
        lab_code=lab_name,
        capacity=capacity,
        used_seating=len(workstations),
        available_seating=capacity - len(workstations),
        faculty=faculty,
        meeting_rooms=meeting_rooms,
        seats=seats
    )


@app.route("/student/<string:roll>", methods=["GET", "POST"])
@login_required
def student_details(roll):
    student = Workstation.query.filter_by(roll=roll).first_or_404()

    # Equipment assigned to this student
    assigned_equipment = Equipment.query.filter_by(assigned_to_roll=roll).all()

    # Unassigned equipment for dropdown
    unassigned_equipment = Equipment.query.filter_by(assigned_to_roll=None).all()

    return render_template("student_details.html",
                           student=student,
                           assigned_equipment=assigned_equipment,
                           unassigned_equipment=unassigned_equipment)


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




@app.route("/slurm/check", methods=["GET", "POST"])
def slurm_check():
    result = None
    if request.method == "POST":
        roll = request.form.get("roll")
        status = check_user_on_remote(roll)  # ✅ THIS CALLS THE FUNCTION

        if status is True:
            result = {"roll": roll, "found": True}
        elif status is False:
            result = {"roll": roll, "found": False}
        else:
            result = {"roll": roll, "found": None}  # SSH or other error

    return render_template("slurm_facility.html", result=result)


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

@app.route("/user/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if not check_password_hash(current_user.password, current):
            flash("Current password is incorrect.")
        elif new != confirm:
            flash("New passwords do not match.")
        else:
            current_user.password = generate_password_hash(new)
            db.session.commit()
            flash("Password updated successfully!")
            return redirect(url_for("user_settings"))

    return render_template("user_settings.html")


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
from models import Workstation
from flask import render_template, request

@app.route('/students_directory', methods=['GET'])
def students_directory():
    # Get filter values from query parameters
    course = request.args.get('course')
    year = request.args.get('year')
    room_lab_name = request.args.get('room_lab_name')
    roll = request.args.get('roll')
    faculty = request.args.get('faculty')

    # Start with base query
    query = Workstation.query

    # Apply filters
    if course:
        query = query.filter(Workstation.course == course)
    if year:
        query = query.filter(Workstation.year == year)
    if room_lab_name:
        query = query.filter(Workstation.room_lab_name == room_lab_name)
    if roll:
        query = query.filter(Workstation.roll.ilike(f"%{roll}%"))
    if faculty:
        query = query.filter(Workstation.faculty == faculty)

    students = query.all()

    # For dropdown filters
    faculty_list = [
        "Prof. Antony Franklin", "Dr. Ashish Mishra", "Prof. Bheemarjuna Reddy Tamma",
        "Prof. C. Krishna Mohan", "Dr. J. Saketha Nath", "Dr. Jyothi Vedurada",
        "Dr. Kotaro Kataoka", "Prof. M. V. Panduranga Rao", "Dr. Manish Singh",
        "Dr. Maria Francis", "Prof. Maunendra Sankar Desarkar", "Dr. N. R. Aravind",
        "Dr. Nitin Saurabh", "Dr. Praveen Tammana", "Dr. Rajesh Kedia", "Dr. Rakesh Venkat",
        "Dr. Ramakrishna Upadrasta", "Dr. Rameshwar Pratap", "Dr. Rogers Mathew",
        "Prof. Sathya Peri", "Dr. Saurabh Kumar", "Dr. Shirshendu Das", "Dr. Sobhan Babu",
        "Dr. Srijith P. K.", "Prof. Subrahmanyam Kalyanasundaram", "Prof. Vineeth N. Balasubramanian"
    ]

    labs = ["CS-107", "CS-108", "CS-109", "CS-207", "CS-208", "CS-209",
            "CS-317", "CS-318", "CS-319", "CS-320", "CS-411", "CS-412"]

    return render_template("students_directory.html", students=students,
                           faculty_list=faculty_list, labs=labs)



@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
def edit_equipment(id):
    item = Equipment.query.get_or_404(id)

    if request.method == 'POST':
        item.name = request.form['name']
        item.category = request.form['category']
        item.manufacturer = request.form['manufacturer']
        item.model = request.form['model']
        item.serial_number = request.form['serial_number']
        item.location = request.form['location']
        item.purchase_date = request.form['purchase_date']
        item.status = request.form['status']
        item.po_date = request.form['po_date']
        item.intender_name = request.form['intender_name']
        item.quantity = int(request.form['quantity'])
        item.department_code = request.form['department_code']

        db.session.commit()
        return redirect(url_for('equipment_list'))

    return render_template('edit_equipment.html', item=item)

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

@app.route('/generate_equipment_pdf/<int:student_id>')
def generate_equipment_pdf(student_id):
    student = Workstation.query.get_or_404(student_id)
    # assigned_equipment = Equipment.query.filter_by(assigned_to=student_id).all()
    # assigned_equipment = Equipment.query.filter_by(assigned_to_id=student_id).all()
    assigned_equipment = Equipment.query.filter_by(assigned_to_roll=student.roll).all()

    # Use the same template that renders the HTML view
    rendered = render_template('pdf_student.html', student=student, assigned_equipment=assigned_equipment)

    # Convert to PDF using WeasyPrint
    from weasyprint import HTML
    pdf_file = HTML(string=rendered).write_pdf()

    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Student_{student.roll}_Details.pdf'
    return response

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
from models import Workstation, db
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

from flask import render_template, request, redirect, url_for, flash
from models import Workstation # adjust import path as per your project
from app import db # or your SQLAlchemy instance
@app.route('/edit_workstation/<int:id>', methods=['GET', 'POST'])
def edit_workstation(id):
    workstation = Workstation.query.get_or_404(id)

    if request.method == 'POST':
        # All assignments...
        workstation.name = request.form['name']
        workstation.roll = request.form['roll']
        workstation.course = request.form['course']
        workstation.year = request.form['year']
        workstation.faculty = request.form['faculty']
        workstation.staff_incharge = request.form['staff_incharge']
        workstation.email = request.form['email']
        workstation.phone = request.form['phone']
        workstation.room_lab_name = request.form['room_lab_name']
        workstation.cubicle_no = request.form['cubicle_no']

        workstation.manufacturer = request.form['manufacturer']
        workstation.otherManufacturer = request.form['otherManufacturer']
        workstation.model = request.form['model']
        workstation.serial = request.form['serial']
        workstation.os = request.form['os']
        workstation.otherOs = request.form['otherOs']
        workstation.processor = request.form['processor']
        workstation.cores = request.form['cores']
        workstation.ram = request.form['ram']
        workstation.otherRam = request.form['otherRam']

        workstation.storage_type1 = request.form['storage_type1']
        workstation.storage_capacity1 = request.form['storage_capacity1']
        workstation.storage_type2 = request.form['storage_type2']
        workstation.storage_capacity2 = request.form['storage_capacity2']

        workstation.gpu = request.form['gpu']
        workstation.vram = request.form['vram']

        workstation.issue_date = request.form['issue_date']
        workstation.system_required_till = request.form['system_required_till']
        workstation.po_date = request.form['po_date']
        workstation.source_of_fund = request.form['source_of_fund']

        workstation.keyboard_provided = request.form['keyboard_provided']
        workstation.keyboard_details = request.form['keyboard_details']
        workstation.mouse_provided = request.form['mouse_provided']
        workstation.mouse_details = request.form['mouse_details']
        workstation.monitor_provided = request.form['monitor_provided']
        workstation.monitor_details = request.form['monitor_details']
        workstation.monitor_size = request.form['monitor_size']
        workstation.monitor_serial = request.form['monitor_serial']

        try:
            db.session.commit()
            flash('Workstation updated successfully!', 'success')
            return redirect(url_for('alloted_machines'))  # Replace with actual route
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating workstation: {e}', 'danger')


    return render_template('edit_workstation.html', workstation=workstation)


@app.route('/delete_workstation/<int:id>', methods=['POST', 'GET'])
def delete_workstation(id):
    workstation = Workstation.query.get_or_404(id)
    try:
        db.session.delete(workstation)
        db.session.commit()
        flash('Workstation deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting workstation: {e}', 'danger')
    return redirect(url_for('alloted_machines'))


if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True, port=5009)
