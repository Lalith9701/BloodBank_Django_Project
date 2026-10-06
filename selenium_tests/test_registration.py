import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def test_registration_page_renders(driver, base_url):
    """TC-AUTO-005: Verify Registration Page loads with all mandatory input fields."""
    driver.get(f"{base_url}/register/")
    assert "Registration" in driver.title or "Register" in driver.title
    
    assert driver.find_element(By.ID, "full_name").is_displayed()
    assert driver.find_element(By.ID, "email").is_displayed()
    assert driver.find_element(By.ID, "phone").is_displayed()
    assert driver.find_element(By.ID, "password").is_displayed()
    assert driver.find_element(By.ID, "confirm_password").is_displayed()
    assert driver.find_element(By.ID, "blood_group").is_displayed()

def test_registration_weak_password_validation(driver, base_url):
    """TC-AUTO-006: Verify password strength validation blocks simple passwords."""
    driver.get(f"{base_url}/register/")
    
    driver.find_element(By.ID, "full_name").send_keys("Test Donor")
    driver.find_element(By.ID, "email").send_keys("testdonor@example.com")
    driver.find_element(By.ID, "phone").send_keys("9123456789")
    driver.find_element(By.ID, "password").send_keys("simple")
    driver.find_element(By.ID, "confirm_password").send_keys("simple")
    
    # Select required dropdown options
    Select(driver.find_element(By.ID, "blood_group")).select_by_index(1)
    Select(driver.find_element(By.ID, "gender")).select_by_value("Male")
    Select(driver.find_element(By.ID, "security_question")).select_by_index(1)
    
    driver.find_element(By.ID, "age").send_keys("25")
    driver.find_element(By.ID, "weight").send_keys("65")
    driver.find_element(By.ID, "security_answer").send_keys("Answer")
    
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    error_area = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger"))
    )
    assert "Please fix the following errors" in error_area.text or "Be at least 8 characters long" in error_area.text

def test_registration_password_mismatch(driver, base_url):
    """TC-AUTO-007: Verify registration failure when passwords do not match."""
    driver.get(f"{base_url}/register/")
    
    driver.find_element(By.ID, "full_name").send_keys("Test User")
    driver.find_element(By.ID, "email").send_keys("mismatch@example.com")
    driver.find_element(By.ID, "phone").send_keys("9123456788")
    driver.find_element(By.ID, "password").send_keys("Pass@1234")
    driver.find_element(By.ID, "confirm_password").send_keys("Different@1234")
    
    # Select required dropdown options
    Select(driver.find_element(By.ID, "blood_group")).select_by_index(1)
    Select(driver.find_element(By.ID, "gender")).select_by_value("Male")
    Select(driver.find_element(By.ID, "security_question")).select_by_index(1)
    
    driver.find_element(By.ID, "age").send_keys("25")
    driver.find_element(By.ID, "weight").send_keys("65")
    driver.find_element(By.ID, "security_answer").send_keys("Answer")
    
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    error_area = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger"))
    )
    assert "Passwords do not match" in error_area.text or "Please fix the following errors" in error_area.text
