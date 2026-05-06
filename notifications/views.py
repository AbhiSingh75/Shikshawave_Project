from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.decorators import login_required
from .services import NotificationService
import json
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """Get notifications for the logged-in user"""
    user_id = request.session.get('UserId')
    profile_name = request.session.get('ProfileName')
    
    # Super Admin and Support Executive don't need school filter
    if profile_name in ['Super Admin', 'Support Executive']:
        school_id = None
    else:
        school_id = request.session.get('SchoolId') or request.session.get('SchoolID')
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    if not user_id:
        return JsonResponse({'notifications': [], 'total_count': 0, 'page_number': 1, 'page_size': 20, 'total_pages': 0})
    
    try:
        result = NotificationService.get_notifications(
            user_id=user_id,
            school_id=school_id,
            page_number=page,
            page_size=page_size,
            unread_only=unread_only
        )
        
        # Format datetime fields safely
        for notification in result['notifications']:
            # Handle CreatedAt
            c_at = notification.get('CreatedAt')
            if c_at:
                try:
                    notification['CreatedAt'] = c_at.isoformat() if hasattr(c_at, 'isoformat') else str(c_at)
                except Exception:
                    notification['CreatedAt'] = str(c_at)
            
            # Handle ReadAt
            r_at = notification.get('ReadAt')
            if r_at:
                try:
                    notification['ReadAt'] = r_at.isoformat() if hasattr(r_at, 'isoformat') else str(r_at)
                except Exception:
                    notification['ReadAt'] = str(r_at)
        
        return JsonResponse(result)
    except Exception as e:
        import traceback
        logger.error(f"Notification Error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'notifications': [], 'total_count': 0, 'page_number': 1, 'page_size': page_size, 'total_pages': 0,
            'error': str(e)
        }, status=200) # Still return 200 for frontend dropdown to handle it as an empty state or error message


@require_http_methods(["GET"])
def get_unread_count(request):
    """Get unread notification count"""
    try:
        user_id = request.session.get('UserId')
        if not user_id:
            return JsonResponse({'unread_count': 0})
        
        profile_name = request.session.get('ProfileName')
        
        # Super Admin and Support Executive don't need school filter
        if profile_name in ['Super Admin', 'Support Executive']:
            school_id = None
        else:
            school_id = request.session.get('SchoolId') or request.session.get('SchoolID')
        
        count = NotificationService.get_unread_count(
            user_id=user_id,
            school_id=school_id
        )
        return JsonResponse({'unread_count': count})
    except:
        return JsonResponse({'unread_count': 0})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    user_id = request.session.get('UserId')
    success = NotificationService.mark_as_read(
        notification_id=notification_id,
        user_id=user_id
    )
    return JsonResponse({'success': success})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """Mark all notifications as read"""
    user_id = request.session.get('UserId')
    profile_name = request.session.get('ProfileName')
    
    # Super Admin and Support Executive don't need school filter
    if profile_name in ['Super Admin', 'Support Executive']:
        school_id = None
    else:
        school_id = request.session.get('SchoolId') or request.session.get('SchoolID')
    
    success = NotificationService.mark_all_as_read(
        user_id=user_id,
        school_id=school_id
    )
    return JsonResponse({'success': success})
