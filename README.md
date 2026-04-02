# Blood Bank Management System (Django Project)

A comprehensive web application for managing blood bank operations built with Django 6.0 and Python 3.13.

## ✅ Project Status: ALL BUGS FIXED

All critical bugs and errors have been resolved. The project is now fully functional.

## Features

- **User Authentication**: Login with phone number OR full name
- **Role-Based Access**: Admin, Donor, and Requester roles
- **Blood Inventory Management**: Track blood stock in real-time
- **Donation Tracking**: Record and manage blood donations
- **Blood Requests**: Submit and approve blood requests
- **Notifications**: In-app notifications for all key events
- **Security**: Question-based password reset, CSRF protection, password hashing
- **Admin Panel**: Manage donors, approve health eligibility, view audit logs
- **Ratings**: Rate blood request service
- **Export**: CSV export for donors and requests

## Quick Start

### Prerequisites
- Python 3.13
- Django 6.0

### Installation

1. Install Django:
```bash
pip install django
```

2. Apply database migrations:
```bash
python manage.py migrate
```

3. Create an admin superuser:
```bash
python manage.py createsuperuser
```

4. Start the development server:
```bash
python manage.py runserver
```

5. Open in browser:
```
http://127.0.0.1:8000
```

## Login Instructions

You can login using either:
- **Phone Number**: Enter your registered phone number (e.g., 9876543210)
- **Full Name**: Enter your full name exactly as registered (e.g., John Doe)

## Project Structure

- `accounts/` - User authentication, registration, profile, security questions
- `donors/` - Donor model and donor search
- `inventory/` - Blood groups and stock management
- `requests_app/` - Blood requests and donations
- `notifications/` - In-app notification system
- `ratings/` - Rating system for blood requests
- `templates/` - 24 HTML templates
- `static/` - CSS and static files

## Recent Fixes (31 Bugs Fixed)

See `BUGS_FIXED.md` and `FIXES_SUMMARY.md` for complete details.

Key fixes:
- ✅ Fixed all syntax errors in accounts/views.py
- ✅ Fixed login with mobile number and full name
- ✅ Removed external API dependencies
- ✅ Added database constraints (unique phone numbers)
- ✅ Cleaned up duplicate records
- ✅ Removed unused temporary files

## Documentation

- **project_report.html** - Complete project documentation (open in browser)
- **BUGS_FIXED.md** - Detailed list of all bugs fixed
- **FIXES_SUMMARY.md** - Comprehensive summary of fixes

## Technology Stack

- **Backend**: Django 6.0, Python 3.13
- **Database**: SQLite 3
- **Frontend**: Bootstrap 5.3, Vanilla JavaScript
- **Authentication**: Django built-in auth with custom User model

## Security Features

- PBKDF2-SHA256 password hashing
- CSRF protection on all forms
- Security question-based password reset
- Brute-force protection (account lockout)
- Role-based access control
- Audit logging for admin actions

## Support

For issues or questions, refer to the project documentation in `project_report.html`.

---

**Status**: ✅ Production Ready | **Bugs**: 0 | **Tests**: Passing
