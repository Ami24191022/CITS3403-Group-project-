"""
Selenium Tests for Study Planner
=================================
Requirements:
    pip install selenium webdriver-manager pytest

Run:
    python -m pytest tests/selenium/test_ui_flows.py -v

Make sure Flask is running first:
    python run.py
"""

import time
import uuid
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:5000"
WAIT = 10  # seconds


# ──────────────────────────────────────────────
# Driver fixture
# ──────────────────────────────────────────────

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    # Uncomment the line below to run without a visible browser window:
    # options.add_argument("--headless")
    d = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    d.implicitly_wait(WAIT)
    yield d
    d.quit()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def dismiss_any_alert(driver):
    """
    Dismiss a confirm() / alert dialog if one is open.
    Safe to call even when no alert is present.
    """
    try:
        alert = driver.switch_to.alert
        alert.dismiss()
    except NoAlertPresentException:
        pass


def js_click(driver, element):
    """
    Click an element via JavaScript.
    Avoids issues where another element overlaps the button.
    """
    driver.execute_script("arguments[0].click();", element)


def signup_user(driver, email, password="Password1"):
    """
    Sign up a brand-new account and wait until the dashboard loads.
    Uses JS clicks to avoid overlay/intercept issues.
    """
    driver.get(f"{BASE_URL}/signup")

    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.NAME, "firstName"))
    ).send_keys("Test")

    driver.find_element(By.NAME, "lastName").send_keys("User")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "confirmPassword").send_keys(password)

    # JS click the checkbox — avoids "element not interactable" errors
    agree = driver.find_element(By.ID, "agree")
    js_click(driver, agree)

    # JS click the submit button — avoids overlay intercept errors
    submit = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )
    js_click(driver, submit)

    WebDriverWait(driver, WAIT).until(
        lambda d: "/dashboard" in d.current_url
    )


def create_plan(driver, title="Test Plan", description="Test description"):
    """
    Create a new plan via the UI.
    After saving, lands on plan_view (/plan/<id>).
    """
    driver.get(f"{BASE_URL}/plan/new")

    title_input = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    title_input.clear()
    title_input.send_keys(title)

    desc = driver.find_element(By.NAME, "description")
    desc.clear()
    desc.send_keys(description)

    # Target the submit button that belongs to planForm specifically.
    # In plan/new there is only one submit button, so this is safe here,
    # but using the form attribute selector is more robust.
    submit = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[type='submit'][form='planForm']")
        )
    )
    js_click(driver, submit)

    # After save, Flask redirects to /plan/<id>
    # We wait for the URL to contain /plan/ AND not contain /new or /edit
    WebDriverWait(driver, WAIT).until(
        lambda d: "/plan/" in d.current_url
                  and "/new" not in d.current_url
                  and "/edit" not in d.current_url
    )


# ──────────────────────────────────────────────
# Test 1 — Invalid login shows error message
# ──────────────────────────────────────────────

def test_login_invalid_shows_error_message(driver):
    """
    Logging in with a non-existent account shows an error on the login page.
    """
    driver.get(f"{BASE_URL}/login")

    driver.find_element(By.NAME, "email").send_keys("nobody@nowhere.com")
    driver.find_element(By.NAME, "password").send_keys("WrongPass99")

    submit = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )
    js_click(driver, submit)

    WebDriverWait(driver, WAIT).until(
        lambda d: "Invalid email or password" in d.page_source
    )
    assert "Invalid email or password" in driver.page_source, \
        "Expected error message for invalid login"


# ──────────────────────────────────────────────
# Test 2 — Signup with mismatched passwords
# ──────────────────────────────────────────────

def test_signup_password_mismatch_shows_error(driver):
    """
    Submitting the signup form with mismatched passwords shows an error
    and does NOT redirect to the dashboard.
    """
    driver.get(f"{BASE_URL}/signup")

    driver.find_element(By.NAME, "firstName").send_keys("Test")
    driver.find_element(By.NAME, "lastName").send_keys("User")
    driver.find_element(By.NAME, "email").send_keys(
        f"mismatch{uuid.uuid4().hex[:6]}@test.com"
    )
    driver.find_element(By.NAME, "password").send_keys("Password1")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Different9")

    agree = driver.find_element(By.ID, "agree")
    js_click(driver, agree)

    submit = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )
    js_click(driver, submit)

    # JS validation runs client-side, so the page stays at /signup
    time.sleep(1)
    assert "/signup" in driver.current_url, \
        "Expected to stay on /signup after password mismatch"
    assert "dashboard" not in driver.current_url, \
        "Should NOT redirect to dashboard on mismatch"


