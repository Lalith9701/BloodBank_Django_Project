import pytest
from selenium.webdriver.common.by import By

def test_unauthenticated_admin_health_approvals(driver, base_url):
    """TC-AUTO-012: Verify unauthenticated user accessing admin health approvals is redirected to login (root with next parameter)."""
    driver.get(f"{base_url}/admin-health-approvals/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title

def test_unauthenticated_admin_audit_log(driver, base_url):
    """TC-AUTO-013: Verify unauthenticated user accessing audit log is redirected to login."""
    driver.get(f"{base_url}/admin-audit-log/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title

def test_unauthenticated_agent_dashboard(driver, base_url):
    """TC-AUTO-014: Verify unauthenticated user accessing AI agent dashboard is redirected to login."""
    driver.get(f"{base_url}/agents/dashboard/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title

def test_unauthenticated_admin_all_donors(driver, base_url):
    """TC-AUTO-015: Verify unauthenticated user accessing all donors list is redirected to login."""
    driver.get(f"{base_url}/admin-all-donors/")
    assert "next=" in driver.current_url or "login" in driver.current_url.lower() or "Login" in driver.title
