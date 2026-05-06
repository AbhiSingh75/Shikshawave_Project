from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from .decorators import login_required
import logging

logger = logging.getLogger(__name__)

@login_required
def user_settings(request):
    user_id = request.session.get('UserId')
    
    # Get current timeout setting (default 60 minutes if not set)
    with connection.cursor() as cursor:
        cursor.execute('SELECT "SessionTimeoutMinutes" FROM "UserMaster" WHERE "UserID" = %s', [user_id])
        result = cursor.fetchone()
        timeout_minutes = result[0] if result and result[0] is not None else 60
        
        # Ensure timeout is one of allowed values
        allowed_timeouts = [5, 10, 15, 30, 60, 90, 120, 180]
        if timeout_minutes not in allowed_timeouts:
            timeout_minutes = 60
    
    if request.method == 'POST':
        new_timeout = int(request.POST.get('timeout_minutes', 60))
        
        # Validate timeout is one of allowed values
        allowed_timeouts = [5, 10, 15, 30, 60, 90, 120, 180]
        if new_timeout not in allowed_timeouts:
            new_timeout = 60  # Default to 60 if invalid
        
        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE "UserMaster" SET "SessionTimeoutMinutes" = %s WHERE "UserID" = %s',
                [new_timeout, user_id]
            )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'status': 'success', 
                'message': f'Session timeout set to {new_timeout} minutes. It will take effect at next login.'
            })

        messages.success(request, f'Session timeout set to {new_timeout} minutes. Please logout and login again for changes to take effect.')
        logger.info(f"User {user_id} updated timeout from {timeout_minutes} to {new_timeout} minutes")
        return redirect('dashboard')
    
    context = {
        'timeout_minutes': timeout_minutes,
        'dark_mode': request.session.get('dark_mode', False),
        'user_name': request.session.get('UserName', 'User'),
        'profile_name': request.session.get('ProfileName', 'Profile')
    }
    return render(request, 'core/user_settings.html', context)
