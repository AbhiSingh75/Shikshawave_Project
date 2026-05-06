from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from .decorators import custom_login_required
from .utils import get_context, _get_custom_session_info
import logging
import json

logger = logging.getLogger(__name__)

# Debug/Test Views

def menu_data_list_debug(request):
    """Debug view to check session and permissions"""
    context = get_context(request)
    sess = _get_custom_session_info(request)
    
    debug_info = {
        'has_custom_session': sess is not None,
        'session_info': sess,
        'django_session_keys': list(request.session.keys()),
        'user_id_session': request.session.get('UserId'),
        'profile_id_session': request.session.get('ProfileID'),
        'user_name_session': request.session.get('UserName'),
    }
    
    return JsonResponse(debug_info)

def menu_data_list_test(request):
    """Test view without login requirement to check if data loads"""
    try:
        with connection.cursor() as cursor:
            # Updated to PostgreSQL syntax (LIMIT, quotes, COALESCE)
            cursor.execute("""
                SELECT 
                    m.MenuID,
                    m.MenuName,
                    m.MenuURL,
                    m.Icon,
                    m.DisplayOrder,
                    m.IsActive,
                    pm.MenuName as ParentMenuName
                FROM "MenuMaster" m
                LEFT JOIN "MenuMaster" pm ON m.ParentMenuID = pm.MenuID
                WHERE COALESCE(m.IsDeleted, FALSE) = FALSE
                ORDER BY COALESCE(m.ParentMenuID, 0), m.DisplayOrder, m.MenuName
                LIMIT 10
            """)
            
            columns = [col[0] for col in cursor.description]
            menu_data = []
            for row in cursor.fetchall():
                menu_item = dict(zip(columns, row))
                menu_data.append(menu_item)
            
            return JsonResponse({
                'success': True,
                'count': len(menu_data),
                'data': menu_data[:5]  # Show first 5 items
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Main Views

@custom_login_required
def menu_data_list(request):
    """
    Menu Data list view - Display all menu data using stored procedure
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user context for header
    context = get_context(request)
    
    # Aggressively clear existing messages from session
    storage = messages.get_messages(request)
    list(storage)  # Iterate to load from session and mark as used
    
    # Override messages in context to ensure nothing is displayed
    context['messages'] = []

    # Get session info for user object (needed for header template)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    
    logger.info(f"Menu data access - UserID: {user_id}, ProfileID: {profile_id}")
    
    if not user_id:
        messages.error(request, "Please login to access menu data")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        logger.warning(f"Access denied - ProfileID {profile_id} not in [1, 2]")
        messages.error(request, "You don't have permission to access menu data management")
        return redirect('dashboard')
    
    # Initialize variables
    menu_data = []
    
    try:
        with connection.cursor() as cursor:
            # Use the stored function to get menu data
            cursor.execute("SELECT * FROM Proc_menu_list_get()")
            
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                menu_item = dict(zip(columns, row))
                menu_data.append(menu_item)
            
            logger.info(f"Fetched {len(menu_data)} menu items using stored procedure")
    
    except Exception as e:
        logger.error(f"Error fetching menu data: {str(e)}")
        messages.error(request, "Error loading menu data")
        menu_data = []
    
    # Sort menu data hierarchically (Parent -> Children)
    parents = [m for m in menu_data if not m.get('ParentMenuID')]
    children = [m for m in menu_data if m.get('ParentMenuID')]
    
    parents.sort(key=lambda x: (x.get('DisplayOrder') or 0, x.get('MenuName') or ''))
    
    sorted_menu = []
    for parent in parents:
        sorted_menu.append(parent)
        p_children = [c for c in children if c.get('ParentMenuID') == parent.get('MenuID')]
        p_children.sort(key=lambda x: (x.get('DisplayOrder') or 0, x.get('MenuName') or ''))
        sorted_menu.extend(p_children)
        
    handled_ids = set(m['MenuID'] for m in sorted_menu)
    orphans = [m for m in menu_data if m['MenuID'] not in handled_ids]
    orphans.sort(key=lambda x: (x.get('DisplayOrder') or 0, x.get('MenuName') or ''))
    sorted_menu.extend(orphans)
    
    menu_data = sorted_menu
    
    # Get parent menus for modal dropdown using quoted identifiers
    parent_menus = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "MenuID", "MenuName" 
                FROM "MenuMaster" 
                WHERE "ParentMenuID" IS NULL 
                AND "IsActive" = TRUE 
                AND COALESCE("IsDeleted", FALSE) = FALSE
                ORDER BY "DisplayOrder", "MenuName"
            """)
            parent_menus = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching parent menus: {str(e)}")
    
    # Add context info
    context.update({
        'menu_data': menu_data,
        'parent_menus': parent_menus,
        'total_count': len(menu_data),
        'page_title': 'Menu Data Management',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Menu Data', 'url': None}
        ]
    })
    
    return render(request, 'core/menu_data_list.html', context)

