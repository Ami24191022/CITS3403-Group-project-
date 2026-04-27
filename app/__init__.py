from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Needed for sessions (login)
    app.config["SECRET_KEY"] = "dev-secret-change-later"

    # SQLite database stored in instance/app.db
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Init SQLAlchemy
    db.init_app(app)

    # Register routes (Blueprint)
    from .routes import main
    app.register_blueprint(main)

    # Create tables (simple uni approach)
    with app.app_context():
        db.create_all()

    return app