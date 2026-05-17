import uuid
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    d = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    d.implicitly_wait(10)
    yield d
    d.quit()


def js_click(driver, element):
    """Click via JavaScript to avoid element intercept errors."""
    driver.execute_script("arguments[0].click();", element)


# Test 1 — invalid login shows error
def test_invalid_login_shows_error_message(driver):
    driver.get(f"{BASE_URL}/login")

    driver.find_element(By.NAME, "email").send_keys("wrong@test.com")
    driver.find_element(By.NAME, "password").send_keys("wrongpassword")

    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)

    WebDriverWait(driver, 10).until(
        lambda d: "Invalid email or password" in d.page_source
    )
    assert "Invalid email or password" in driver.page_source


# Test 2 — mismatched passwords shows error
def test_signup_password_mismatch_shows_error_message(driver):
    driver.get(f"{BASE_URL}/signup")

    driver.find_element(By.NAME, "firstName").send_keys("Test")
    driver.find_element(By.NAME, "lastName").send_keys("User")
    driver.find_element(By.NAME, "email").send_keys(
        f"test{uuid.uuid4().hex[:8]}@test.com"
    )
    driver.find_element(By.NAME, "password").send_keys("Password123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Different123")

    # JS click the checkbox to avoid intercept errors
    agree = driver.find_element(By.ID, "agree")
    js_click(driver, agree)

    # JS click submit to avoid intercept errors
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)

    WebDriverWait(driver, 10).until(
        lambda d: "Passwords do not match" in d.page_source
    )
    assert "Passwords do not match" in driver.page_source


# Test 3 — dashboard requires login
def test_dashboard_requires_login(driver):
    driver.get(f"{BASE_URL}/dashboard")

    WebDriverWait(driver, 10).until(
        lambda d: "/login" in d.current_url
    )
    assert "/login" in driver.current_url


# Test 4 — logout works
def test_logout_works(driver):
    email = f"logout{uuid.uuid4().hex[:8]}@test.com"

    driver.get(f"{BASE_URL}/signup")

    driver.find_element(By.NAME, "firstName").send_keys("Logout")
    driver.find_element(By.NAME, "lastName").send_keys("Test")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys("Password123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Password123")

    # JS click the checkbox and submit
    agree = driver.find_element(By.ID, "agree")
    js_click(driver, agree)

    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    js_click(driver, submit)

    WebDriverWait(driver, 10).until(
        lambda d: "/dashboard" in d.current_url
    )
    assert "/dashboard" in driver.current_url

    driver.get(f"{BASE_URL}/logout")
    driver.get(f"{BASE_URL}/dashboard")

    WebDriverWait(driver, 10).until(
        lambda d: "/login" in d.current_url
    )
    assert "/login" in driver.current_url