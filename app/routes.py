import json
from datetime import date #for calendar dates
#Blueprint: allows me to group routes/pages together
#render_template: renders HTML templates for the browser
#request: handles data coming from forms or URL queries
#redirect: redirects the browser to another page
#url_for: dynamically builds URLs based on route names
#session: keeps track of logged-in users
#flash: displays temporary messages to the user
#jsonify: sends JSON responses (used for APIs)
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
#generate_password_hash / check_password_hash: safely store and verify passwords
from werkzeug.security import generate_password_hash, check_password_hash
#my database connection and models
from .models import db, User, Plan, Session

#main is a group of routes
#Blueprint lets Flask know these routes belong together
#this is registered in my __init__.py with app.register_blueprint(main)
main = Blueprint("main", __name__)

#checks if a user is logged in by seeing if user_id is in the session.
#used throughout your routes to protect pages
def require_login():
    return "user_id" in session #returns True or False

def parse_date(value): #parse dates from forms
    if not value:
        return None
    try:
        return date.fromisoformat(value) #converts a string like "2026-05-15" into a Python date object
    except ValueError:
        return None

# ----------------------
# Public pages
# ----------------------
@main.route("/") #homepage route (/)
def home():
    return render_template("index.html") #shows index.html to the user

@main.route("/api/check-email") #API route that returns JSON???
def api_check_email(): #live email validation on signup forms
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"exists": False})
    user = User.query.filter_by(email=email).first()
    return jsonify({"exists": user is not None}) #returns {"exists": True} if the email is already registered

# ----------------------
# Auth
# ----------------------
@main.route("/signup", methods=["GET", "POST"]) #GET (show signup form) and POST (process signup)
def signup():
    if require_login(): #checks if the user is logged in first
        return redirect(url_for("main.dashboard")) #redirects if yes
    if request.method == "POST": #reads from data
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")
        if not first_name or not last_name or not email or not password: #make sure all fields filled
            return render_template("signup.html", error="All fields are required.")
        if password != confirm: #password matches confirmation
            return render_template("signup.html", error="Passwords do not match.")
        if len(password) < 8: #password at least 8 characters
            return render_template("signup.html", error="Password must be at least 8 characters.")
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password): #password needs to include a letter and a number
            return render_template(
                "signup.html",
                error="Password must contain at least one letter and one number."
            )
        if User.query.filter_by(email=email).first(): #email not already registered
            return render_template("signup.html", error="This email is already registered.")
        #creates a new User with a hashed password
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256")
        )
        #saves it to the database
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id #stores the user’s ID in session
        flash("Account created successfully.", "success") #success message
        return redirect(url_for("main.dashboard")) #redirects to dashboard
    return render_template("signup.html") #shows signup.html to the user

@main.route("/login", methods=["GET", "POST"])
def login():
    if require_login():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first() #check if email exists
        if not user or not check_password_hash(user.password_hash, password): #checks if email exists and password matches using check_password_hash
            return render_template("login.html", error="Invalid email or password.")
        session["user_id"] = user.id #stores user_id in session if login is successful
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.home"))


# ----------------------
# Dashboard
# ----------------------
@main.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("main.login"))

    plans = (
        Plan.query
        .filter_by(user_id=session["user_id"])
        .order_by(Plan.updated_at.desc())
        .all()
    )

    return render_template("dashboard.html", plans=plans, today=date.today())


# ----------------------
# Templates
# ----------------------
@main.route("/templates")
def templates():
    q = Plan.query.filter_by(is_template=True)

    if require_login():
        q = q.filter(Plan.user_id != session["user_id"])

    templates_list = q.order_by(Plan.updated_at.desc()).all()
    return render_template("templates.html", templates=templates_list)


@main.route("/templates/<int:template_id>")
def template_view(template_id):
    template = Plan.query.filter_by(id=template_id, is_template=True).first_or_404()
    return render_template("template_view.html", template=template)


@main.route("/templates/<int:template_id>/copy", methods=["POST"])
def template_copy(template_id):
    if not require_login():
        return redirect(url_for("main.login"))

    original = Plan.query.filter_by(id=template_id, is_template=True).first_or_404()

    copied_plan = Plan(
        title=f"{original.title} (copy)",
        description=original.description,
        start_date=original.start_date,
        end_date=original.end_date,
        is_template=False,
        user_id=session["user_id"]
    )

    db.session.add(copied_plan)
    db.session.flush()

    for original_session in original.sessions:
        copied_session = Session(
            title=original_session.title,
            session_type=original_session.session_type,
            status="notstarted",
            due_date=original_session.due_date,
            notes=original_session.notes,
            checklist=original_session.checklist,
            plan_id=copied_plan.id
        )
        db.session.add(copied_session)

    db.session.commit()

    flash("Template copied to your plans.", "success")
    return redirect(url_for("main.plan_view", plan_id=copied_plan.id))