# ──────────────────────────────────────────────
# Test 3 — Dashboard requires login
# ──────────────────────────────────────────────

def test_dashboard_requires_login(driver):
    """
    Visiting /dashboard while logged out redirects to /login.
    """
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, WAIT).until(
        lambda d: "/login" in d.current_url
    )
    assert "/login" in driver.current_url, \
        "Expected redirect to /login when visiting /dashboard unauthenticated"


# ──────────────────────────────────────────────
# Test 4 — Logout works
# ──────────────────────────────────────────────

def test_logout_works(driver):
    """
    After logging out, visiting /dashboard redirects to /login.
    """
    email = f"logout{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    assert "/dashboard" in driver.current_url, \
        "Expected to be on dashboard after signup"

    driver.get(f"{BASE_URL}/logout")

    # After logout, /dashboard should redirect to /login
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, WAIT).until(
        lambda d: "/login" in d.current_url
    )
    assert "/login" in driver.current_url, \
        "Expected redirect to /login after logout"


# ──────────────────────────────────────────────
# Test 5 — Create plan appears on dashboard
# ──────────────────────────────────────────────

def test_create_plan_appears_on_dashboard(driver):
    """
    A logged-in user can create a plan; it appears on the dashboard.
    """
    email = f"create{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    plan_title = f"Selenium Plan {uuid.uuid4().hex[:6]}"
    create_plan(driver, title=plan_title)

    # After create_plan(), we're on /plan/<id>
    # Check the title shows on the plan view page
    body = driver.find_element(By.TAG_NAME, "body").text
    assert plan_title in body, \
        f"Expected '{plan_title}' on plan view page after creation"

    # Go to dashboard and confirm it's listed there too
    driver.get(f"{BASE_URL}/dashboard")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "planList"))
    )
    body = driver.find_element(By.TAG_NAME, "body").text
    assert plan_title in body, \
        f"Expected '{plan_title}' to appear on dashboard"


# ──────────────────────────────────────────────
# Test 6 — Edit plan title is saved
# ──────────────────────────────────────────────

def test_edit_plan_title_is_saved(driver):
    """
    A user can edit a plan's title and the updated title is shown after save.
    """
    email = f"edit{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    original_title = f"Original {uuid.uuid4().hex[:6]}"
    create_plan(driver, title=original_title)

    # We're now on /plan/<id> — click Edit Plan
    edit_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Edit Plan"))
    )
    js_click(driver, edit_btn)

    WebDriverWait(driver, WAIT).until(
        lambda d: "/edit" in d.current_url
    )

    new_title = f"Edited {uuid.uuid4().hex[:6]}"
    title_input = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    title_input.clear()
    title_input.send_keys(new_title)

    # FIX: target the Save button by its form attribute to avoid
    # accidentally clicking the Delete button's submit, which also
    # matches the generic "button[type='submit']" selector.
    save_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[type='submit'][form='planForm']")
        )
    )
    js_click(driver, save_btn)

    # Dismiss any stray confirm() dialogs (e.g. delete button proximity)
    dismiss_any_alert(driver)

    # Wait to land back on plan_view
    WebDriverWait(driver, WAIT).until(
        lambda d: "/plan/" in d.current_url and "/edit" not in d.current_url
    )

    body = driver.find_element(By.TAG_NAME, "body").text
    assert new_title in body, \
        f"Expected updated title '{new_title}' after edit"


# ──────────────────────────────────────────────
# Test 7 — Delete plan removes it from dashboard
# ──────────────────────────────────────────────

def test_delete_plan(driver):
    """
    Deleting a plan removes it from the dashboard.
    """
    email = f"del{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    plan_title = f"ToDelete {uuid.uuid4().hex[:6]}"
    create_plan(driver, title=plan_title)

    # Go to edit page where the Delete button lives
    edit_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Edit Plan"))
    )
    js_click(driver, edit_btn)

    WebDriverWait(driver, WAIT).until(
        lambda d: "/edit" in d.current_url
    )

    # Override confirm() so it returns true automatically
    driver.execute_script("window.confirm = function() { return true; }")

    delete_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.btn-outline-danger")
        )
    )
    js_click(driver, delete_btn)

    # After delete, Flask redirects to /dashboard
    WebDriverWait(driver, WAIT).until(
        lambda d: "/dashboard" in d.current_url
    )

    body = driver.find_element(By.TAG_NAME, "body").text
    assert plan_title not in body, \
        f"Expected deleted plan '{plan_title}' to be gone from dashboard"


