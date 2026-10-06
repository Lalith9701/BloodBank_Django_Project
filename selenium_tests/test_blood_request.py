import pytest
from selenium.webdriver.common.by import By

def test_unauthenticated_blood_request_access(driver, base_url):
    """TC-AUTO-010: Verify unauthenticated user accessing request-blood page is redirected to login."""
    driver.get(f"{base_url}/requests/request-blood/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title

def test_unauthenticated_my_requests_access(driver, base_url):
    """TC-AUTO-011: Verify unauthenticated user accessing my-requests page is redirected to login."""
    driver.get(f"{base_url}/requests/my-requests/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title
