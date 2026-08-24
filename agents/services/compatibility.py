"""
Medical Blood Compatibility Matrix for ABO and Rh Factor Systems.
Defines compatible donor blood types for any recipient blood group.
"""

BLOOD_COMPATIBILITY_MATRIX = {
    'O-': ['O-'],
    'O+': ['O-', 'O+'],
    'A-': ['O-', 'A-'],
    'A+': ['O-', 'O+', 'A-', 'A+'],
    'B-': ['O-', 'B-'],
    'B+': ['O-', 'O+', 'B-', 'B+'],
    'AB-': ['O-', 'A-', 'B-', 'AB-'],
    'AB+': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
}


def get_compatible_donor_groups(recipient_group_str: str) -> list[str]:
    """
    Given a recipient's blood group (e.g. 'A+', 'O-'), returns a list of all
    compatible donor blood groups according to standard medical guidelines.
    """
    clean_group = recipient_group_str.strip().upper()
    return BLOOD_COMPATIBILITY_MATRIX.get(clean_group, [clean_group])
