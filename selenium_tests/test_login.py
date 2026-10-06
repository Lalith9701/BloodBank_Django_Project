import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_login_page_renders(driver, base_url):
    """TC-AUTO-001: Verify Login Page loads with correct UI elements."""
    driver.get(f"{base_url}/")
    assert "Login" in driver.title
    
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    assert username_input.is_displayed()
    assert password_input.is_displayed()
    assert submit_btn.is_displayed()

def test_login_invalid_credentials(driver, base_url):
    """TC-AUTO-002: Verify error message for invalid login credentials."""
    driver.get(f"{base_url}/")
    
    driver.find_element(By.ID, "username").send_keys("9999999999")
    driver.find_element(By.ID, "password").send_keys("WrongPass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    error_banner = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger"))
    )
    assert "Invalid credentials" in error_banner.text

def test_login_empty_fields_validation(driver, base_url):
    """TC-AUTO-003: Verify browser required field validation on empty login."""
    driver.get(f"{base_url}/")
    
    username_input = driver.find_element(By.ID, "username")
    required_attr = username_input.get_attribute("required")
    assert required_attr is not None or required_attr == "true"

def test_login_forgot_password_navigation(driver, base_url):
    """TC-AUTO-004: Verify navigation to Forgot Password (Security Question Lookup) page."""
    driver.get(f"{base_url}/")
    
    forgot_link = driver.find_element(By.XPATH, "//a[contains(@href, 'forgot-password')]")
    forgot_link.click()
    
    assert "forgot-password" in driver.current_url
