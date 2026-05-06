from django.db import connection
import logging
import json
from .utils import get_context

logger = logging.getLogger(__name__)

def global_user_context(request):
    """
    Consolidated global context processor to add user information, 
    school info, dark mode preference, and session timeout to all templates.
    """
    try:
        # Use existing utility to fetch core context
        context = get_context(request)
        
        # Calculate actual session expiry relative strictly to the server's sliding window
        # We output remaining_seconds instead of an absolute server timestamp to prevent 
        # infinite redirect loops if the user's local PC hardware clock is heavily desynchronized.
        session_remaining_seconds = 3600
        try:
            from django.utils import timezone
            
            # Fetch the actual expiration explicitly from custom user_sessions table
            # to prevent the UI from resetting to 60:00 continuously on every page refresh
            session_token = request.COOKIES.get('shsw_sess')
            if session_token:
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT "expires_at" FROM "user_sessions" WHERE "session_token" = %s AND "LogoutTime" IS NULL', 
                        [session_token]
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        expiry_date = row[0]
                        now = timezone.now()
                        
                        # Align expiry_date awareness with current timezone.now() relative to USE_TZ
                        if timezone.is_aware(now):
                            if timezone.is_naive(expiry_date):
                                expiry_date = timezone.make_aware(expiry_date, timezone.get_current_timezone())
                        else:
                            if timezone.is_aware(expiry_date):
                                expiry_date = timezone.make_naive(expiry_date, timezone.get_current_timezone())
                        
                        remaining_delta = expiry_date - now
                        session_remaining_seconds = int(remaining_delta.total_seconds())
                        
                        if session_remaining_seconds < 0:
                            session_remaining_seconds = 0
        except Exception as e:
            logger.error(f"Error calculating session expiry: {str(e)}")
            
        context['session_remaining_seconds'] = session_remaining_seconds
        
        # Fetch timeout_minutes from database if not in context
        if 'timeout_minutes' not in context:
            user_id = request.session.get('UserId')
            if user_id:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT \"SessionTimeoutMinutes\" FROM \"UserMaster\" WHERE \"UserID\" = %s AND \"IsDeleted\" IS FALSE", 
                            [user_id]
                        )
                        row = cursor.fetchone()
                        if row and row[0]:
                            context['timeout_minutes'] = row[0]
                        else:
                            context['timeout_minutes'] = 60 # Default
                except Exception as e:
                    logger.error(f"Error fetching timeout for UserID {user_id}: {str(e)}")
        
        context['session_remaining_seconds'] = session_remaining_seconds
        
        # Ensure 'user' object is available globally for header templates
        # This fixes the VariableDoesNotExist error on non-dashboard pages
        context['user'] = context.get('user') or getattr(request, 'custom_user', None)
        
        return context
        
    except Exception as e:
        logger.error(f"Error in global_user_context: {str(e)}")
        return {}

def dark_mode_context(request):
    """
    Deprecated: use global_user_context instead.
    Keeping for backward compatibility if referenced elsewhere.
    """
    return global_user_context(request)

def menu_context(request):
    """
    Global context processor to add menu items to all templates.
    """
    menus = []
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID') # Use ProfileID from session
    
    if user_id and profile_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT 
                        m."MenuID",
                        m."MenuName",
                        m."MenuURL",
                        m."ParentMenuID",
                        m."DisplayOrder",
                        m."Icon"
                    FROM "MenuMaster" m
                    INNER JOIN "ProfileMenuMapping" pmm ON m."MenuID" = pmm."MenuID"
                    WHERE pmm."ProfileID" = %s 
                        AND m."IsActive" = TRUE 
                        AND m."IsDeleted" IS FALSE
                    ORDER BY m."DisplayOrder", m."MenuName"
                """, [profile_id])
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                menu_dict = {}
                for row in rows:
                    menu_data = dict(zip(columns, row))
                    menu_id = menu_data['MenuID']
                    menu_dict[menu_id] = {
                        'id': menu_id,
                        'name': menu_data['MenuName'],
                        'url': menu_data['MenuURL'] or '#',
                        'icon': menu_data.get('Icon') or 'fas fa-circle',
                        'parent_id': menu_data['ParentMenuID'],
                        'children': []
                    }
                
                # Build hierarchy
                for menu_id, menu in menu_dict.items():
                    if menu['parent_id'] and menu['parent_id'] in menu_dict:
                        menu_dict[menu['parent_id']]['children'].append(menu)
                    elif not menu['parent_id']:
                        menus.append(menu)
                        
        except Exception as e:
            logger.error(f"Error loading menus: {str(e)}")
    
    return {'menus': menus}