@custom_login_required
def menu_data_add(request):
    """
    Add new menu data
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user context for header
    context = get_context(request)
    
    # Get session info for user object (needed for header template)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    
    if not user_id:
        messages.error(request, "Please login to access menu data management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access menu data management")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Extract form data
            menu_name = request.POST.get('menu_name', '').strip()
            menu_url = request.POST.get('menu_url', '').strip()
            icon = request.POST.get('icon', '').strip()
            display_order = request.POST.get('display_order', '').strip()
            parent_menu_id = request.POST.get('parent_menu_id', '').strip()
            is_active = request.POST.get('is_active', '1')
            
            # Validation
            errors = []
            if not menu_name:
                errors.append("Menu name is required")
            if not display_order or not display_order.isdigit():
                errors.append("Display order must be a valid number")
            if parent_menu_id and not parent_menu_id.isdigit():
                errors.append("Invalid parent menu selection")
            
            if errors:
                context.update({
                    'errors': errors,
                    'form_data': request.POST
                })
            else:
                # Use stored procedure for INSERT
                with connection.cursor() as cursor:
                    # Prepare parameters
                    parent_menu_id_param = int(parent_menu_id) if parent_menu_id else None
                    display_order_param = int(display_order) if display_order else 0
                    is_active_param = is_active == '1'
                    
                    # Execute stored procedure - PostgreSQL CALL syntax
                    # Params: Action, MenuID, MenuName, ParentMenuID, MenuURL, Icon, DisplayOrder, IsActive, UserID, Message(OUT)
                    cursor.execute("""
                        CALL Proc_MenuMaster_Manage(
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, [
                        'INSERT',
                        None, # MenuID is NULL for insert
                        menu_name,
                        parent_menu_id_param,
                        menu_url if menu_url else None,
                        icon if icon else None,
                        display_order_param,
                        is_active_param,
                        user_id,
                        None # Output parameter placeholder
                    ])
                    
                    # Fetch return message logic depends on DB driver
                    # Using fetchone() usually works if the procedure returns a result set or INOUT param
                    result = cursor.fetchone()
                    
                    if result:
                         # The INOUT param matches the last placeholder
                        result_json_str = result[0]
                        try:
                            result_data = json.loads(result_json_str)
                            if result_data.get('status') == 'success':
                                messages.success(request, result_data.get('message', 'Menu added successfully'))
                                return redirect('menu_data_list')
                            else:
                                messages.error(request, result_data.get('message', 'Error adding menu'))
                        except json.JSONDecodeError:
                            # Fallback if raw text
                            messages.success(request, "Menu added successfully")
                            return redirect('menu_data_list')
                    else:
                        # Fallback success (some drivers don't return INOUT easily)
                        messages.success(request, "Menu added successfully")
                        return redirect('menu_data_list')

        
        except Exception as e:
            logger.error(f"Error adding menu: {str(e)}")
            messages.error(request, "Error adding menu. Please try again.")
            context.update({'form_data': request.POST})
    
    # Get parent menus for dropdown
    parent_menus = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "MenuID", "MenuName" 
                FROM "MenuMaster" 
                WHERE "ParentMenuID" IS NULL 
                AND "IsActive" = TRUE 
                AND COALESCE("IsDeleted", FALSE) = FALSE
                ORDER BY "DisplayOrder", "MenuName"
            """)
            parent_menus = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching parent menus: {str(e)}")
    
    context.update({
        'parent_menus': parent_menus,
        'page_title': 'Add Menu Data',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Menu Data', 'url': 'menu_data_list'},
            {'name': 'Add Menu Data', 'url': None}
        ]
    })
    
    return render(request, 'core/menu_data_add.html', context)

@custom_login_required
def menu_data_edit(request, menu_id):
    """
    Edit existing menu data
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    context = get_context(request)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    
    if not user_id:
        messages.error(request, "Please login to access menu data management")
        return redirect('login')
    
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access menu data management")
        return redirect('dashboard')
    
    # Get menu data
    menu = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    "MenuID", "MenuName", "MenuURL", "Icon", "DisplayOrder", 
                    "ParentMenuID", "IsActive", "CreatedAt", "UpdatedAt"
                FROM "MenuMaster" 
                WHERE "MenuID" = %s AND COALESCE("IsDeleted", FALSE) = FALSE
            """, [menu_id])
            
            row = cursor.fetchone()
            if row:
                menu = {
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'icon': row[3],
                    'display_order': row[4],
                    'parent_id': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            else:
                messages.error(request, "Menu not found")
                return redirect('menu_data_list')
    
    except Exception as e:
        logger.error(f"Error fetching menu: {str(e)}")
        messages.error(request, "Error loading menu data")
        return redirect('menu_data_list')
    
    if request.method == 'POST':
        try:
            menu_name = request.POST.get('menu_name', '').strip()
            menu_url = request.POST.get('menu_url', '').strip()
            icon = request.POST.get('icon', '').strip()
            display_order = request.POST.get('display_order', '').strip()
            parent_menu_id = request.POST.get('parent_menu_id', '').strip()
            is_active = request.POST.get('is_active', '1')
            
            errors = []
            if not menu_name:
                errors.append("Menu name is required")
            if not display_order or not display_order.isdigit():
                errors.append("Display order must be a valid number")
            if parent_menu_id and not parent_menu_id.isdigit():
                errors.append("Invalid parent menu selection")
            
            if errors:
                context.update({
                    'errors': errors,
                    'menu': menu,
                    'form_data': request.POST
                })
            else:
                with connection.cursor() as cursor:
                    parent_menu_id_param = int(parent_menu_id) if parent_menu_id else None
                    display_order_param = int(display_order) if display_order else 0
                    is_active_param = is_active == '1'
                    
                    cursor.execute("""
                        CALL Proc_MenuMaster_Manage(
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, [
                        'UPDATE',
                        menu_id,
                        menu_name,
                        parent_menu_id_param,
                        menu_url if menu_url else None,
                        icon if icon else None,
                        display_order_param,
                        is_active_param,
                        user_id,
                        None
                    ])
                    
                    result = cursor.fetchone()
                    if result:
                        try:
                            result_data = json.loads(result[0])
                            if result_data.get('status') == 'success':
                                messages.success(request, result_data.get('message', 'Menu updated successfully'))
                                return redirect('menu_data_list')
                            else:
                                messages.error(request, result_data.get('message', 'Error updating menu'))
                        except:
                             messages.success(request, "Menu updated successfully")
                             return redirect('menu_data_list')
                    else:
                        messages.success(request, "Menu updated successfully")
                        return redirect('menu_data_list')
        
        except Exception as e:
            logger.error(f"Error updating menu: {str(e)}")
            messages.error(request, "Error updating menu. Please try again.")
            context.update({'menu': menu, 'form_data': request.POST})
    
    # Get parent menus
    parent_menus = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "MenuID", "MenuName" 
                FROM "MenuMaster" 
                WHERE "ParentMenuID" IS NULL 
                AND "IsActive" = TRUE 
                AND COALESCE("IsDeleted", FALSE) = FALSE
                AND "MenuID" != %s
                ORDER BY "DisplayOrder", "MenuName"
            """, [menu_id])
            parent_menus = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching parent menus: {str(e)}")
    
    context.update({
        'menu': menu,
        'parent_menus': parent_menus,
        'page_title': 'Edit Menu Data',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Menu Data', 'url': 'menu_data_list'},
            {'name': 'Edit Menu Data', 'url': None}
        ]
    })
    
    return render(request, 'core/menu_data_edit.html', context)

@custom_login_required
def menu_data_delete(request, menu_id):
    """
    Soft delete menu data
    """
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    
    if not user_id:
        return redirect('login')
    
    if profile_id not in [1, 2]:
        messages.error(request, "Permission denied")
        return redirect('dashboard')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL Proc_MenuMaster_Manage(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                'DELETE', menu_id, None, None, None, None, 0, False, user_id, None
            ])
            
            result = cursor.fetchone()
            if result:
                 # Logic for parsing result message
                 messages.success(request, "Menu deleted successfully")
            else:
                 messages.success(request, "Menu deleted successfully")
    
    except Exception as e:
        logger.error(f"Error deleting menu: {str(e)}")
        messages.error(request, "Error deleting menu")
    
    return redirect('menu_data_list')

@custom_login_required
def menu_data_restore(request, menu_id):
    """
    Restore deleted menu data
    """
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    
    if not user_id:
        return redirect('login')
    
    if profile_id not in [1, 2]:
        messages.error(request, "Permission denied")
        return redirect('dashboard')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL Proc_MenuMaster_Manage(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                'RESTORE', menu_id, None, None, None, None, 0, False, user_id, None
            ])
            
            messages.success(request, "Menu restored successfully")
    
    except Exception as e:
        logger.error(f"Error restoring menu: {str(e)}")
        messages.error(request, "Error restoring menu")
    
    return redirect('menu_data_list')


# -------------------------------------------------------------------------
# Profile Menu Mapping Views
# -------------------------------------------------------------------------

@custom_login_required
def profile_menu_mapping_list(request):
    """List all profile menu mappings"""
    try:
        # Get full global context (includes theme_styles, global menus, etc.)
        context = get_context(request)
        
        # Aggressively clear existing messages
        storage = messages.get_messages(request)
        list(storage)  # Consume all messages
        
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # Get profile filter from request
        profile_filter = request.GET.get('profile_filter')
        profile_id_param = int(profile_filter) if profile_filter else None
        
        # Get profile menu mappings using stored procedure (PostgreSQL Function)
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Proc_ProfileMenuMapping_List(%s)", [profile_id_param])
            columns = [col[0] for col in cursor.description]
            mappings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get profiles and menus for dropdowns
        # Rename 'menus' to 'menu_list' to avoid shadowing the global sidebar menus
        with connection.cursor() as cursor:
            cursor.execute('SELECT "ProfileID", "ProfileName" FROM "ProfileMaster" WHERE "IsDeleted" = FALSE')
            profiles = [dict(zip(['ProfileID', 'ProfileName'], row)) for row in cursor.fetchall()]
            
            cursor.execute('SELECT "MenuID", "MenuName" FROM "MenuMaster" WHERE "IsDeleted" = FALSE ORDER BY "MenuName"')
            menu_list = [dict(zip(['MenuID', 'MenuName'], row)) for row in cursor.fetchall()]
        
        context.update({
            'mappings': mappings,
            'profiles': profiles,
            'menu_list': menu_list,
            'total_count': len(mappings),
            'selected_profile_id': profile_id_param,
            'page_title': 'Profile Menu Mapping'
        })
        
        return render(request, 'core/profile_menu_mapping_list.html', context)
        
    except Exception as e:
        import traceback
        print("\n--- PROFILE MENU ERROR ---\n")
        print(traceback.format_exc())
        print("\n--------------------------\n")
        logger.error(f"Error in profile_menu_mapping_list: {e}")
        messages.error(request, 'An error occurred while loading profile menu mappings.', extra_tags='profile_menu')
        return redirect('dashboard')


@custom_login_required
def profile_menu_mapping_add(request):
    """Add new profile menu mapping"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            profile_id_param = request.POST.get('profile_id')
            menu_id_param = request.POST.get('menu_id')
            # Checkbox logic: if checkbox is checked, it sends '0', if unchecked, it sends '1' (via JavaScript)
            can_view = 0 if request.POST.get('can_view') == '0' else 1
            can_add = 0 if request.POST.get('can_add') == '0' else 1
            can_edit = 0 if request.POST.get('can_edit') == '0' else 1
            can_delete = 0 if request.POST.get('can_delete') == '0' else 1
            
            # Use stored procedure for INSERT (PostgreSQL Procedure)
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL Proc_ProfileMenuMapping_Manage(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    'INSERT',
                    None, # MappingID is NULL for insert
                    profile_id_param,
                    menu_id_param,
                    can_view,
                    can_add,
                    can_edit,
                    can_delete,
                    user_id,
                    None # Output parameter placeholder
                ])
                
                # Fetching the INOUT parameter from procedure call in Python via Psycopg2 matches the result set
                # Note: Psycopg2 usually returns the INOUT params as a tuple if `callproc` is used, or as a result set if `execute("CALL...")` is used.
                # When using `execute("CALL ...")`, if the procedure has INOUT, Postgres returns a single row result set with the values.
                result = cursor.fetchone()
                if result:
                    try:
                        # result[0] corresponds to the INOUT param_Message
                        result_data = json.loads(result[0])
                        if result_data.get('status') == 'success':
                            messages.success(request, result_data.get('message', 'Profile menu mapping added successfully'))
                            return redirect('profile_menu_mapping_list')
                        else:
                            messages.error(request, result_data.get('message', 'Error adding profile menu mapping'))
                    except json.JSONDecodeError:
                        messages.error(request, "Error processing response from server")
                else:
                    messages.error(request, "No response from server")
        
        # Get profiles and menus for dropdowns
        with connection.cursor() as cursor:
            cursor.execute('SELECT "ProfileID", "ProfileName" FROM "ProfileMaster" WHERE "IsDeleted" = FALSE')
            profiles = [dict(zip(['ProfileID', 'ProfileName'], row)) for row in cursor.fetchall()]
            
            cursor.execute('SELECT "MenuID", "MenuName" FROM "MenuMaster" WHERE "IsDeleted" = FALSE ORDER BY "MenuName"')
            menus = [dict(zip(['MenuID', 'MenuName'], row)) for row in cursor.fetchall()]
        
        context = {
            'profiles': profiles,
            'menus': menus,
            'user': session_info
        }
        
        return render(request, 'core/profile_menu_mapping_add.html', context)
        
    except Exception as e:
        logger.error(f"Error in profile_menu_mapping_add: {e}")
        messages.error(request, 'An error occurred while adding profile menu mapping.')
        return redirect('profile_menu_mapping_list')


