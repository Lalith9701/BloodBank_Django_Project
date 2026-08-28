# 🩸 Blood Bank Management System (Full-Stack Django Project)

A complete, enterprise-grade Blood Bank Management Application built with **Django 6.0**, **Python 3.13**, and **Bootstrap 5.3**, featuring complete inventory management, donor health approvals, role-based workflows, in-app notifications, and an **Autonomous AI Agent Engine**.

---

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Key Modules & Features](#-key-modules--features)
  - [1. Authentication & Security](#1-authentication--security-accounts)
  - [2. Donor Management](#2-donor-management-donors)
  - [3. Inventory & Stock Tracking](#3-inventory--stock-tracking-inventory)
  - [4. Blood Requests & Donations](#4-blood-requests--donations-requests_app)
  - [5. AI Agent & Verification Engine](#5-ai-agent--verification-engine-agents)
  - [6. Notifications & Ratings](#6-notifications--ratings-notifications--ratings)
- [System Architecture & Roles](#-system-architecture--roles)
- [Technology Stack](#-technology-stack)
- [Quick Start Guide](#-quick-start-guide)
- [Demo Credentials](#-demo-credentials)
- [Testing](#-testing)
- [Project Directory Map](#-project-directory-map)

---

## 🌟 Project Overview

The **Blood Bank Management System** is a robust web platform designed to streamline blood collection, inventory tracking, patient request processing, and donor management. It bridges patients in need with active blood donors while giving blood bank administrators complete real-time visibility over inventory stock, medical approvals, and emergency dispatches.

---

## ✨ Key Modules & Features

### 1. Authentication & Security (`accounts`)
* **Dual Login Options**: Users can log in using either their **Registered Mobile Number** OR **Full Name**.
* **Role-Based Access Control (RBAC)**: Supports three distinct user roles: `ADMIN`, `DONOR`, and `REQUESTER`.
* **Security Profile & Question-Based Password Reset**: Users set security questions during registration with PBKDF2 hashed answers.
* **Account Deactivation Guard**: Inactive users are safely restricted and can submit reactivation requests via an embedded contact form on the login page.
* **Audit Logging**: Immutable system audit trail (`AuditLog`) tracking all administrative approvals, rejections, and state changes.


### 2. Donor Management (`donors`)
* **Donor Registration**: Captures blood group, age, gender, weight, address, city, state, pincode, and health history.
* **Medical Certificate & Health Approval**: Donors with medical conditions upload supporting certificates for Admin health review (`ELIGIBLE`, `PENDING`, `REJECTED`).
* **Donor Directory Search**: Search active donors by Blood Group, City, Pincode, State, or Availability.
* **Availability Toggle**: One-click toggle (`Available` / `Unavailable`) on the donor dashboard for donor convenience.
* **90-Day Rest Period Enforcement**: Built-in safety check enforcing a mandatory 90-day recovery wait period between donations.

---

### 3. Inventory & Stock Tracking (`inventory`)
* **All 8 Blood Groups**: Full support for `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`.
* **Real-Time Stock Updates**: Inventory automatically increments upon donor donations and decrements upon blood request approvals.
* **Low Stock Alerts**: Visual warning indicators on the admin dashboard when any blood group stock falls below 5 units.
* **Inventory Management UI**: Add new blood groups or manually update unit quantities.

---

### 4. Blood Requests & Donations (`requests_app`)
* **Patient Blood Request Form**: Requesters submit blood group requirements, required units, urgency levels (`NORMAL`, `URGENT`, `EMERGENCY`), patient details, medical purpose, and doctor prescription documents (JPG/PNG/PDF).
* **Donation Recording**: Donors log their blood donations, automatically updating stock and setting donor recovery availability.
* **Request & Donation History**: Dedicated tracking tables (`My Requests`, `My Donations`) for users.
* **Admin Approval Panel**: Staff interface to inspect patient details, view uploaded doctor prescription files, approve/reject requests with custom rejection reasons, and export data as CSV.

---

### 5. AI Agent & Verification Engine (`agents`)
* **3-Tier AI Verification**: Evaluates new requests across Patient Data (Tier 1), Doctor Prescription Document Upload (Tier 2), and Inventory Stock (Tier 3).
* **Autonomous Auto-Approval**: Automatically approves requests and deducts inventory stock when all verification tiers pass—preventing manual approval delays.
* **Handover to Admin Review**: Flags exact validation warnings in `AgentExecutionLog` and leaves requests `PENDING` for staff review if any verification tier fails.
* **Emergency Match & Dispatch**: Uses ABO/Rh medical compatibility rules (e.g. `O-` universal donor, `AB+` universal recipient) to send targeted alerts to eligible donors during stock shortages or emergency requests.
* **AI Control Center**: Dedicated staff dashboard (`/agents/dashboard/`) featuring live execution metrics and step-by-step reasoning logs.

---

### 6. Notifications & Ratings (`notifications` & `ratings`)
* **In-App Notification Engine**: Real-time notifications with unread badge count in the navigation bar for request approvals, availability updates, and emergency dispatches.
* **Service Ratings & Feedback**: Requesters rate donor response and blood bank service quality (1 to 5 stars) with written feedback.

---

## 👥 System Architecture & Roles

```
                      ┌────────────────────────────────────────┐
                      │    Blood Bank Management System        │
                      └───────────────────┬────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
┌───────────────┐                 ┌───────────────┐                 ┌───────────────┐
│  ADMIN ROLE   │                 │  DONOR ROLE   │                 │REQUESTER ROLE │
├───────────────┤                 ├───────────────┤                 ├───────────────┤
│• System Dash  │                 │• Profile      │                 │• Request Blood│
│• Stock Control│                 │• Availability │                 │• Upload Doc   │
│• Approvals    │                 │• Record Don.  │                 │• Track Status │
│• Health Review│                 │• Alert Inbox  │                 │• Service Rate │
│• Audit Logs   │                 │• Cooldown Check                 │• My Requests  │
│• AI Dashboard │                 └───────────────┘                 └───────────────┘
└───────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology Used |
| :--- | :--- |
| **Backend Framework** | Django 6.0 |
| **Programming Language** | Python 3.13 |
| **Database** | SQLite 3 |
| **Frontend UI** | Bootstrap 5.3 & Bootstrap Icons |
| **Typography** | Inter (Google Fonts) |
| **Authentication** | Django Auth (Custom User Model with Phone / Name Login) |
| **AI Agent Layer** | Custom Python Engine (`agents` app) |
| **Data Export** | CSV Export Engine |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.13 or higher
- Git

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Lalith9701/BloodBank_Django_Project.git
   cd BloodBank_Django_Project
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install django pillow
   ```

4. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Populate 200+ Demo Records (Optional)**:
   ```bash
   python seed_data.py
   ```

6. **Create an Admin Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

8. **Open in Browser**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 Demo Credentials

* **Login Identifier**: Use **Registered Mobile Number** OR **Full Name**
* **Default Password for Seeded Users**: `password123` (works for all seeded donors and requesters)

---

## 🧪 Testing

Run the full Django test suite:
```bash
python manage.py test
```

---

## 📁 Project Directory Map

```
BloodBank_Django_Project/
├── accounts/          # User authentication, RBAC, security questions, audit logs
├── donors/            # Donor profiles, directory search, health eligibility documents
├── inventory/         # BloodGroup model, stock tracking, inventory management
├── requests_app/      # BloodRequest model, prescription uploads, donations
├── agents/            # AI Agent verification, compatibility matrix, execution logs
├── notifications/     # In-app notification engine and context processors
├── ratings/           # Service rating system and feedback models
├── templates/         # 25+ HTML Bootstrap 5 templates
├── static/            # CSS styles and static assets
├── media/             # Uploaded health certificates & doctor prescriptions
├── seed_data.py       # Data seeder script (generates 200+ realistic records)
├── manage.py          # Django management script
└── README.md          # Project documentation
```

---

## 📄 Documentation

* **`project_report.html`**: Complete project documentation report (viewable in browser).
* **`BUGS_FIXED.md`**: Complete summary of all bug fixes and stability enhancements.

---

**Status**: ✅ Production Ready | **Bugs**: 0 | **Tests**: Passing
