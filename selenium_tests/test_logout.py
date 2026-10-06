import pytest
from selenium.webdriver.common.by import By

def test_unauthenticated_logout_redirect(driver, base_url):
    """TC-AUTO-016: Verify accessing logout route redirects cleanly to login page."""
    driver.get(f"{base_url}/logout/")
    assert driver.current_url.rstrip("/") == base_url.rstrip("/") or "login" in driver.current_url.lower() or "Login" in driver.title
