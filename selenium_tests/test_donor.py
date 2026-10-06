import pytest
from selenium.webdriver.common.by import By

def test_donor_search_page_loads(driver, base_url):
    """TC-AUTO-008: Verify Donor Search page renders search filters."""
    driver.get(f"{base_url}/donors/search/")
    assert "Search" in driver.title or "Donor" in driver.title
    
    blood_select = driver.find_element(By.NAME, "blood_group")
    city_input = driver.find_element(By.NAME, "city")
    pincode_input = driver.find_element(By.NAME, "pincode")
    
    assert blood_select.is_displayed()
    assert city_input.is_displayed()
    assert pincode_input.is_displayed()

def test_public_blood_availability_view(driver, base_url):
    """TC-AUTO-009: Verify Public Blood Availability dashboard page renders stock cards."""
    driver.get(f"{base_url}/inventory/availability/")
    assert "Availability" in driver.title or "Blood" in driver.title
    
    header = driver.find_element(By.TAG_NAME, "h1")
    assert "Blood Availability" in header.text