@custom_login_required
def profile_menu_mapping_edit(request, mapping_id):
    """Edit profile menu mapping"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            profile_id_param = request.POST.get('profile_id')
            menu_id_param = request.POST.get('menu_id')
            # Checkbox logic
            can_view = 0 if request.POST.get('can_view') == '0' else 1
            can_add = 0 if request.POST.get('can_add') == '0' else 1
            can_edit = 0 if request.POST.get('can_edit') == '0' else 1
            can_delete = 0 if request.POST.get('can_delete') == '0' else 1
            
            # Use stored procedure for UPDATE
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL Proc_ProfileMenuMapping_Manage(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    'UPDATE',
                    mapping_id,
                    profile_id_param,
                    menu_id_param,
                    can_view,
                    can_add,
                    can_edit,
                    can_delete,
                    user_id,
                    None
                ])
                
                result = cursor.fetchone()
                if result:
                    try:
                        result_data = json.loads(result[0])
                        if result_data.get('status') == 'success':
                            messages.success(request, result_data.get('message', 'Profile menu mapping updated successfully'), extra_tags='profile_menu')
                            return redirect('profile_menu_mapping_list')
                        else:
                            messages.error(request, result_data.get('message', 'Error updating profile menu mapping'), extra_tags='profile_menu')
                    except json.JSONDecodeError:
                        messages.error(request, "Error processing response from server", extra_tags='profile_menu')
                else:
                    messages.error(request, "No response from server", extra_tags='profile_menu')
        
        # Get current mapping data
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "MappingID", "ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete"
                FROM "ProfileMenuMapping" 
                WHERE "MappingID" = %s AND "IsDeleted" = FALSE
            """, [mapping_id])
            mapping_data = cursor.fetchone()
            
            if not mapping_data:
                messages.error(request, 'Profile menu mapping not found.', extra_tags='profile_menu')
                return redirect('profile_menu_mapping_list')
            
            mapping = dict(zip(['MappingID', 'ProfileID', 'MenuID', 'CanView', 'CanAdd', 'CanEdit', 'CanDelete'], mapping_data))
        
        # Get profiles and menus for dropdowns
        with connection.cursor() as cursor:
            cursor.execute('SELECT "ProfileID", "ProfileName" FROM "ProfileMaster" WHERE "IsDeleted" = FALSE')
            profiles = [dict(zip(['ProfileID', 'ProfileName'], row)) for row in cursor.fetchall()]
            
            cursor.execute('SELECT "MenuID", "MenuName" FROM "MenuMaster" WHERE "IsDeleted" = FALSE ORDER BY "MenuName"')
            menus = [dict(zip(['MenuID', 'MenuName'], row)) for row in cursor.fetchall()]
        
        context = {
            'mapping': mapping,
            'profiles': profiles,
            'menus': menus,
            'user': session_info
        }
        
        return render(request, 'core/profile_menu_mapping_edit.html', context)
        
    except Exception as e:
        logger.error(f"Error in profile_menu_mapping_edit: {e}")
        messages.error(request, 'An error occurred while editing profile menu mapping.', extra_tags='profile_menu')
        return redirect('profile_menu_mapping_list')


