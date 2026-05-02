from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Plan, Session

main = Blueprint("main", __name__)

# --- Helper ---
def require_login():
    return "user_id" in session


# ----------------------
# Public pages
# ----------------------
@main.route("/")
def home():
    return render_template("index.html")


# ----------------------
# Auth
# ----------------------
@main.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("main.signup"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.signup"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("This email is already registered. Please log in.", "danger")
            return redirect(url_for("main.login"))

        user = User(
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        flash("Account created successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("main.login"))

        session["user_id"] = user.id
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


# ----------------------
# Dashboard
# ----------------------
@main.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    plans = Plan.query.filter_by(user_id=user_id).order_by(Plan.id.desc()).all()
    return render_template("dashboard.html", plans=plans)


# ----------------------
# Templates (public)
# ----------------------
@main.route("/templates")
def templates():
    templates = Plan.query.filter_by(is_template=True).order_by(Plan.id.desc()).all()
    return render_template("templates.html", templates=templates)

@main.route("/templates/<int:template_id>")
def template_view(template_id):
    template = Plan.query.get_or_404(template_id)
    return render_template("template-view.html", template=template)

@main.route("/templates/<int:template_id>/copy", methods=["POST"])
def template_copy(template_id):
    if not require_login():
        return redirect(url_for("main.login"))
    original = Plan.query.get_or_404(template_id)
    user_id = session["user_id"]
    copy = Plan(
        title=original.title + " (copy)",
        description=original.description,
        start_date=original.start_date,
        end_date=original.end_date,
        is_template=False,
        user_id=user_id
    )
    db.session.add(copy)
    db.session.commit()
    return redirect(url_for("main.dashboard"))


# ----------------------
# Plan CRUD
# ----------------------
@main.route("/plan/new", methods=["GET", "POST"])
@main.route("/plan/<int:plan_id>/edit", methods=["GET", "POST"])
def plan_edit(plan_id=None):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = None
    if plan_id:
        plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    if request.method == "POST":
        from datetime import date
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        end_str = request.form.get("end_date", "")
        end_date = date.fromisoformat(end_str) if end_str else None
        if not title:
            return render_template("plan-edit.html", plan=plan, error="Title is required.")
        if plan:
            plan.title = title
            plan.description = description
            plan.end_date = end_date
        else:
            plan = Plan(title=title, description=description,
                        end_date=end_date, user_id=user_id)
            db.session.add(plan)
        db.session.commit()
        return redirect(url_for("main.plan_view", plan_id=plan.id))
    return render_template("plan-edit.html", plan=plan)

@main.route("/plan/<int:plan_id>")
def plan_view(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    return render_template("plan-view.html", plan=plan)

@main.route("/plan/<int:plan_id>/delete", methods=["POST"])
def plan_delete(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return redirect(url_for("main.dashboard"))

@main.route("/plan/<int:plan_id>/share", methods=["POST"])
def plan_share(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    plan.is_template = not plan.is_template
    db.session.commit()
    return redirect(url_for("main.plan_view", plan_id=plan.id))


# ----------------------
# Session CRUD
# ----------------------
@main.route("/plan/<int:plan_id>/session/new", methods=["POST"])
def session_create(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    title = request.form.get("title", "").strip()
    if title:
        new_session = Session(title=title, plan_id=plan.id)
        db.session.add(new_session)
        db.session.commit()
        return redirect(url_for("main.session_edit", plan_id=plan.id, session_id=new_session.id))
    return redirect(url_for("main.plan_view", plan_id=plan.id))

@main.route("/plan/<int:plan_id>/session/<int:session_id>/edit", methods=["GET", "POST"])
def session_edit(plan_id, session_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    session_obj = Session.query.filter_by(id=session_id, plan_id=plan.id).first_or_404()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        status = request.form.get("status", "notstarted")
        notes = request.form.get("notes", "").strip()
        if not title:
            return render_template("session-edit.html", plan=plan, session_obj=session_obj, error="Title is required.")
        session_obj.title = title
        session_obj.status = status
        db.session.commit()
        return redirect(url_for("main.plan_view", plan_id=plan.id))
    return render_template("session-edit.html", plan=plan, session_obj=session_obj)

@main.route("/plan/<int:plan_id>/session/<int:session_id>/status", methods=["POST"])
def session_status(plan_id, session_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    s = Session.query.filter_by(id=session_id, plan_id=plan.id).first_or_404()
    s.status = request.form.get("status", "notstarted")
    db.session.commit()
    return redirect(url_for("main.plan_view", plan_id=plan.id))

@main.route("/plan/<int:plan_id>/session/<int:session_id>/delete", methods=["POST"])
def session_delete(plan_id, session_id):
    if not require_login():
        return redirect(url_for("main.login"))
    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    s = Session.query.filter_by(id=session_id, plan_id=plan.id).first_or_404()
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("main.plan_view", plan_id=plan.id))