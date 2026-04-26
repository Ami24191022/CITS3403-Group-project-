# Study Planner

This is a simple study planner web app built with Flask.

## How to run

1. Clone the repository

```bash
git clone https://github.com/yourname/your-repo-name.git
cd your-repo-name
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

* The app currently uses dummy data to render pages
* The `.venv` folder is ignored in git
