from datetime import datetime #work with dates and times
from flask_sqlalchemy import SQLAlchemy #lets python talk to my database

db = SQLAlchemy() #create database object to connect database to Flask app in __init__.py

class User(db.Model): #defines a table called User in my database (each instance of User is one row in the table)
    __tablename__ = "users" #names the table in the database users
    #every user has an ID number
    #primary_key=True means it’s unique and identifies this user
    id = db.Column(db.Integer, primary_key=True)
    #signup / login part
    #email is stored as text (max 255 characters)
    #unique=True: no two users can have the same email
    #nullable=False: email is required
    #index=True: makes searching by email faster
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    #stores the hashed password (never store plain passwords, only hashes for security)
    password_hash = db.Column(db.String(255), nullable=False)
    #optional display fields
    #can be empty
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    #timestamps part
    #automatically stores when the user was created
    #default=datetime.utcnow: automatically sets to the current time
    #nullable=False: cannot be empty
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    plans = db.relationship( #links users to their plans
        "Plan",
        backref="user", #lets a plan know which user it belongs to: plan.user
        lazy=True, #loads the related plans automatically when needed
        cascade="all, delete-orphan" #if a user is deleted, all their plans are also deleted
    )

    @property #python property lets me read an attribute safely (to control what happens when someone reads or changes the value)
    def username(self):
        if self.first_name or self.last_name: #if the user has a first or last name
            return f"{self.first_name or ''} {self.last_name or ''}".strip() #returns "First Last"
        return self.email.split("@")[0] #otherwise, it uses the part of their email before the @

class Plan(db.Model): #defines a plans table (each row is one study plan)
    __tablename__ = "plans"
    #plan id
    id = db.Column(db.Integer, primary_key=True)
    #required name of the plan
    title = db.Column(db.String(200), nullable=False)
    #optional notes
    description = db.Column(db.Text, nullable=True)
    #optional start/end dates for the plan
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    #True if this plan is a public template
    #False if it’s private
    is_template = db.Column(db.Boolean, default=False, nullable=False)
    # priority level for the plan
    priority = db.Column(db.String(20), default="normal", nullable=False)
    #links the plan to a user (users.id)
    #every plan must belong to one user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    #when the plan was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    #automatically updated every time the plan is changed
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    sessions = db.relationship( #each plan can have multiple sessions (like weeks or tasks)
        "Session",
        backref="plan", #plan.sessions gives all sessions belonging to this plan
        lazy=True,
        cascade="all, delete-orphan" #if a plan is deleted, all its sessions are deleted
    )

    @property
    def weeks(self): #computes how many weeks the plan spans
        if not self.start_date or not self.end_date:
            return None
        days = (self.end_date - self.start_date).days + 1
        if days <= 0:
            return None
        #adds 6 days before floor division so partial weeks count as one week
        return max(1, (days + 6) // 7)


class Session(db.Model): #each session is a small part of a plan (like a lecture or a task)
    __tablename__ = "sessions"
    #session id
    id = db.Column(db.Integer, primary_key=True)
    #name of the session
    title = db.Column(db.String(200), nullable=False)
    #type like lecture, lab, etc
    session_type = db.Column(db.String(50), default="lecture", nullable=False)
    #current state (not started, in progress, done)
    status = db.Column(
        db.String(50),
        default="notstarted",
        nullable=False
    )
    #optional date when session is due
    due_date = db.Column(db.Date, nullable=True)
    #optional extra text
    notes = db.Column(db.Text, nullable=True)
    #optional list stored as JSON string (tasks inside the session)
    checklist = db.Column(db.Text, nullable=True)
    #links session to a plan
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    #timestamps part
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )