import os
from flask import Flask #Flask is the tool/framework used to build websites (without it, I can't create Flask app)
from .models import db #from the models.py file (look in the current app folder) in the same folder, import db 

def create_app(): #create and set up the Flask app

    #store Flask app in app
    #__name__ helps Flask find files like templates and static files in the app folder (Flask needs this to know where your project starts from)
    #use the instance folder (database like app.db) for certain private/local files (exp: database files, secret config files, local settings)
    app = Flask(__name__, instance_relative_config=True)

    #secret key is needed for sessions (login). This key lets Flask safely remember who is logged in.
    #exp: session["user_id"] = user.id (that needs a secret key)
    #when a user logs in, Flask stores something in the browser cookie (the secret key helps Flask check that the cookie was not tampered with)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-later")

    #SQLite = the actual database
    #SQLAlchemy = the Python tool used to talk to the database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db" #tell Flask/SQLAlchemy to use SQLite database and store data in app.db 
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False #do not track every tiny object change internally (uses extra memory, is usually not needed, can create warning messages)

    #connect database to Flask app
    db.init_app(app)

    from .routes import main #import main from routes.py (bring in all the website page routes) [avoid circular imports]
    app.register_blueprint(main) #add all routes from the main Blueprint into this app (connect all pages/routes to the website, so that visiting different pages would work)

    # Create tables (simple uni approach)
    with app.app_context():
        db.create_all()

    return app