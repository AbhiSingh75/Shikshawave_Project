import logging

logger = logging.getLogger(__name__)

def get_branding_title(profile_id, school_name):
    """
    Simplified branding logic based on user roles.
    - Super Admin (1), Support (9), Referral (10) -> ShikshaWave
    - Others -> School Name
    """
    try:
        # Profile IDs: 1=Super Admin, 9=Support Executive, 10=Referral Partner
        brand_roles = (1, 9, 10)
        
        if profile_id in brand_roles:
            return "ShikshaWave"
        
        return school_name or "ShikshaWave"
    except Exception as e:
        logger.error(f"Error resolving branding title: {e}")
        return school_name or "ShikshaWave"
