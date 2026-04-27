from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Plan

main = Blueprint("main", __name__)

# --- Helper: simple login-required check (minimal version) ---
def require_login():
    return "user_id" in session

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")

        # Basic validation
        if not email or not password:
            return render_template("signup.html", error="Email and password are required.")
        if password != confirm:
            return render_template("signup.html", error="Passwords do not match.")

        # Check if user exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template("signup.html", error="This email is already registered. Please log in.")

        # Create user
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        # Log them in
        session["user_id"] = user.id
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html")

@main.route("/login", methods=["GET", "POST"])
def login():
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

@main.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("main.login"))

    user_id = session["user_id"]

    # Real DB plans (not dummy)
    plans = Plan.query.filter_by(user_id=user_id).order_by(Plan.id.desc()).all()

    return render_template("dashboard.html", plans=plans)

@main.route("/templates")
def templates():
    # Public templates (from all users)
    templates = Plan.query.filter_by(is_template=True).order_by(Plan.id.desc()).all()
    return render_template("templates.html", templates=templates)