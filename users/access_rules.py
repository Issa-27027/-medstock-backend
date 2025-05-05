# Define access rules for each role
ROLE_ACCESS = {
    'admin': [
        'dashboard',
        'prescriptions',
        'patient_records',
        'settings',
        'inventory',
        'orders',
        # Add any other pages admin should have access to
    ],
    'doctor': [
        'dashboard',
        'prescriptions',
        'patient_records',
        'settings',
    ],
    'pharmacist': [
        'dashboard',
        'inventory',
        'prescriptions',
        'patient_records',
        'orders',
        'settings',
    ],
}

def has_access(user, page):
    """
    Check if a user has access to a specific page
    """
    if not user.is_authenticated:
        return False
        
    # Admin has access to everything
    if user.userprofile.role == 'admin':
        return True
        
    # Check if the user's role has access to the requested page
    return page in ROLE_ACCESS.get(user.userprofile.role, [])