from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from .models import db, User, Plan

main = Blueprint("main", __name__)

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
            return render_template("signup.html", error="Email and password are required.")
        if password != confirm:
            return render_template("signup.html", error="Passwords do not match.")

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template("signup.html", error="This email is already registered. Please log in.")

        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
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
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user.id
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main.route("/logout")
def logout():
    session.pop("user_id", None)
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
    # Show templates from DB; optionally hide your own when logged in
    q = Plan.query.filter_by(is_template=True)

    if "user_id" in session:
        q = q.filter(Plan.user_id != session["user_id"])

    templates_list = q.order_by(Plan.id.desc()).all()
    return render_template("templates.html", templates=templates_list)


@main.route("/templates/<int:template_id>")
def template_view(template_id):
    template = Plan.query.get_or_404(template_id)
    if not template.is_template:
        abort(404)
    return render_template("template_view.html", template=template)


@main.route("/templates/<int:template_id>/copy", methods=["POST"])
def template_copy(template_id):
    if not require_login():
        return redirect(url_for("main.login"))

    original = Plan.query.get_or_404(template_id)
    if not original.is_template:
        abort(404)

    user_id = session["user_id"]

    copy = Plan(
        title=f"{original.title} (copy)",
        description=original.description,
        start_date=original.start_date,
        end_date=original.end_date,
        is_template=False,
        user_id=user_id,
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
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        start_str = request.form.get("start_date", "")
        end_str = request.form.get("end_date", "")

        start_date = date.fromisoformat(start_str) if start_str else None
        end_date = date.fromisoformat(end_str) if end_str else None

        is_template = request.form.get("is_template") == "on"

        if not title:
            return render_template("plan_edit.html", plan=plan, error="Title is required.")

        if plan:
            plan.title = title
            plan.description = description
            plan.start_date = start_date
            plan.end_date = end_date
            plan.is_template = is_template
        else:
            plan = Plan(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                is_template=is_template,
                user_id=user_id,
            )
            db.session.add(plan)

        db.session.commit()
        return redirect(url_for("main.plan_view", plan_id=plan.id))

    return render_template("plan_edit.html", plan=plan)


@main.route("/plan/<int:plan_id>")
def plan_view(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    return render_template("plan_view.html", plan=plan)


@main.route("/plan/<int:plan_id>/delete", methods=["POST"])
def plan_delete(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    plan = Plan.query.filter_by(id=plan_id, user_id=user_id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return redirect(url_for("main.dashboard"))