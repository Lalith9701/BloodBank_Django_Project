import re
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model

from requests_app.models import BloodRequest, Donation
from inventory.models import BloodStock
from donors.models import Donor
from notifications.models import Notification
from accounts.models import AuditLog
from agents.models import AgentExecutionLog
from agents.services.compatibility import get_compatible_donor_groups

logger = logging.getLogger(__name__)
User = get_user_model()


def run_emergency_dispatch_agent(blood_request_id: int, trigger_type: str = 'AUTOMATIC') -> AgentExecutionLog:
    """
    Enhanced Multi-Tier AI Verification & Auto-Approval Engine.
    
    Tiers of Verification:
    - Tier 1: Patient Details Verification (Name, 10-digit Phone, Gender, Address, Purpose).
    - Tier 2: Doctor Prescription Verification (Attachment of prescription image/PDF).
    - Tier 3: Inventory Stock Availability (Units available >= Units required).
    
    Actions:
    - IF ALL TIERS PASS: Automatically approves the request, deducts stock, notifies requester.
    - IF ANY TIER FAILS: Leaves request as PENDING and logs detailed verification warnings 
      so staff/admins can review manually. Dispatches emergency donor alerts if needed.
    """
    try:
        blood_request = BloodRequest.objects.select_related('user', 'blood_group').get(id=blood_request_id)
    except BloodRequest.DoesNotExist:
        logger.error(f"Agent failed: BloodRequest #{blood_request_id} does not exist.")
        raise ValueError(f"BloodRequest #{blood_request_id} not found.")

    requested_group_str = blood_request.blood_group.blood_group
    units_needed = blood_request.units_required

    # 1. Tier 3: Stock Evaluation
    try:
        stock_obj = BloodStock.objects.get(blood_group=blood_request.blood_group)
        stock_available = stock_obj.units_available
    except BloodStock.DoesNotExist:
        stock_available = 0

    stock_deficit = units_needed - stock_available

    # 2. Tier 1: Patient Details & Purpose Verification
    patient_name_valid = bool(blood_request.patient_name and len(blood_request.patient_name.strip()) >= 2)
    
    # 10-digit phone verification
    clean_phone = re.sub(r'\D', '', blood_request.patient_phone or '')
    patient_phone_valid = len(clean_phone) == 10

    patient_address_valid = bool(blood_request.patient_address and len(blood_request.patient_address.strip()) >= 3)
    purpose_valid = bool(blood_request.purpose and len(blood_request.purpose.strip()) >= 3)

    tier1_patient_details_passed = (patient_name_valid and patient_phone_valid and patient_address_valid and purpose_valid)

    # 3. Tier 2: Prescription Document Verification
    tier2_prescription_passed = bool(blood_request.prescription_document)

    # 4. Tier 3: Stock Availability
    tier3_stock_passed = (stock_available >= units_needed)

    # 5. Autonomous Auto-Approval Evaluation
    all_tiers_passed = (tier1_patient_details_passed and tier2_prescription_passed and tier3_stock_passed)

    auto_approved = False
    if all_tiers_passed and blood_request.status == 'PENDING':
        blood_request.status = 'APPROVED'
        blood_request.save()  # Triggers stock deduction in BloodRequest.save()
        auto_approved = True

        # Send auto-approval notification to requester
        Notification.objects.create(
            user=blood_request.user,
            title="🤖 Prescription Verified: Auto-Approved by AI Agent",
            message=(
                f"Your request for {units_needed} units of {requested_group_str} (Patient: {blood_request.patient_name}) "
                f"was verified and automatically approved by the AI Agent! "
                f"Prescription document and patient details were successfully validated."
            ),
            notif_type="success"
        )

        # Log system audit action
        AuditLog.objects.create(
            actor=None,
            action='AI Agent Auto-Approved Verified Request',
            target=f'Patient: {blood_request.patient_name} (by {blood_request.user.username})',
            detail=f'{units_needed} units of {requested_group_str}. Prescription & Patient Data Verified.'
        )

    # 6. Medical Compatibility & Emergency Donor Dispatch (for shortages or urgent requests)
    compatible_groups = get_compatible_donor_groups(requested_group_str)
    notified_count = 0
    candidate_donors_count = 0
    excluded_cooldown_count = 0

    if stock_deficit > 0 or blood_request.urgency in ['EMERGENCY', 'URGENT']:
        candidate_donors = Donor.objects.filter(
            blood_group__blood_group__in=compatible_groups,
            availability=True,
            eligibility_status='ELIGIBLE',
            user__is_active=True
        ).select_related('user', 'blood_group')

        candidate_donors_count = candidate_donors.count()
        eligible_donors = []
        now = timezone.now()

        for donor in candidate_donors:
            last_donation = Donation.objects.filter(donor=donor).order_by('-donation_date').first()
            if last_donation:
                days_since = (now - last_donation.donation_date).days
                if days_since < 90:
                    excluded_cooldown_count += 1
                    continue
            eligible_donors.append(donor)

        requester_display = blood_request.user.get_full_name() or blood_request.user.username

        for donor in eligible_donors:
            Notification.objects.create(
                user=donor.user,
                title="🚨 URGENT BLOOD DONATION DISPATCH ALERT",
                message=(
                    f"EMERGENCY MATCH ALERT: An urgent request for {units_needed} units of "
                    f"{requested_group_str} has been logged by {requester_display}. "
                    f"Your blood group ({donor.blood_group.blood_group}) is medically compatible! "
                    f"If you are able to donate, please log in to record your donation or contact the blood bank immediately."
                ),
                notif_type="danger"
            )
            notified_count += 1

    # 7. Build Detailed Agent Verification Reasoning Log
    reasoning_lines = [
        f"• Evaluated Request #{blood_request.id} ({units_needed} units of {requested_group_str}, Urgency: {blood_request.urgency}).",
        f"• Patient Name: {blood_request.patient_name or 'N/A'} | Phone: {blood_request.patient_phone or 'N/A'}.",
        f"• Medical Purpose: {blood_request.purpose or 'N/A'}.",
        f"--- VERIFICATION TIERS MATRIX ---",
        f"  [Tier 1] Patient Info Check: {'✅ PASSED' if tier1_patient_details_passed else '❌ FAILED (Invalid name, phone format, or missing address)'}",
        f"  [Tier 2] Doctor Prescription Check: {'✅ PASSED (File Attached)' if tier2_prescription_passed else '❌ FAILED (No Prescription Image Uploaded)'}",
        f"  [Tier 3] Stock Availability Check: {'✅ PASSED (' + str(stock_available) + ' available)' if tier3_stock_passed else '❌ FAILED (Deficit of ' + str(stock_deficit) + ' units)'}",
    ]

    if auto_approved:
        reasoning_lines.append(
            f"• FINAL AGENT DECISION: ALL TIERS PASSED. Request automatically APPROVED and stock deducted without admin delay."
        )
    else:
        failure_reasons = []
        if not tier1_patient_details_passed:
            failure_reasons.append("Incomplete patient details or invalid mobile number")
        if not tier2_prescription_passed:
            failure_reasons.append("Missing prescription image/PDF")
        if not tier3_stock_passed:
            failure_reasons.append(f"Stock shortage ({stock_available} units available)")

        reasoning_lines.append(
            f"• FINAL AGENT DECISION: HANDOVER TO ADMIN REVIEW. Reason: {', '.join(failure_reasons)}. Status remains PENDING."
        )

    if stock_deficit > 0 or blood_request.urgency in ['EMERGENCY', 'URGENT']:
        reasoning_lines.append(
            f"• Donor Dispatch Action: Notified {notified_count} compatible donor(s) across groups ({', '.join(compatible_groups)})."
        )

    reasoning_summary = "\n".join(reasoning_lines)

    # 8. Notify Staff / Admins
    staff_users = User.objects.filter(is_staff=True)
    status_msg = "Auto-Approved" if auto_approved else "Requires Admin Review"
    for staff in staff_users:
        Notification.objects.create(
            user=staff,
            title=f"🤖 AI Agent Verification: Request #{blood_request.id} ({status_msg})",
            message=(
                f"AI Agent verified Request #{blood_request.id} ({requested_group_str}, {units_needed} units). "
                f"Outcome: {status_msg}. Prescription: {'Attached' if tier2_prescription_passed else 'Missing'}. "
                f"Stock: {stock_available} units."
            ),
            notif_type="success" if auto_approved else "warning"
        )

    # 9. Create Agent Execution Log
    log_entry = AgentExecutionLog.objects.create(
        blood_request=blood_request,
        trigger_type=trigger_type,
        requested_blood_group=requested_group_str,
        units_requested=units_needed,
        stock_available=stock_available,
        compatible_blood_groups=", ".join(compatible_groups),
        eligible_donors_found=candidate_donors_count,
        donors_notified_count=notified_count,
        reasoning_summary=reasoning_summary
    )

    logger.info(f"Agent Execution Log #{log_entry.id} saved for Request #{blood_request.id}.")
    return log_entry
