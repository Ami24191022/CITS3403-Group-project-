import uuid
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1200,800")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    yield driver
    driver.quit()

#opens the login page, enters a fake email and password, clicks login, then checks for the error message "Invalid email or password" on the page
def test_invalid_login_shows_error_message(driver):
    driver.get(f"{BASE_URL}/login")

    driver.find_element(By.NAME, "email").send_keys("wrong@test.com")
    driver.find_element(By.NAME, "password").send_keys("wrongpassword")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 5).until(
        lambda d: "Invalid email or password" in d.page_source
    )

    assert "Invalid email or password" in driver.page_source

#checks: Invalid signup details are rejected properly.
def test_signup_password_mismatch_shows_error_message(driver):
    driver.get(f"{BASE_URL}/signup")

    driver.find_element(By.NAME, "firstName").send_keys("Test")
    driver.find_element(By.NAME, "lastName").send_keys("User")
    driver.find_element(By.NAME, "email").send_keys(f"test{uuid.uuid4().hex[:8]}@test.com")
    driver.find_element(By.NAME, "password").send_keys("Password123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Different123")

    agree = driver.find_element(By.ID, "agree")
    if not agree.is_selected():
        agree.click()

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 5).until(
        lambda d: "Passwords do not match" in d.page_source
    )

    assert "Passwords do not match" in driver.page_source

#Test dashboard requires login
def test_dashboard_requires_login(driver):
    driver.get(f"{BASE_URL}/dashboard")

    WebDriverWait(driver, 5).until(
        lambda d: "/login" in d.current_url
    )

    assert "/login" in driver.current_url

# Test if logout works
def test_logout_works(driver):
    email = f"logout{uuid.uuid4().hex[:8]}@test.com"

    # Sign up a new user first so we are logged in
    driver.get(f"{BASE_URL}/signup")

    driver.find_element(By.NAME, "firstName").send_keys("Logout")
    driver.find_element(By.NAME, "lastName").send_keys("Test")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys("Password123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Password123")

    agree = driver.find_element(By.ID, "agree")
    if not agree.is_selected():
        agree.click()

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # After signup, user should be sent to dashboard
    WebDriverWait(driver, 5).until(
        lambda d: "/dashboard" in d.current_url
    )

    assert "/dashboard" in driver.current_url

    # Now log out
    driver.get(f"{BASE_URL}/logout")

    # After logout, dashboard should no longer be accessible
    driver.get(f"{BASE_URL}/dashboard")

    WebDriverWait(driver, 5).until(
        lambda d: "/login" in d.current_url
    )

    assert "/login" in driver.current_url