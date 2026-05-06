import os
import sys
import django
from django.utils import timezone

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
django.setup()

from core.models import UserMaster, SchoolMaster

def get_or_create_user(profile_id, role_name, school_id=None):
    user = UserMaster.objects.filter(profile_id=profile_id, is_active=True).first()
    if not user:
        print(f"Creating {role_name}...")
        if not school_id:
            school = SchoolMaster.objects.first()
            school_id = school.school_id if school else 1
            
        user = UserMaster.objects.create(
            email=f"test_{role_name.replace(' ', '_').lower()}@example.com",
            password="password",
            user_name=f"Test {role_name}",
            profile_id=profile_id,
            school_id=school_id,
            is_active=True,
            created_at=timezone.now()
        )
    print(f"USER_FOUND: {role_name}|{user.user_id}|{user.school_id}")
    return user

sa = get_or_create_user(1, "Super Admin")
school_admin = get_or_create_user(2, "School Admin", school_id=sa.school_id)
support = get_or_create_user(5, "Support Executive", school_id=sa.school_id)