# ----------------------
# Plan CRUD
# ----------------------
@main.route("/plan/new", methods=["GET", "POST"])
@main.route("/plan/<int:plan_id>/edit", methods=["GET", "POST"])
def plan_edit(plan_id=None):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = None

    if plan_id is not None:
        plan = Plan.query.filter_by(
            id=plan_id,
            user_id=session["user_id"]
        ).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_date = parse_date(request.form.get("start_date", ""))
        end_date = parse_date(request.form.get("end_date", ""))
        is_template = request.form.get("is_template") == "on"

        if not title:
            return render_template("plan_edit.html", plan=plan, error="Title is required.")

        if start_date and end_date and end_date < start_date:
            return render_template(
                "plan_edit.html",
                plan=plan,
                error="End date cannot be before start date."
            )

        if plan is None:
            plan = Plan(user_id=session["user_id"])
            db.session.add(plan)

        plan.title = title
        plan.description = description
        plan.start_date = start_date
        plan.end_date = end_date
        plan.is_template = is_template

        db.session.commit()

        flash("Plan saved successfully.", "success")
        return redirect(url_for("main.plan_view", plan_id=plan.id))

    return render_template("plan_edit.html", plan=plan)


@main.route("/plan/<int:plan_id>")
def plan_view(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    return render_template("plan_view.html", plan=plan)


@main.route("/plan/<int:plan_id>/share", methods=["POST"])
def plan_share(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    plan.is_template = not plan.is_template
    db.session.commit()

    if plan.is_template:
        flash("Plan shared as a public template.", "success")
    else:
        flash("Plan is no longer shared as a template.", "success")

    return redirect(url_for("main.plan_view", plan_id=plan.id))


@main.route("/plan/<int:plan_id>/delete", methods=["POST"])
def plan_delete(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(plan)
    db.session.commit()

    flash("Plan deleted successfully.", "success")
    return redirect(url_for("main.dashboard"))


# ----------------------
# Session CRUD
# ----------------------
@main.route("/plan/<int:plan_id>/session/new", methods=["POST"])
def session_create(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    title = request.form.get("title", "Untitled Session").strip() or "Untitled Session"

    new_session = Session(
        title=title,
        session_type="lecture",
        status="notstarted",
        plan_id=plan.id
    )

    db.session.add(new_session)
    db.session.commit()

    return redirect(url_for(
        "main.session_edit",
        plan_id=plan.id,
        session_id=new_session.id
    ))


@main.route("/plan/<int:plan_id>/session/<int:session_id>/edit", methods=["GET", "POST"])
def session_edit(plan_id, session_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    session_obj = Session.query.filter_by(
        id=session_id,
        plan_id=plan.id
    ).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        session_type = request.form.get("session_type", "lecture")
        custom_type = request.form.get("custom_type", "").strip()
        status = request.form.get("status", "notstarted")
        due_date = parse_date(request.form.get("due_date", ""))
        notes = request.form.get("notes", "").strip()

        valid_statuses = {"notstarted", "inprogress", "done"}
        valid_types = {"lecture", "workshop", "revision", "assignment", "other"}

        if not title:
            checklist_data = json.loads(session_obj.checklist or "[]")
            return render_template(
                "session_edit.html",
                plan=plan,
                session_obj=session_obj,
                checklist_data=checklist_data,
                error="Title is required."
            )

        if status not in valid_statuses:
            status = "notstarted"

        if session_type not in valid_types:
            session_type = "lecture"

        if session_type == "other" and custom_type:
            session_type = custom_type[:50]

        checklist_items = request.form.getlist("checklist_item")
        checklist_done_indexes = set(request.form.getlist("checklist_done"))

        checklist_data = []
        for i, item_text in enumerate(checklist_items):
            item_text = item_text.strip()
            if item_text:
                checklist_data.append({
                    "text": item_text,
                    "done": str(i) in checklist_done_indexes
                })

        session_obj.title = title
        session_obj.session_type = session_type
        session_obj.status = status
        session_obj.due_date = due_date
        session_obj.notes = notes
        session_obj.checklist = json.dumps(checklist_data)

        db.session.commit()

        flash("Session saved successfully.", "success")
        return redirect(url_for("main.plan_view", plan_id=plan.id))

    checklist_data = json.loads(session_obj.checklist or "[]")

    return render_template(
        "session_edit.html",
        plan=plan,
        session_obj=session_obj,
        checklist_data=checklist_data
    )


@main.route("/plan/<int:plan_id>/session/<int:session_id>/delete", methods=["POST"])
def session_delete(plan_id, session_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"]
    ).first_or_404()

    session_obj = Session.query.filter_by(
        id=session_id,
        plan_id=plan.id
    ).first_or_404()

    db.session.delete(session_obj)
    db.session.commit()

    flash("Session deleted successfully.", "success")
    return redirect(url_for("main.plan_view", plan_id=plan.id))