@custom_login_required
def profile_menu_mapping_delete(request, mapping_id):
    """Delete profile menu mapping"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions
        if profile_id not in [1, 2]:
            messages.error(request, 'Permission denied')
            return redirect('dashboard')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL Proc_ProfileMenuMapping_Manage(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                'DELETE',
                mapping_id,
                None, None, None, None, None, None,
                user_id,
                None
            ])
            
            result = cursor.fetchone()
            if result:
                try:
                    result_data = json.loads(result[0])
                    if result_data.get('status') == 'success':
                        messages.success(request, result_data.get('message', 'Mapping deleted successfully'), extra_tags='profile_menu')
                    else:
                        messages.error(request, result_data.get('message', 'Error deleting mapping'), extra_tags='profile_menu')
                except:
                    messages.error(request, "Error processing server response")
            else:
                messages.success(request, "Mapping deleted successfully")
        
        return redirect('profile_menu_mapping_list')
        
    except Exception as e:
        logger.error(f"Error in profile_menu_mapping_delete: {e}")
        messages.error(request, 'Error deleting mapping')
        return redirect('profile_menu_mapping_list')


@custom_login_required
def profile_menu_mapping_restore(request, mapping_id):
    """Restore profile menu mapping"""
    try:
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        if profile_id not in [1, 2]:
            messages.error(request, 'Permission denied')
            return redirect('dashboard')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL Proc_ProfileMenuMapping_Manage(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                'RESTORE',
                mapping_id,
                None, None, None, None, None, None,
                user_id,
                None
            ])
            
            result = cursor.fetchone()
            if result:
                try:
                    result_data = json.loads(result[0])
                    if result_data.get('status') == 'success':
                        messages.success(request, result_data.get('message', 'Mapping restored successfully'))
                    else:
                        messages.error(request, result_data.get('message', 'Error restoring mapping'))
                except:
                     messages.success(request, "Mapping restored successfully")
            else:
                messages.success(request, "Mapping restored successfully")
        
        return redirect('profile_menu_mapping_list')
        
    except Exception as e:
        logger.error(f"Error in profile_menu_mapping_restore: {e}")
        messages.error(request, 'Error restoring mapping')
        return redirect('profile_menu_mapping_list')


@custom_login_required
def profile_menu_mapping_debug(request):
    """Debug view to check session and user data"""
    try:
        session_info = _get_custom_session_info(request)
        debug_data = {
            'session_info': session_info,
            'request_cookies': dict(request.COOKIES),
            'request_session': dict(request.session),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': request.META.get('REMOTE_ADDR', ''),
        }
        return JsonResponse(debug_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