# ──────────────────────────────────────────────
# Test 8 — Add session to plan
# ──────────────────────────────────────────────

def test_add_session_to_plan(driver):
    """
    A user can add a session to a plan; it appears on the plan view.
    """
    email = f"sess{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)
    create_plan(driver, title="Plan With Sessions")

    # Click "Add Session" — it's a button inside a form
    add_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.session-add-card")
        )
    )
    js_click(driver, add_btn)

    # Dismiss any alert that opens (shouldn't happen, but safety net)
    dismiss_any_alert(driver)

    # Should land on session_edit page
    WebDriverWait(driver, WAIT).until(
        lambda d: "/session/" in d.current_url
    )

    session_title = f"Session {uuid.uuid4().hex[:6]}"
    title_input = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    title_input.clear()
    title_input.send_keys(session_title)

    # FIX: target the Save button by its form attribute to avoid
    # accidentally clicking the Delete button's submit, which also
    # matches the generic "button[type='submit']" selector.
    save_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[type='submit'][form='sessionForm']")
        )
    )
    js_click(driver, save_btn)

    # Dismiss any confirm dialog that appears
    dismiss_any_alert(driver)

    # Should go back to plan_view
    WebDriverWait(driver, WAIT).until(
        lambda d: "/plan/" in d.current_url and "/session/" not in d.current_url
    )

    body = driver.find_element(By.TAG_NAME, "body").text
    assert session_title in body, \
        f"Expected session title '{session_title}' on plan view"


# ──────────────────────────────────────────────
# Test 9 — Dashboard search filter
# ──────────────────────────────────────────────

def test_dashboard_search_filters_plans(driver):
    """
    Typing in the dashboard search box filters plan cards in real time.
    """
    email = f"search{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    unique_word = f"UniqueXYZ{uuid.uuid4().hex[:4]}"
    create_plan(driver, title=f"{unique_word} Plan")
    create_plan(driver, title="Something Completely Different")

    # Now explicitly navigate to the dashboard
    driver.get(f"{BASE_URL}/dashboard")

    search_box = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "search"))
    )
    search_box.clear()
    search_box.send_keys(unique_word)

    time.sleep(0.6)  # Let the JS filter run

    visible_cards = [
        c for c in driver.find_elements(By.CSS_SELECTOR, ".plan-card")
        if c.is_displayed()
    ]
    assert len(visible_cards) >= 1, \
        "Expected at least one plan card visible after search"

    titles = " ".join(
        c.find_element(By.TAG_NAME, "h2").text for c in visible_cards
    )
    assert unique_word in titles, \
        f"Expected '{unique_word}' in visible plan titles, got: '{titles}'"


# ──────────────────────────────────────────────
# Test 10 — Share plan as template toggles button
# ──────────────────────────────────────────────

def test_share_plan_as_template(driver):
    """
    Clicking 'Share as Template' toggles the button to 'Unshare'.
    """
    email = f"share{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)
    create_plan(driver, title="Template Share Test")

    share_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.btn-outline-success")
        )
    )
    assert "Share" in share_btn.text, \
        f"Expected 'Share as Template' button, got: '{share_btn.text}'"

    js_click(driver, share_btn)

    # Wait for page reload back to plan_view
    WebDriverWait(driver, WAIT).until(
        lambda d: "/plan/" in d.current_url and "/edit" not in d.current_url
    )

    unshare_btn = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.btn-outline-success")
        )
    )
    assert "Unshare" in unshare_btn.text, \
        f"Expected 'Unshare' button after sharing, got: '{unshare_btn.text}'"


# ──────────────────────────────────────────────
# Test 11 — Templates page is public
# ──────────────────────────────────────────────

def test_templates_page_accessible_without_login(driver):
    """
    The /templates page loads for anyone, no login required.
    """
    driver.get(f"{BASE_URL}/templates")
    heading = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
    )
    assert "Template" in heading.text, \
        f"Expected Templates heading, got: '{heading.text}'"


# ──────────────────────────────────────────────
# Test 12 — Successful signup
# ──────────────────────────────────────────────

def test_signup_success(driver):
    """
    A new user can sign up with valid details and reach the dashboard.
    """
    email = f"new{uuid.uuid4().hex[:6]}@test.com"
    signup_user(driver, email)

    assert "/dashboard" in driver.current_url, \
        "Expected to land on /dashboard after signup"

    nav = driver.find_element(By.CSS_SELECTOR, "nav").get_attribute("innerHTML")
    assert "Log out" in nav, \
        "Expected 'Log out' in navbar after signup"