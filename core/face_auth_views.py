# core/face_auth_views.py
import json
import logging
import uuid
import base64
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views import View

from .face_recognition_service import FaceRecognitionService
from .liveness_detection import LivenessDetectionService
from .decorators import custom_login_required
from .auth_utils import _get_client_ip

logger = logging.getLogger(__name__)


@custom_login_required
def face_registration_page(request):
    """
    Face ID registration page for logged-in users.
    Users must be logged in to register their face template.
    Can accept encrypted user parameter to register face for a specific user (admin functionality).
    """
    # Get encrypted user ID from URL parameter (for admin registering face for other users)
    encrypted_user_id = request.GET.get('u')
    target_username = request.GET.get('username', '')
    
    # Default to current logged-in user
    current_user_id = request.session.get('UserId')
    current_username = request.session.get('UserName', '')
    
    # Determine which user we're registering face for
    if encrypted_user_id:
        try:
            # Decrypt the user ID (handle URL-safe base64)
            import base64
            # Convert URL-safe base64 back to standard base64
            standard_b64 = encrypted_user_id.replace('-', '+').replace('_', '/')
            # Add padding if needed
            while len(standard_b64) % 4:
                standard_b64 += '='
            
            decrypted = base64.b64decode(standard_b64.encode()).decode()
            # Extract user ID (format: "userid_timestamp")
            target_user_id = decrypted.split('_')[0]
            
            # Admin is registering face for another user
            registration_user_id = target_user_id
            registration_username = target_username
            is_admin_registration = True
        except Exception as e:
            logger.warning(f"Failed to decrypt user ID parameter: {e}")
            # If decryption fails, fall back to self-registration
            registration_user_id = str(current_user_id)
            registration_username = current_username
            is_admin_registration = False
    else:
        # User is registering their own face
        registration_user_id = str(current_user_id)
        registration_username = current_username
        is_admin_registration = False
    
    # Fetch registration user's details (specifically UserCode)
    registration_user_code = ""
    if registration_user_id and registration_user_id != 'None':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "UserCode" FROM "UserMaster" WHERE "UserID" = %s
                """, [registration_user_id])
                row = cursor.fetchone()
                if row:
                    registration_user_code = row[0]
        except Exception as e:
            logger.error(f"Error fetching UserCode for {registration_user_id}: {e}")

    context = {
        'page_title': 'Face ID Registration',
        'dark_mode': request.session.get('dark_mode', False),
        'registration_user_id': registration_user_id,
        'registration_user_code': registration_user_code,
        'registration_username': registration_username,
        'is_admin_registration': is_admin_registration,
        'current_user_id': str(current_user_id),
        'current_username': current_username,
    }
    return render(request, 'core/face_registration.html', context)



class FaceAuthenticationView(View):
    """Secure Face Authentication API View"""
    
    def __init__(self):
        super().__init__()
        self.face_service = FaceRecognitionService()
        self.liveness_service = LivenessDetectionService()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """Handle face authentication requests"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'authenticate':
                return self._handle_authentication(request, data)
            elif action == 'start_liveness':
                return self._handle_start_liveness(request, data)
            elif action == 'verify_liveness':
                return self._handle_verify_liveness(request, data)
            elif action == 'cleanup':
                return self._handle_cleanup(request, data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Face authentication error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Authentication service unavailable'
            }, status=500)
    
    def _handle_authentication(self, request, data):
        """Handle face authentication with profile photo comparison"""
        identifier = data.get('identifier', '').strip()
        face_descriptor = data.get('face_descriptor', [])
        reference_descriptor = data.get('reference_descriptor')
        session_id = data.get('session_id', '')
        
        if not identifier:
            return JsonResponse({
                'success': False,
                'error': 'Identifier is required'
            }, status=400)
        
        if not face_descriptor or len(face_descriptor) != 128:
            return JsonResponse({
                'success': False,
                'error': 'Valid face descriptor is required (128 dimensions)'
            }, status=400)
        
        # Check rate limiting
        rate_limit_result = self._check_rate_limit(identifier, request)
        if rate_limit_result['is_blocked']:
            return JsonResponse({
                'success': False,
                'error': f'Too many authentication attempts. Try again in {rate_limit_result["minutes_until_reset"]} minutes.',
                'rate_limited': True
            }, status=429)
        
        # 2. Liveness Detection Bypass (Requested for Ultra-Fast Login)
        # if not self.liveness_service.is_challenge_completed(session_id):
        #     logger.warning(f"Face authentication blocked: Liveness not verified for session {session_id}")
        #     return JsonResponse({
        #         'success': False,
        #         'error': 'Liveness verification required. Please complete the movement challenge.',
        #         'liveness_required': True
        #     }, status=403)

        logger.info(f"Face authentication attempt for identifier: {identifier}")
        
        # Perform face authentication using profile photo
        auth_result = self.face_service.authenticate_face(identifier, face_descriptor, request)
        
        if auth_result and auth_result.get('success'):
            # Authentication successful
            user_data = auth_result['user_data']
            similarity = auth_result['similarity']
            
            logger.info(f"Face authentication successful for user {user_data[1]} (ID: {user_data[0]}) - Similarity: {similarity:.2f}%")
            
            # Start actual Django session
            request.session['UserId'] = user_data[0]
            request.session['UserID'] = user_data[0]
            request.session['UserName'] = user_data[1]
            request.session['ProfileId'] = user_data[2]
            request.session['ProfileID'] = user_data[2]
            request.session['SchoolId'] = user_data[4]
            request.session['SchoolID'] = user_data[4]
            
            return JsonResponse({
                'success': True,
                'message': f'Welcome back, {user_data[1]}! Face authentication successful.',
                'similarity': round(similarity, 2),
                'redirect_url': '/dashboard/',
                'user': {
                    'name': user_data[1],
                    'profile': user_data[3],
                    'school': user_data[5]
                }
            })
        else:
            # Authentication failed or needs sync
            error_message = auth_result.get('error') if auth_result else 'Face authentication failed'
            needs_sync = auth_result.get('needs_sync', False) if auth_result else False
            similarity = auth_result.get('similarity', 0) if auth_result else 0
            
            logger.warning(f"Face authentication failed for identifier: {identifier} - {error_message}")
            return JsonResponse({
                'success': False,
                'error': error_message,
                'similarity': round(similarity, 2),
                'needs_sync': needs_sync,
                'fallback_available': True
            }, status=401 if not needs_sync else 200)

    def _handle_start_liveness(self, request, data):
        """Start liveness detection challenge"""
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        challenge = self.liveness_service.generate_liveness_challenge(session_id)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'challenge': challenge
        })
    
    def _handle_verify_liveness(self, request, data):
        """Verify liveness detection response"""
        session_id = data.get('session_id', '')
        response_data = data.get('response_data', {})
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID is required'
            }, status=400)
        
        result = self.liveness_service.verify_liveness_response(session_id, response_data)
        
        return JsonResponse(result)
    
    def _check_rate_limit(self, identifier, request):
        """Check authentication rate limiting"""
        ip_address = _get_client_ip(request)
        max_attempts = int(self._get_setting('MAX_AUTH_ATTEMPTS_PER_HOUR', '100'))
        
        try:
            with connection.cursor() as cursor:
                # Get user ID for identifier
                cursor.execute("""
                    SELECT "UserID" FROM "UserMaster" 
                    WHERE ("UserName" = %s OR "UserCode" = %s OR "Email" = %s) 
                      AND "IsActive" = TRUE AND COALESCE("IsDeleted", FALSE) = FALSE
                """, [identifier, identifier, identifier])
                
                user_row = cursor.fetchone()
                user_id = user_row[0] if user_row else None
                
                # Check rate limit using PostgreSQL function
                cursor.execute("SELECT * FROM \"Proc_FaceAuthRateLimit_Check\"(%s, %s, %s)", [user_id, ip_address, max_attempts])
                result = cursor.fetchone()
                
                if result:
                    return {
                        'is_blocked': result[0],
                        'current_attempts': result[1],
                        'max_attempts': result[2],
                        'minutes_until_reset': result[3]
                    }
                else:
                    return {'is_blocked': False, 'current_attempts': 0, 'max_attempts': max_attempts, 'minutes_until_reset': 0}
                    
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {'is_blocked': False, 'current_attempts': 0, 'max_attempts': max_attempts, 'minutes_until_reset': 0}
    
    def _get_setting(self, key, default_value):
        """Get face authentication setting from database"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT \"SettingValue\" FROM \"FaceAuthSettings\" WHERE \"SettingKey\" = %s AND \"IsActive\" = TRUE",
                    [key]
                )
                result = cursor.fetchone()
                return result[0] if result else default_value
        except Exception:
            return default_value
    
    def _handle_cleanup(self, request, data):
        """Handle cleanup of face authentication session data"""
        try:
            session_id = data.get('session_id', '')
            
            if session_id:
                # Clean up liveness detection data
                self.liveness_service.cleanup_session(session_id)
                
                # Clean up any cached face authentication data
                cache_key = f"face_auth_session_{session_id}"
                cache.delete(cache_key)
                
                logger.info(f"Face authentication session cleaned up: {session_id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Session cleaned up successfully'
            })
            
        except Exception as e:
            logger.error(f"Face authentication cleanup error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Cleanup failed'
            }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_user_photo(request):
    """Serve user profile photo as data URL for frontend processing"""
    try:
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip()
        
        if not identifier:
            return JsonResponse({'success': False, 'error': 'Identifier required'}, status=400)
            
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "UserPhoto" FROM "UserMaster" 
                WHERE ("UserName" = %s OR "UserCode" = %s OR "Email" = %s) 
                  AND "IsActive" = TRUE AND COALESCE("IsDeleted", FALSE) = FALSE
            """, [identifier, identifier, identifier])
            
            row = cursor.fetchone()
            if not row or not row[0]:
                return JsonResponse({'success': False, 'error': 'No profile photo found'}, status=404)
                
            photo_data = base64.b64encode(row[0]).decode('utf-8')
            return JsonResponse({
                'success': True,
                'photo_url': f"data:image/jpeg;base64,{photo_data}"
            })
    except Exception as e:
        logger.error(f"Error fetching user photo: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_face_template_secure(request):
    """
    Secure face template registration endpoint.
    SECURITY: Only authenticated users (with active session) can register face templates.
    Supports admin registration for other users via target_user_id parameter.
    Enforces 3-template limit per user.
    """
    try:
        data = json.loads(request.body)
        face_descriptor = data.get('face_descriptor', [])
        target_user_id = data.get('target_user_id')  # New parameter for admin registration
        
        # SECURITY: ONLY allow authenticated users - no bypass via identifier
        current_user_id = request.session.get('UserId')
        
        if not current_user_id:
            logger.warning("Face template registration attempted without authentication")
            return JsonResponse({
                'success': False,
                'error': 'Authentication required. Please login first to register for Face ID.'
            }, status=401)
        
        # Determine which user we're registering face for
        if target_user_id:
            # Admin is registering face for another user
            registration_user_id = target_user_id
            logger.info(f"Admin user {current_user_id} registering face template for user {target_user_id}")
        else:
            # User is registering their own face
            registration_user_id = str(current_user_id)
            logger.info(f"User {current_user_id} registering their own face template")
        
        if not face_descriptor or len(face_descriptor) != 128:
            return JsonResponse({
                'success': False,
                'error': 'Valid face descriptor is required (128 dimensions)'
            }, status=400)
        
        # Check current template count for the user
        face_service = FaceRecognitionService()
        existing_templates = face_service.get_user_templates(registration_user_id)
        active_template_count = len([t for t in existing_templates if t.get('is_active', True)])
        
        # Enforce 3-template limit
        if active_template_count >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Maximum of 3 face templates allowed per user. Please delete an existing template first.',
                'template_count': active_template_count,
                'max_templates': 3
            }, status=400)
        
        # Register new face template (without deleting existing ones)
        template_id = face_service.register_face_template(registration_user_id, face_descriptor, current_user_id)
        
        new_template_count = active_template_count + 1
        logger.info(f"Face template registered successfully for user {registration_user_id}, template ID: {template_id}, registered by: {current_user_id}, total templates: {new_template_count}")
        
        return JsonResponse({
            'success': True,
            'message': 'Face template registered successfully',
            'template_id': template_id,
            'registered_for_user': registration_user_id,
            'template_count': new_template_count,
            'max_templates': 3
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Face template registration error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Registration service unavailable'
        }, status=500)


