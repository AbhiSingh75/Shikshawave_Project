from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from core.url_encryption import decrypt_id
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def update_section(request, section_id):
    """
    Update section details via AJAX
    """
    # Decrypt section_id
    decrypted_id = decrypt_id(section_id)
    if not decrypted_id:
        try:
            decrypted_id = int(section_id)
        except:
             return JsonResponse({'success': False, 'error': 'Invalid Section ID'}, status=400)
    section_id = decrypted_id

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        # Get user_id
        user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        # Parse JSON body
        data = json.loads(request.body)
        section_name = data.get('section_name', '').strip()
        capacity = data.get('capacity')
        room_number = data.get('room_number', '').strip()
        
        if not section_name:
            return JsonResponse({'success': False, 'error': 'Section name is required'}, status=400)
        
        # Update section
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE "SectionMaster"
                SET "SectionName" = %s,
                    "Capacity" = %s,
                    "RoomNumber" = %s,
                    "UpdatedBy" = %s,
                    "UpdatedAt" = CURRENT_TIMESTAMP
                WHERE "SectionID" = %s AND "IsDeleted" = FALSE
                RETURNING "SectionID"
            """, [section_name, capacity, room_number, user_id, section_id])
            
            result = cursor.fetchone()
            if result:
                return JsonResponse({'success': True, 'message': 'Section updated successfully'})
            else:
                return JsonResponse({'success': False, 'error': 'Section not found or already deleted'}, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error updating section {section_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def delete_section(request, section_id):
    """
    Soft delete section via AJAX
    """
    # Decrypt section_id
    decrypted_id = decrypt_id(section_id)
    if not decrypted_id:
        try:
             decrypted_id = int(section_id)
        except:
             return JsonResponse({'success': False, 'error': 'Invalid Section ID'}, status=400)
    section_id = decrypted_id

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        # Get user_id
        user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        # Soft delete section
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE "SectionMaster"
                SET "IsDeleted" = TRUE,
                    "UpdatedBy" = %s,
                    "UpdatedAt" = CURRENT_TIMESTAMP
                WHERE "SectionID" = %s AND "IsDeleted" = FALSE
                RETURNING "SectionID"
            """, [user_id, section_id])
            
            result = cursor.fetchone()
            if result:
                return JsonResponse({'success': True, 'message': 'Section deleted successfully'})
            else:
                return JsonResponse({'success': False, 'error': 'Section not found or already deleted'}, status=404)
    
    except Exception as e:
        logger.error(f"Error deleting section {section_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
