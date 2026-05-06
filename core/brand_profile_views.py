from django.shortcuts import render, redirect
from django.contrib import messages
from .decorators import custom_login_required
from .models import BrandProfile, ProfileMaster
from .utils import get_context
from django.utils import timezone
from django.db import connection, transaction

@custom_login_required
def brand_profile_management(request):
    """
    View for managing the global Brand Profile.
    Restricted to Super Admin (ProfileID=1).
    """
    # Use request.custom_user populated by custom_login_required
    user_data = request.custom_user
    if user_data.get('profile_id') != 1:
        messages.error(request, "Access Denied: Only Super Administrators can manage Brand Profile.")
        return redirect('dashboard')

    # Get the session data (theme etc)
    session_data = get_context(request)
    
    # Try to get existing profile or create one if none exists (should be seeded)
    brand_profile = BrandProfile.objects.first()
    
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')
        tagline = request.POST.get('tagline')
        gstin = request.POST.get('gstin')
        pan = request.POST.get('pan')
        address = request.POST.get('address')
        state = request.POST.get('state')
        state_code = request.POST.get('state_code')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        website = request.POST.get('website')
        authorized_signatory = request.POST.get('authorized_signatory')
        
        # Handle file uploads
        logo_file = request.FILES.get('brand_logo')
        signature_file = request.FILES.get('sig_upload')
        stamp_file = request.FILES.get('org_stamp_upload')
        
        # Debugging: Print counts and names
        print(f"DEBUG: Files received: {list(request.FILES.keys())}")
        if logo_file: print(f"DEBUG: Logo received: {logo_file.name}")
        if signature_file: print(f"DEBUG: Signature received: {signature_file.name}")
        if stamp_file: print(f"DEBUG: Stamp received: {stamp_file.name}")
        
        if not brand_profile:
            brand_profile = BrandProfile(brand_name=brand_name)
        
        brand_profile.brand_name = brand_name
        brand_profile.tagline = tagline
        brand_profile.gstin = gstin
        brand_profile.pan = pan
        brand_profile.address = address
        brand_profile.state = state
        brand_profile.state_code = state_code
        brand_profile.phone = phone
        brand_profile.email = email
        brand_profile.website = website
        brand_profile.authorized_signatory = authorized_signatory
        brand_profile.updated_at = timezone.now()
        brand_profile.updated_by = user_data.get('user_id')
        
        # Atomic update strategy for binary fields on managed=False model
        with transaction.atomic():
            brand_profile.save()
            
            if logo_file:
                logo_data = logo_file.read()
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE "BrandProfile" SET "BrandLogo" = %s WHERE "ProfileID" = %s', [logo_data, brand_profile.profile_id])
                print(f"DEBUG: Raw SQL Logo Update executed for ID {brand_profile.profile_id}")
                
            if signature_file:
                sig_data = signature_file.read()
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE "BrandProfile" SET "AuthorizedSignature" = %s WHERE "ProfileID" = %s', [sig_data, brand_profile.profile_id])
                print(f"DEBUG: Raw SQL Signature Update executed for ID {brand_profile.profile_id}")

            if stamp_file:
                stamp_data = stamp_file.read()
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE "BrandProfile" SET "OrganizationStamp" = %s WHERE "ProfileID" = %s', [stamp_data, brand_profile.profile_id])
                print(f"DEBUG: Raw SQL Stamp Update executed for ID {brand_profile.profile_id}")
        
        if logo_file or signature_file or stamp_file:
            brand_profile.refresh_from_db()
            print(f"DEBUG: Model refreshed. SigLen: {len(brand_profile.authorized_signature) if brand_profile.authorized_signature else 'None'}, StampLen: {len(brand_profile.organization_stamp) if brand_profile.organization_stamp else 'None'}")
            
        messages.success(request, 'Profile Synchronization Successful! Corporate identity and digital authorization signatures have been stabilized across the ecosystem.', extra_tags='modal')
        return redirect('brand_profile_management')

    context = {
        'brand_profile': brand_profile,
        **session_data,
        'page_title': 'Brand Profile Management',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Brand Profile', 'url': None},
        ]
    }
    
    return render(request, 'core/brand_profile.html', context)
