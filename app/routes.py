from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/login")
def login():
    return render_template("login.html")

@main.route("/signup")
def signup():
    return render_template("signup.html")

@main.route("/dashboard")
def dashboard():
    # Dummy data (optional but nice — helps checkpoint 3)
    plans = [
        {"title": "CITS3403 Checkpoint Sprint", "status": "Active"},
        {"title": "Mid-Sem Revision", "status": "Upcoming"},
    ]
    return render_template("dashboard.html", plans=plans)

@main.route("/templates")
def templates():
    # Dummy data (optional)
    templates = [
        {"title": "Exam Week Daily Past Papers", "author": "Ami", "weeks": 1},
        {"title": "Balanced Weekly Routine", "author": "Jon", "weeks": 4},
    ]
    return render_template("templates.html", templates=templates)

@main.route("/plan/view")
def plan_view():
    return render_template("plan-view.html")

@main.route("/plan/edit")
def plan_edit():
    return render_template("plan-edit.html")