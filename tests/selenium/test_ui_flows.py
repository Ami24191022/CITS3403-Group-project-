import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # enable later if you want
    options.add_argument("--window-size=1200,800")
    d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield d
    d.quit()

def test_login_invalid_shows_error(driver):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.NAME, "email").send_keys("wrong@test.com")
    driver.find_element(By.NAME, "password").send_keys("wrongpass")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(0.5)
    assert "Invalid email or password" in driver.page_source

def signup_user(driver, email):
    driver.get(f"{BASE_URL}/signup")

    # Fill required fields (adjust names if yours differ)
    driver.find_element(By.NAME, "firstName").send_keys("Test")
    driver.find_element(By.NAME, "lastName").send_keys("User")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys("Pass1234")
    driver.find_element(By.NAME, "confirmPassword").send_keys("Pass1234")

    # Tick "agree" checkbox if present/required
    try:
        agree = driver.find_element(By.ID, "agree")
        if not agree.is_selected():
            agree.click()
    except Exception:
        pass  # if your form doesn't have it, ignore

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait until we either reach dashboard OR see an error on signup page
    WebDriverWait(driver, 5).until(
        lambda d: "/dashboard" in d.current_url or "/signup" in d.current_url
    )

def test_signup_redirects_to_dashboard(driver):
    email = f"user{int(time.time())}@test.com"
    signup_user(driver, email)
    assert "/dashboard" in driver.current_url

def test_create_plan_appears_on_dashboard(driver):
    email = f"user{int(time.time())}@test.com"
    signup_user(driver, email)
    assert "/dashboard" in driver.current_url

    # Go create plan
    driver.get(f"{BASE_URL}/plan/new")

    # Confirm we didn't get redirected to login
    assert "/login" not in driver.current_url

    # Wait for title field to exist (plan form loaded)
    title_input = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    title_input.send_keys("Selenium Plan")

    driver.find_element(By.NAME, "description").send_keys("Created by selenium")

    # Your plan_edit.html uses buttons like form="planForm"
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[form='planForm']").click()

    # Go back to dashboard and verify plan appears
    driver.get(f"{BASE_URL}/dashboard")
    assert "Selenium Plan" in driver.page_source