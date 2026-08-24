# 🩸 BloodBank AI — Smart Blood Bank Management System

A full-stack, enterprise-grade Blood Bank Management System built with **Django 6.0**, **Python 3.13**, and **Bootstrap 5.3**, integrated with an **Autonomous Emergency Match & 3-Tier AI Verification Agent**.

---

## 🌟 Overview

**BloodBank AI** transforms traditional blood bank record-keeping into a proactive, life-saving AI platform. Beyond standard blood inventory and donor management, the platform features an **AI Agent Engine** that automatically verifies medical prescriptions, validates patient data, evaluates inventory stock levels, performs ABO/Rh blood compatibility calculations, and dispatches real-time emergency alerts to eligible donors.

---

## ✨ Key Features

### 🤖 Autonomous AI Agent Engine
* **3-Tier Verification**:
  * **Tier 1 (Patient Data Check)**: Validates patient name, 10-digit mobile number, gender, hospital address, and medical purpose.
  * **Tier 2 (Prescription Upload Verification)**: Verifies presence of attached doctor prescription documents (JPG, PNG, PDF).
  * **Tier 3 (Inventory Stock Evaluation)**: Measures available units against required units.
* **Auto-Approval**: Automatically approves requests and deducts stock when all 3 tiers pass—eliminating manual admin approval delays.
* **Admin Handover & Warning Logging**: If any verification tier fails (e.g. missing prescription or invalid phone format), the AI Agent leaves the request as `PENDING` and logs exact warning reasons for staff review.
* **Emergency Dispatch**: When stock shortages occur or urgent/emergency requests are logged, the AI Agent calculates compatible blood groups and dispatches targeted alerts to eligible donors.
* **90-Day Cooldown Enforcement**: Automatically excludes donors who have donated within the last 90 days.

### 👥 Role-Based Access Control
* **Admin / Staff**: System control panel, AI agent decision logs, prescription document inspection, donor health approval, stock management, audit logging.
* **Donors**: Availability toggle (Available/Unavailable), donation history, in-app emergency dispatch alerts, rest period cooldown tracker.
* **Requesters**: Patient details submission form, doctor prescription upload, blood request tracking, ratings and service feedback.

### 📊 Real-Time Admin Dashboard
* Live metric tiles for total donors, requests, stock levels, AI runs, and pending prescriptions.
* Embedded live feed of the 5 most recent AI Agent decision matrices and dispatch outcomes.
* Direct links to inspect doctor prescription uploads for pending requests.

### 🔔 Notification & Audit System
* Instant in-app notification engine alerting users of request approvals, emergency dispatches, and stock updates.
* Immutable `AuditLog` recording all administrative and AI agent actions.
* CSV export for donors and blood requests.

### 🌱 Pre-seeded Demo Dataset (`seed_data.py`)
* Comes with a built-in seeder script generating **200+ realistic records** (160 donors, 40 requesters, historical donations, blood requests, ratings, and AI execution logs).

---

## 🧠 AI Agent Workflow & Decision Matrix

```
[Patient Submits Request + Uploads Doctor Prescription]
                        │
                        ▼
       [🤖 3-TIER AI VERIFICATION ENGINE]
                        │
 ┌──────────────────────┼──────────────────────┐
 │ Tier 1: Patient Info │ Tier 2: Prescription │ Tier 3: Inventory Stock
 │ Valid Name, 10-digit │ Doctor image/PDF     │ Available Units >=
 │ Phone, Address & Purpose file attached      │ Required Units
 └──────────────────────┴──────────────────────┴──────────────────────┘
                        │
            ┌───────────┴───────────┐
            │ ALL TIERS PASSED      │ ANY TIER FAILED
            ▼                       ▼
 ┌───────────────────────┐ ┌──────────────────────────┐
 │ ✅ AUTO-APPROVAL      │ │ ⚠️ HANDOVER TO ADMIN     │
 │ • Status ➔ APPROVED   │ │ • Status stays PENDING   │
 │ • Deducts Stock Units │ │ • AI Logs warning        │
 │ • Notifies Requester  │ │ • Admin reviews and      │
 │ • Logs Audit Entry    │ │   decides on approval    │
 └───────────────────────┘ └──────────────────────────┘
```

### ABO & Rh Medical Compatibility Rules Applied by AI:
* **O- (Universal Donor)**: Can donate to `O-`, `O+`, `A-`, `A+`, `B-`, `B+`, `AB-`, `AB+`.
* **AB+ (Universal Recipient)**: Can receive blood from all blood groups.
* **A+**: Receives from `O-`, `O+`, `A-`, `A+`.
* **B+**: Receives from `O-`, `O+`, `B-`, `B+`.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Django 6.0 |
| **Programming Language** | Python 3.13 |
| **Database** | SQLite 3 (ORM with indexing & constraints) |
| **Frontend Framework** | Bootstrap 5.3 & Bootstrap Icons |
| **Typography** | Inter (Google Fonts) |
| **Authentication** | Django Custom User Auth (Phone or Full Name login) |
| **AI Agent Layer** | Custom Python Engine (`agents` app) |

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.13 or higher
* Git

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

5. **Populate 200+ Dummy Demo Data (Optional but Recommended)**:
   ```bash
   python seed_data.py
   ```

6. **Create an Admin Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```

8. **Open in Browser**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 Login & Demo Credentials

* **Login Methods Supported**:
  * **Phone Number** (e.g. `9876543210`)
  * **Full Name** (e.g. `John Doe`)
* **Default Seeder Password**: `password123` (works for all seeded donor and requester accounts).

---

## 🧪 Running Unit Tests

Run the full Django test suite (including AI compatibility and verification tests):
```bash
python manage.py test
```

---

## 📁 Project Structure

```
BloodBank_Django_Project/
├── accounts/          # Custom User model, auth, security profiles, admin logs
├── agents/            # AI Agent service engine, compatibility matrix, logs & dashboard
├── donors/            # Donor model, search, health eligibility documents
├── inventory/         # BloodGroup & BloodStock inventory management
├── requests_app/      # BloodRequest model, prescription uploads, donations
├── notifications/     # In-app notification delivery system
├── ratings/           # User service ratings & feedback
├── templates/         # HTML Bootstrap 5 templates & AI Control Center
├── static/            # CSS styles and static assets
├── media/             # Uploaded health certificates & doctor prescriptions
├── seed_data.py       # Data seeder script (populates 200+ realistic records)
├── manage.py          # Django CLI utility
└── README.md          # Project documentation
```

---

## 📄 Documentation Files

* **`project_report.html`**: Comprehensive HTML documentation (open in browser).
* **`BUGS_FIXED.md`**: Complete summary of bug fixes and stability enhancements.

---

## 🤝 Support & Contribution

For questions or contributions, feel free to open an issue or submit a pull request on [GitHub](https://github.com/Lalith9701/BloodBank_Django_Project).

**Status**: ✅ Production Ready | **Bugs**: 0 | **Tests**: Passing