@custom_login_required
@require_http_methods(["GET"])
def get_user_face_templates(request):
    """Get user's face templates (metadata only)"""
    try:
        current_user_id = request.session.get('UserId')
        
        # Support loading templates for a specific user (admin functionality)
        target_user_id = request.GET.get('user_id')
        
        # Determine which user's templates to load
        if target_user_id:
            # Admin is viewing templates for another user
            templates_user_id = target_user_id
            logger.info(f"Admin user {current_user_id} loading templates for user {target_user_id}")
        else:
            # User is viewing their own templates
            templates_user_id = current_user_id
        
        face_service = FaceRecognitionService()
        templates = face_service.get_user_templates(templates_user_id)
        
        template_list = []
        for template in templates:
            template_list.append({
                'id': template['id'],
                'version': template['version'],
                'is_corrupted': template.get('is_corrupted', False),
                'created_at': template['created_at'].isoformat() if template['created_at'] else None,
                'updated_at': template['updated_at'].isoformat() if template['updated_at'] else None
            })
        
        return JsonResponse({
            'success': True,
            'templates': template_list,
            'count': len(template_list),
            'templates_for_user': templates_user_id
        })
        
    except Exception as e:
        logger.error(f"Get face templates error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Service unavailable'
        }, status=500)


@custom_login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_face_template_secure(request, template_id):
    """Secure face template deletion endpoint"""
    try:
        current_user_id = request.session.get('UserId')
        
        # Support deleting templates for a specific user (admin functionality)
        # Parse request body to get target_user_id if provided
        target_user_id = None
        if request.body:
            try:
                data = json.loads(request.body)
                target_user_id = data.get('target_user_id')
            except json.JSONDecodeError:
                pass
        
        # Determine which user's template to delete
        if target_user_id:
            # Admin is deleting template for another user
            template_owner_id = target_user_id
            logger.info(f"Admin user {current_user_id} deleting template {template_id} for user {target_user_id}")
        else:
            # User is deleting their own template
            template_owner_id = current_user_id
        
        face_service = FaceRecognitionService()
        success = face_service.delete_face_template(template_id, template_owner_id, current_user_id)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Face template deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Template not found or already deleted'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Face template deletion error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Deletion service unavailable'
        }, status=500)


@custom_login_required
@require_http_methods(["GET"])
def face_auth_settings(request):
    """Get face authentication settings for frontend"""
    try:
        settings_data = {}
        
        # Get settings from database
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "SettingKey", "SettingValue", "Description" 
                FROM "FaceAuthSettings" 
                WHERE "IsActive" = TRUE
            """)
            
            for row in cursor.fetchall():
                key, value, description = row
                settings_data[key.lower()] = {
                    'value': value,
                    'description': description
                }
        
        # Add computed settings for frontend
        settings_data['frontend'] = {
            'similarity_threshold': float(settings_data.get('similarity_threshold', {}).get('value', '85.0')),
            'liveness_enabled': settings_data.get('liveness_detection_enabled', {}).get('value', 'true') == 'true',
            'max_templates': int(settings_data.get('max_templates_per_user', {}).get('value', '3'))
        }
        
        return JsonResponse({
            'success': True,
            'settings': settings_data
        })
        
    except Exception as e:
        logger.error(f"Get face auth settings error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Settings service unavailable'
        }, status=500)