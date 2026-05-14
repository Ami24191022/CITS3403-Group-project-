# Study Planner

This is a simple study planner web app built with Flask.

---

## Features

* User sign up, log in, and log out
* Create, view, edit, and delete study plans
* Dashboard showing a user's saved plans
* Public templates gallery
* Copy public templates into personal plans
* Responsive interface using Bootstrap 5

---

## How to run

1. Clone the repository

```bash
git clone https://github.com/Ami24191022/CITS3403-Group-project-.git
cd CITS3403-Group-project-
```

2. Create a virtual environment

```bash
python3 -m venv .venv
```

3. Activate the virtual environment

Mac:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

4. Install the required packages

```bash
pip install -r requirements.txt
```

5. Run the app

```bash
python run.py
```

6. Open in your browser:
   http://127.0.0.1:5000

---

## If something doesn’t work

* If you see a "TemplateNotFound" error, check that all HTML files are inside the `app/templates/` folder
* If port 5000 is already in use, stop the process using it or change the port in `run.py`

---

## Notes

* The app uses SQLite with SQLAlchemy.
* The database file is created automatically at `instance/app.db`.
* User accounts and study plans are stored in the database.
* The `.venv` folder is ignored in git.
* User A shares plan as template → User B can see it in Templates → User B copies it.

## How to run selenium tests

* Terminal 1: python run.py
* Terminal 2: pytest tests/selenium -q

##　Security
* Passwords are securely stored using Werkzeug password hashing.
* User sessions are protected using Flask SECRET_KEY configuration.
* Authentication is required to access private plans and dashboard pages.
* Users can only edit or delete their own plans and sessions.