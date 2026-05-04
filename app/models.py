from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Signup / login
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Optional display fields
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    plans = db.relationship(
        "Plan",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def username(self):
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.email.split("@")[0]


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    is_template = db.Column(db.Boolean, default=False, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    sessions = db.relationship(
        "Session",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def weeks(self):
        if not self.start_date or not self.end_date:
            return None

        days = (self.end_date - self.start_date).days + 1
        if days <= 0:
            return None

        return max(1, (days + 6) // 7)


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    session_type = db.Column(db.String(50), default="lecture", nullable=False)

    status = db.Column(
        db.String(50),
        default="notstarted",
        nullable=False
    )

    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Stored as JSON string
    checklist = db.Column(db.Text, nullable=True)

    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )