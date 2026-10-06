# Selenium Automation Testing Suite — Blood Bank Management System

This directory contains the automated end-to-end browser test suite built with **Selenium WebDriver (Python)** and **pytest** for the Blood Bank Management System Django application.

---

## 📁 Directory Structure

```text
selenium_tests/
├── conftest.py              # Pytest fixtures (Headless Chrome WebDriver, Base URL setup)
├── test_login.py            # Automation tests for Login form, invalid credentials, forgot password navigation
├── test_registration.py     # Automation tests for Donor Registration form & password complexity validation
├── test_donor.py            # Automation tests for Donor Search filters & Public Blood Availability dashboard
├── test_blood_request.py    # Automation tests for Blood Request creation & RBAC route protection
├── test_admin.py            # Automation tests for Staff Admin URLs, Health Approvals, & Audit Log security
├── test_logout.py           # Automation tests for Logout workflow & session clearance
└── README.md                # Execution guide & setup instructions
```

---

## 🛠️ Prerequisites & Installation

### 1. Requirements
* Python 3.13.14+
* Google Chrome Browser installed
* Active Django Server running on `http://127.0.0.1:8000`

### 2. Install Required Dependencies
Run the following command to install Selenium, WebDriver Manager, Pytest, and Pytest-HTML report plugin:

```powershell
python -m pip install selenium webdriver-manager pytest pytest-html
```

---

## 🚀 How to Run the Selenium Test Suite

### Step 1: Start the Django Local Development Server
Open a terminal window in the project root folder and start the server:

```powershell
python manage.py runserver
```

*(Ensure the server is accessible at `http://127.0.0.1:8000`)*

### Step 2: Execute All Selenium Tests
In a second terminal window, run pytest pointing to the `selenium_tests/` directory:

```powershell
pytest selenium_tests/ --html=selenium_tests/report.html --self-contained-html
```

### Step 3: Run Specific Test Modules (Optional)
To run an individual test module:

```powershell
# Run only Login Automation Tests
pytest selenium_tests/test_login.py -v

# Run only Registration Automation Tests
pytest selenium_tests/test_registration.py -v

# Run only Admin RBAC Automation Tests
pytest selenium_tests/test_admin.py -v
```

---

## 📊 Viewing Test Reports & Results

After running the command with `--html=selenium_tests/report.html`, open `selenium_tests/report.html` in any web browser to view the interactive test execution summary:

```powershell
# Open HTML test report in default browser (Windows)
start selenium_tests/report.html
```

The HTML report provides:
* Total test execution count
* Pass / Fail status breakdown
* Detailed assertion failure tracebacks (if any)
* Execution time per test case
