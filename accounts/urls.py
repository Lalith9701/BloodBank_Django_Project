from django.urls import path
from .views import (
    login_view, register, dashboard, logout_view,
    admin_health_approvals, admin_all_donors, profile, export_donors_csv,
    sq_lookup, sq_answer, sq_reset_password,
    audit_log, toggle_donor_active,
    contact_admin, admin_contact_messages,
)

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('admin-health-approvals/', admin_health_approvals, name='admin_health_approvals'),
    path('admin-all-donors/', admin_all_donors, name='admin_all_donors'),
    path('export-donors/', export_donors_csv, name='export_donors_csv'),
    path('admin-audit-log/', audit_log, name='audit_log'),
    path('admin-donors/toggle/<int:donor_id>/', toggle_donor_active, name='toggle_donor_active'),
    path('contact-admin/', contact_admin, name='contact_admin'),
    path('admin-messages/', admin_contact_messages, name='admin_contact_messages'),

    # ── Security Question Password Reset ────────────────────
    path('forgot-password/', sq_lookup, name='sq_lookup'),
    path('forgot-password/question/', sq_answer, name='sq_answer'),
    path('forgot-password/reset/', sq_reset_password, name='sq_reset_password'),
]
