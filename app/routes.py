from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Plan

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
    if require_login():
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
            return render_template("signup.html", error="Email already registered.")

        # （scrypt → pbkdf2）
        user = User(
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if require_login():
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
    templates = Plan.query.filter_by(is_template=True).order_by(Plan.id.desc()).all()
    return render_template("templates.html", templates=templates)


# ----------------------
# PLAN CRUD
# ----------------------

# CREATE
@main.route("/plans/new", methods=["GET", "POST"])
def new_plan():
    if not require_login():
        return redirect(url_for("main.login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            return render_template("plan-edit.html", error="Title is required.")

        plan = Plan(
            title=title,
            description=description,
            user_id=session["user_id"],
            is_template=False
        )

        db.session.add(plan)
        db.session.commit()

        return redirect(url_for("main.dashboard"))

    return render_template("plan-edit.html")


# READ
@main.route("/plans/<int:plan_id>")
def view_plan(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != session["user_id"]:
        return redirect(url_for("main.dashboard"))

    return render_template("plan-view.html", plan=plan)


# UPDATE
@main.route("/plans/<int:plan_id>/edit", methods=["GET", "POST"])
def edit_plan(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != session["user_id"]:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        plan.title = request.form.get("title")
        plan.description = request.form.get("description")

        db.session.commit()
        return redirect(url_for("main.view_plan", plan_id=plan.id))

    return render_template("plan-edit.html", plan=plan)


# DELETE
@main.route("/plans/<int:plan_id>/delete", methods=["POST"])
def delete_plan(plan_id):
    if not require_login():
        return redirect(url_for("main.login"))

    plan = Plan.query.get_or_404(plan_id)

    if plan.user_id != session["user_id"]:
        return redirect(url_for("main.dashboard"))

    db.session.delete(plan)
    db.session.commit()

    return redirect(url_for("main.dashboard"))