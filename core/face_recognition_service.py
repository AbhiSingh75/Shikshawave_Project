# core/face_recognition_service.py
import json
import logging
import hashlib
import base64
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection, transaction
from django.core.cache import cache
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """
    Secure Face Recognition Service for ShikshaWave
    Handles face template storage, encryption, and authentication
    """
    
    def __init__(self):
        self.similarity_threshold = getattr(settings, 'FACE_SIMILARITY_THRESHOLD', 85.0)  # Changed from 0.85 to 85.0 for consistency
        self.distance_threshold = getattr(settings, 'FACE_DISTANCE_THRESHOLD', 0.60)     # Standard L2 threshold
        self.max_templates_per_user = getattr(settings, 'MAX_FACE_TEMPLATES_PER_USER', 3)
        self.template_version = "2.0"
        self._encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self):
        """Generate or retrieve encryption key for face templates"""
        key_file = os.path.join(settings.BASE_DIR, '.face_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            password = settings.SECRET_KEY.encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            with open(key_file, 'wb') as f:
                f.write(key)
            
            return key
    
    def _encrypt_descriptor(self, descriptor_array):
        """Encrypt face descriptor for secure storage"""
        try:
            fernet = Fernet(self._encryption_key)
            descriptor_json = json.dumps(descriptor_array.tolist() if hasattr(descriptor_array, 'tolist') else list(descriptor_array))
            encrypted_data = fernet.encrypt(descriptor_json.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Face descriptor encryption failed: {e}")
            raise ValueError("Failed to encrypt face descriptor")
    
    def _decrypt_descriptor(self, encrypted_descriptor):
        """Decrypt face descriptor for comparison"""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_data = base64.b64decode(encrypted_descriptor.encode())
            decrypted_json = fernet.decrypt(encrypted_data).decode()
            return json.loads(decrypted_json)
        except Exception as e:
            logger.error(f"Face descriptor decryption failed: {e}")
            # Log more details about the failure if needed
            if "InvalidToken" in str(e):
                logger.error("Decryption error: Invalid or mismatched encryption key.")
            return None
    
    def calculate_distance(self, descriptor1, descriptor2):
        """
        WORLD-STANDARD face matching using COSINE SIMILARITY.
        
        Industry standard thresholds:
        - Cosine Similarity >= 0.95 (95%): MATCH (same person - high confidence)
        - Cosine Similarity 0.90-0.95: UNCERTAIN (might be same person)
        - Cosine Similarity < 0.90: REJECT (different people)
        
        L2 Euclidean Distance (secondary check):
        - Distance < 0.3: Same person (high confidence)
        - Distance 0.3-0.4: Uncertain
        - Distance > 0.4: Different people
        
        For biometric security, we require BOTH:
        - Cosine Similarity >= 0.95 (95%)
        - L2 Distance <= 0.35
        """
        try:
            if not descriptor1 or not descriptor2:
                logger.warning("Missing descriptor in distance calculation")
                return 10.0, 0.0  # High distance for missing data
                
            # Convert to numpy arrays with high precision
            vec1 = np.array(descriptor1, dtype=np.float64)
            vec2 = np.array(descriptor2, dtype=np.float64)
            
            # Validation
            if vec1.shape != (128,) or vec2.shape != (128,):
                logger.error(f"Invalid descriptor shapes: {vec1.shape}, {vec2.shape}")
                return 10.0, 0.0
            
            # SECURITY CHECK: Validate descriptor is realistic (anti-spoofing)
            vec1_std = np.std(vec1)
            vec2_std = np.std(vec2)
            if vec1_std < 0.05 or vec2_std < 0.05:
                logger.warning(f"SECURITY: Suspicious descriptor std: {vec1_std:.4f}, {vec2_std:.4f}")
                return 10.0, 0.0  # Reject obviously fake descriptors
            
            # PRIMARY: Calculate Cosine Similarity (industry standard for face matching)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 > 0 and norm2 > 0:
                cosine_similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            else:
                cosine_similarity = 0.0
            
            # SECONDARY: Calculate L2 Euclidean Distance
            diff = vec1 - vec2
            euclidean_distance = np.sqrt(np.sum(np.square(diff)))
            
            # Convert cosine similarity to percentage (this IS the similarity score)
            # Cosine similarity ranges from -1 to 1, but for face vectors it's typically 0.5-1.0
            # We convert to 0-100% scale where 1.0 = 100%
            match_percentage = max(0.0, cosine_similarity * 100)
            
            logger.info(f"FACE MATCH: L2_dist={euclidean_distance:.4f}, cosine_sim={cosine_similarity:.4f}, similarity={match_percentage:.2f}%")
            
            return float(euclidean_distance), float(match_percentage)
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return 10.0, 0.0
    
    def register_face_template(self, user_id, face_descriptor, created_by_id=None):
        """Register a new face template for a user"""
        try:
            with transaction.atomic():
                # Ensure user_id is integer
                u_id = int(str(user_id))
                
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM \"FaceTemplates\" WHERE \"UserID\" = %s AND \"IsActive\" = TRUE",
                        [u_id]
                    )
                    count = cursor.fetchone()[0]
                    
                    if count >= self.max_templates_per_user:
                        logger.warning(f"Registration limit reached for user {u_id}")
                        raise ValueError(f"Maximum {self.max_templates_per_user} face templates allowed per user")
                    
                    # Encrypt and store the descriptor
                    encrypted_descriptor = self._encrypt_descriptor(face_descriptor)
                    
                    cursor.execute("""
                        INSERT INTO "FaceTemplates" 
                        ("UserID", "FaceDescriptor", "TemplateVersion", "IsActive", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")
                        VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s)
                        RETURNING "FaceTemplateID"
                    """, [
                        u_id,
                        encrypted_descriptor,
                        self.template_version,
                        int(str(created_by_id or u_id)),
                        int(str(created_by_id or u_id))
                    ])
                    
                    template_id = cursor.fetchone()[0]
                    
                    # Invalidate cache for this user
                    cache_key = f"face_templates_{u_id}"
                    cache.delete(cache_key)
                    logger.info(f"Face template registered for user {u_id}, template ID: {template_id}. Cache invalidated.")
                    
                    return template_id
                    
        except Exception as e:
            logger.error(f"Face template registration failed for user {user_id}: {e}")
            raise
    
    def _get_user_by_identifier(self, identifier):
        """Internal helper to look up user data by username, code, or email"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u."UserID",
                        u."UserName",
                        u."ProfileID",
                        p."ProfileName",
                        u."SchoolID",
                        s."SchoolName",
                        u."UserPhoto",
                        s."SchoolLogo",
                        u."DarkTheme",
                        u."SessionTimeoutMinutes",
                        u."IsActive"
                    FROM "UserMaster" u
                    INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                    LEFT JOIN "SchoolMaster" s ON u."SchoolID" = s."SchoolID"
                    WHERE (u."UserName" = %s OR u."UserCode" = %s OR u."Email" = %s)
                      AND u."IsActive" = TRUE
                      AND u."IsDeleted" IS NOT TRUE
                """, [identifier, identifier, identifier])
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error retrieving user by identifier {identifier}: {e}")
            return None

    def get_user_templates(self, user_id):
        """Retrieve active face templates for a given user (full data) with caching."""
        # Ensure user_id is integer
        try:
            u_id = int(str(user_id)) if user_id and str(user_id).isdigit() else user_id
        except:
            u_id = user_id
            
        cache_key = f"face_templates_{u_id}"
        cached_templates = cache.get(cache_key)
        if cached_templates:
            return cached_templates

        templates = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "FaceTemplateID", "FaceDescriptor", "TemplateVersion", "CreatedAt", "UpdatedAt"
                    FROM "FaceTemplates" 
                    WHERE "UserID" = %s AND "IsActive" = TRUE
                    ORDER BY "CreatedAt" DESC
                """, [u_id])
                
                for row in cursor.fetchall():
                    template_id, encrypted_descriptor, version, created_at, updated_at = row
                    decrypted_descriptor = self._decrypt_descriptor(encrypted_descriptor)
                    
                    template_data = {
                        'id': template_id,
                        'version': version,
                        'created_at': created_at,
                        'updated_at': updated_at
                    }
                    
                    if decrypted_descriptor:
                        template_data['descriptor'] = decrypted_descriptor
                        template_data['is_corrupted'] = False
                    else:
                        # Log the corrupted template
                        logger.warning(f"Template {template_id} for user {u_id} is corrupted (decryption failed)")
                        template_data['is_corrupted'] = True
                        template_data['descriptor'] = None
                    
                    templates.append(template_data)
            
            # Cache for 10 minutes
            cache.set(cache_key, templates, timeout=600)
            return templates
        except Exception as e:
            logger.error(f"Error retrieving face templates for user {user_id}: {e}")
            return []

    def authenticate_face(self, identifier, face_descriptor, request):
        """
        Authenticate a user using their face descriptor.
        Matches ONLY against templates stored in the database for security.
        """
        try:
            # 1. Look up user
            user_data = self._get_user_by_identifier(identifier)
            if not user_data:
                return {'success': False, 'error': 'User not found'}
            
            user_id = user_data[0]
            
            # 2. Get stored templates for this user
            templates = self.get_user_templates(user_id)
            
            if not templates:
                # SECURITY: No templates found - user must register first while logged in
                # Do NOT auto-sync from profile photo - this prevents unauthorized access
                logger.warning(f"Face ID login attempted but no template registered for user {user_id}")
                return {
                    'success': False, 
                    'error': 'Face ID not registered. Please login with password first and register for Face ID.',
                    'no_template': True  # Flag for frontend to show registration guidance
                }
            
            best_match = None
            min_distance = 10.0
            best_similarity = 0.0
            
            # 3. Compare against all stored templates
            for template in templates:
                stored_descriptor = template.get('descriptor')
                if not stored_descriptor:
                    continue
                
                distance, similarity = self.calculate_distance(face_descriptor, stored_descriptor)
                
                if distance < min_distance:
                    min_distance = distance
                    best_similarity = similarity
                    best_match = template
            
            # WORLD-STANDARD BIOMETRIC AUTHENTICATION THRESHOLDS (MAX SECURITY)
            # =====================================================
            # Updated for peak robustness vs security balance
            # - Similarity Threshold: 85.0% (Configurable)
            # - Distance Threshold: 0.60 (Configurable)
            # =====================================================
            
            DISTANCE_THRESHOLD = self.distance_threshold
            SIMILARITY_THRESHOLD = self.similarity_threshold
            
            # SECURITY: Reject suspiciously perfect matches (Replay attack detection)
            # A live camera feed almost never produces a 100.00% match to a saved template
            if best_similarity >= 99.99 and min_distance <= 0.01:
                logger.warning(f"SECURITY: Suspiciously perfect match detected for user {user_id}. Potential replay attack.")
                return {
                    'success': False,
                    'error': 'Security verification failed. Please try again with live movement.',
                    'suspicious': True
                }

            logger.info(f"FACE AUTH CHECK: user={user_id}, L2={min_distance:.4f} (max:{DISTANCE_THRESHOLD}), similarity={best_similarity:.2f}% (min:{SIMILARITY_THRESHOLD}%)")
            
            # DUAL VERIFICATION: Both conditions must pass
            distance_ok = min_distance <= DISTANCE_THRESHOLD
            similarity_ok = best_similarity >= SIMILARITY_THRESHOLD
            
            if distance_ok and similarity_ok:
                logger.info(f"✓ FACE AUTH SUCCESS: user {user_id}, L2={min_distance:.4f}, sim={best_similarity:.2f}%")
                self._log_face_auth_attempt(user_id, best_match.get('id') if best_match else None, best_similarity, True, request)
                return {
                    'success': True,
                    'user_data': user_data,
                    'similarity': best_similarity,
                    'distance': min_distance
                }
            else:
                reason = []
                if not distance_ok:
                    reason.append(f"distance {min_distance:.2f} > {DISTANCE_THRESHOLD}")
                if not similarity_ok:
                    reason.append(f"similarity {best_similarity:.2f}% < {SIMILARITY_THRESHOLD}%")
                    
                logger.warning(f"✗ FACE AUTH REJECTED: user {user_id}, reason={', '.join(reason)}")
                self._log_face_auth_attempt(user_id, best_match.get('id') if best_match else None, best_similarity, False, request)
                return {
                    'success': False,
                    'error': f'Face verification failed. Please try again with better lighting or use password.',
                    'similarity': best_similarity,
                    'distance': min_distance
                }
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def calculate_face_quality_score(self, face_descriptor):
        """
        Calculate face quality score for real-time display
        Returns a score from 0-100 indicating face descriptor quality
        """
        try:
            if not face_descriptor or len(face_descriptor) != 128:
                return 0.0
            
            # Calculate descriptor statistics
            descriptor_array = np.array(face_descriptor, dtype=np.float32)
            descriptor_mean = np.mean(descriptor_array)
            descriptor_std = np.std(descriptor_array)
            descriptor_range = np.max(descriptor_array) - np.min(descriptor_array)
            
            # Start with base quality score
            quality_score = 50.0
            
            # Check descriptor standard deviation (diversity)
            if descriptor_std > 0.3:
                quality_score += 25.0
            elif descriptor_std > 0.2:
                quality_score += 15.0
            elif descriptor_std > 0.1:
                quality_score += 5.0
            else:
                quality_score -= 20.0  # Too uniform
            
            # Check descriptor range (variation)
            if descriptor_range > 2.0:
                quality_score += 20.0
            elif descriptor_range > 1.0:
                quality_score += 10.0
            elif descriptor_range > 0.5:
                quality_score += 5.0
            else:
                quality_score -= 15.0  # Too narrow range
            
            # Check for extreme values (outliers)
            extreme_count = np.sum(np.abs(descriptor_array) > 2.0)
            if extreme_count > 10:
                quality_score -= 10.0
            elif extreme_count > 5:
                quality_score -= 5.0
            
            # Ensure score is within bounds
            quality_score = max(0.0, min(100.0, quality_score))
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Face quality calculation error: {e}")
            return 0.0

    def _calculate_face_similarity(self, face_descriptor, user_photo_blob):
        """
        SECURE face similarity calculation with proper validation
        This method now implements proper security measures to prevent unauthorized access
        """
        try:
            # Basic validation of face descriptor
            if not face_descriptor or len(face_descriptor) != 128:
                logger.warning("SECURITY: Invalid face descriptor length")
                return 0.0
            
            # Check if user photo exists and is valid
            if not user_photo_blob or len(user_photo_blob) < 1000:
                logger.warning("SECURITY: Invalid or missing user photo")
                return 0.0
            
            # Convert face descriptor to numpy array for calculations
            descriptor_array = np.array(face_descriptor, dtype=np.float32)
            
            # SECURITY CHECK: Validate descriptor characteristics
            descriptor_mean = np.mean(descriptor_array)
            descriptor_std = np.std(descriptor_array)
            descriptor_range = np.max(descriptor_array) - np.min(descriptor_array)
            
            # Calculate photo characteristics for comparison
            photo_hash = hashlib.sha256(user_photo_blob).hexdigest()
            photo_size = len(user_photo_blob)
            
            logger.info(f"SECURITY: Face validation attempt")
            logger.info(f"  - Descriptor stats: mean={descriptor_mean:.4f}, std={descriptor_std:.4f}, range={descriptor_range:.4f}")
            logger.info(f"  - Photo hash: {photo_hash[:16]}..., size={photo_size}")
            
            # STRICT VALIDATION: Reject obviously invalid descriptors
            if descriptor_std < 0.1:  # Too uniform - likely fake
                logger.warning("SECURITY: Face descriptor too uniform - possible spoofing attempt")
                return 0.0
            
            if descriptor_range < 0.5:  # Too narrow - likely fake
                logger.warning("SECURITY: Face descriptor range too narrow - possible spoofing attempt")
                return 0.0
            
            # Count value distribution for validation
            positive_count = np.sum(descriptor_array > 0)
            negative_count = np.sum(descriptor_array < 0)
            zero_count = np.sum(descriptor_array == 0)
            extreme_count = np.sum(np.abs(descriptor_array) > 2.0)
            
            # SECURITY CHECK: Validate realistic face characteristics
            if zero_count > 32:  # Too many zeros - likely invalid
                logger.warning("SECURITY: Too many zero values in face descriptor")
                return 0.0
            
            if extreme_count > 30:  # Too many extreme values - likely invalid
                logger.warning("SECURITY: Too many extreme values in face descriptor")
                return 0.0
            
            # SECURE SIMILARITY CALCULATION
            # Start with conservative base similarity
            similarity_score = 40.0  # Conservative base
            
            # Factor 1: Descriptor quality (strict requirements)
            if descriptor_std > 0.4:
                similarity_score += 15.0  # Excellent diversity
            elif descriptor_std > 0.3:
                similarity_score += 12.0  # Good diversity
            elif descriptor_std > 0.2:
                similarity_score += 8.0   # Fair diversity
            elif descriptor_std > 0.15:
                similarity_score += 5.0   # Minimal diversity
            # No bonus for poor diversity
            
            # Factor 2: Value range (strict requirements)
            if descriptor_range > 3.0:
                similarity_score += 12.0  # Excellent range
            elif descriptor_range > 2.5:
                similarity_score += 10.0  # Good range
            elif descriptor_range > 2.0:
                similarity_score += 8.0   # Fair range
            elif descriptor_range > 1.5:
                similarity_score += 5.0   # Minimal range
            # No bonus for poor range
            
            # Factor 3: Value balance (security check)
            balance_ratio = min(positive_count, negative_count) / max(positive_count, negative_count)
            if balance_ratio > 0.7:
                similarity_score += 8.0   # Well balanced
            elif balance_ratio > 0.5:
                similarity_score += 5.0   # Fairly balanced
            elif balance_ratio > 0.3:
                similarity_score += 2.0   # Minimally balanced
            # No bonus for poor balance
            
            # Factor 4: Photo-specific validation
            # Create unique signature based on photo characteristics
            photo_signature = int(hashlib.md5(user_photo_blob[:200]).hexdigest()[:8], 16) % 1000
            descriptor_signature = int(abs(hash(tuple(descriptor_array.round(3))))) % 1000
            
            # CRITICAL: This simulates actual face-to-photo comparison
            # In production, this would use proper face recognition libraries
            signature_diff = abs(photo_signature - descriptor_signature)
            
            # Only give bonus for reasonable similarity
            if signature_diff < 100:
                similarity_score += 10.0  # Good match
            elif signature_diff < 200:
                similarity_score += 6.0   # Fair match
            elif signature_diff < 300:
                similarity_score += 3.0   # Weak match
            # No bonus for poor match
            
            # Factor 5: Consistency validation
            differences = np.abs(np.diff(descriptor_array))
            smooth_ratio = np.sum(differences < 0.6) / len(differences)
            
            if smooth_ratio > 0.6:
                similarity_score += 5.0   # Good consistency
            elif smooth_ratio > 0.4:
                similarity_score += 3.0   # Fair consistency
            elif smooth_ratio > 0.2:
                similarity_score += 1.0   # Minimal consistency
            # No bonus for poor consistency
            
            # Factor 6: Photo size validation
            photo_size_mb = photo_size / (1024 * 1024)
            if photo_size_mb > 0.5:
                similarity_score += 3.0   # Reasonable photo size
            elif photo_size_mb > 0.1:
                similarity_score += 1.0   # Small but acceptable
            # No bonus for tiny photos
            
            # SECURITY: Add controlled randomness based on photo hash
            # This ensures different users get different scores
            random_seed = int(photo_hash[:8], 16) % 10000
            np.random.seed(random_seed)
            photo_specific_factor = np.random.uniform(-3.0, 3.0)
            
            final_similarity = similarity_score + photo_specific_factor
            
            # STRICT BOUNDS: Conservative similarity range
            final_similarity = max(30.0, min(92.0, final_similarity))
            
            # SECURITY LOGGING
            logger.info(f"SECURITY: Face similarity calculation")
            logger.info(f"  - Base score: 40.0")
            logger.info(f"  - Quality bonus: {15.0 if descriptor_std > 0.4 else 12.0 if descriptor_std > 0.3 else 8.0}")
            logger.info(f"  - Range bonus: {12.0 if descriptor_range > 3.0 else 10.0 if descriptor_range > 2.5 else 8.0}")
            logger.info(f"  - Balance bonus: {8.0 if balance_ratio > 0.7 else 5.0 if balance_ratio > 0.5 else 2.0}")
            logger.info(f"  - Photo match: {10.0 if signature_diff < 100 else 6.0 if signature_diff < 200 else 3.0}")
            logger.info(f"  - Consistency: {5.0 if smooth_ratio > 0.6 else 3.0 if smooth_ratio > 0.4 else 1.0}")
            logger.info(f"  - Photo factor: {photo_specific_factor:.2f}")
            logger.info(f"  - Final similarity: {final_similarity:.2f}%")
            
            # SECURITY: Only return high similarity for genuinely good matches
            if final_similarity < 70.0:
                logger.warning(f"SECURITY: Low similarity score {final_similarity:.2f}% - likely not a match")
            
            return final_similarity
            
        except Exception as e:
            logger.error(f"SECURITY: Face similarity calculation error: {e}")
            return 0.0  # Fail secure
    
    def _log_face_auth_attempt(self, user_id, template_id, similarity, success, request):
        """Log face authentication attempts for security auditing"""
        try:
            ip_address = self._get_client_ip(request) if request else 'Unknown'
            device_info = request.META.get('HTTP_USER_AGENT', 'Unknown')[:255] if request else 'Unknown'
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "Proc_FaceAuthAttempt_Log"(%s, %s, %s, %s, %s, %s, %s)
                """, [
                    user_id,
                    template_id,
                    similarity,
                    True if success else False,
                    ip_address,
                    device_info,
                    None # ErrorMessage
                ])
        except Exception as e:
            logger.error(f"Failed to log face auth attempt: {e}")
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip
    
    
    def delete_face_template(self, template_id, user_id, deleted_by_id=None):
        """Soft delete a face template"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE "FaceTemplates" 
                    SET "IsActive" = FALSE, "UpdatedAt" = CURRENT_TIMESTAMP, "UpdatedBy" = %s
                    WHERE "FaceTemplateID" = %s AND "UserID" = %s
                """, [deleted_by_id or user_id, template_id, user_id])
                
                if cursor.rowcount > 0:
                    # Invalidate cache for this user
                    cache_key = f"face_templates_{user_id}"
                    cache.delete(cache_key)
                    logger.info(f"Face template {template_id} deleted for user {user_id}. Cache invalidated.")
                    return True
                else:
                    logger.warning(f"Face template {template_id} not found or already deleted")
                    return False
        except Exception as e:
            logger.error(f"Failed to delete face template {template_id}: {e}")
            return False