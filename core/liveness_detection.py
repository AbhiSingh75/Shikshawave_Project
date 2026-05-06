# core/liveness_detection.py
import json
import logging
import time
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

class LivenessDetectionService:
    """
    Liveness Detection Service for anti-spoofing protection
    Implements blink detection and head movement verification
    """
    
    def __init__(self):
        self.blink_threshold = 0.25  # Eye aspect ratio threshold for blink detection
        self.head_movement_threshold = 15  # Degrees for head movement
        self.challenge_timeout = 30  # Seconds to complete liveness challenge
        self.max_attempts = 3
    
    def generate_liveness_challenge(self, session_id):
        """Generate a random liveness challenge for the user, or reuse existing valid one"""
        import random
        
        # Check if valid challenge already exists to avoid regeneration spam
        cache_key = f"liveness_challenge_{session_id}"
        existing_data = cache.get(cache_key)
        if existing_data and not existing_data.get('completed', False):
            logger.info(f"Reusing existing liveness challenge for session {session_id}")
            return existing_data['challenge']

        challenges = [
            {"type": "head_turn", "instruction": "Please look left then right", "directions": ["left", "right"]},
            {"type": "nod", "instruction": "Please look up and down", "movements": ["up", "down"]}
        ]
        
        challenge = random.choice(challenges)
        challenge_data = {
            "challenge": challenge,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "completed": False,
            "attempts": 0
        }
        
        # Store challenge in cache with timeout
        cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
        
        logger.info(f"Generated new liveness challenge for session {session_id}: {challenge['type']}")
        return challenge
    
    def verify_liveness_response(self, session_id, response_data):
        """Verify the user's response to the liveness challenge"""
        cache_key = f"liveness_challenge_{session_id}"
        challenge_data = cache.get(cache_key)
        
        if not challenge_data:
            logger.warning(f"Liveness challenge expired or not found for session {session_id}")
            return {"success": False, "error": "Challenge expired or not found"}
        
        challenge = challenge_data["challenge"]
        challenge_data["attempts"] += 1
        
        # Check max attempts
        if challenge_data["attempts"] > self.max_attempts:
            cache.delete(cache_key)
            logger.warning(f"Max liveness attempts exceeded for session {session_id}")
            return {"success": False, "error": "Maximum attempts exceeded"}
        
        try:
            if challenge["type"] == "blink":
                return self._verify_blink_challenge(challenge, response_data, challenge_data, cache_key)
            elif challenge["type"] == "head_turn":
                return self._verify_head_turn_challenge(challenge, response_data, challenge_data, cache_key)
            elif challenge["type"] == "smile":
                return self._verify_smile_challenge(challenge, response_data, challenge_data, cache_key)
            elif challenge["type"] == "nod":
                return self._verify_nod_challenge(challenge, response_data, challenge_data, cache_key)
            else:
                return {"success": False, "error": "Unknown challenge type"}
                
        except Exception as e:
            logger.error(f"Liveness verification error for session {session_id}: {e}")
            return {"success": False, "error": "Verification failed"}
    
    def _verify_blink_challenge(self, challenge, response_data, challenge_data, cache_key):
        """Verify blink detection challenge"""
        blink_count = response_data.get("blink_count", 0)
        eye_aspect_ratios = response_data.get("eye_aspect_ratios", [])
        
        # Analyze eye aspect ratios for blink patterns
        detected_blinks = 0
        if eye_aspect_ratios:
            for i in range(1, len(eye_aspect_ratios)):
                # Detect blink: significant drop in eye aspect ratio followed by recovery
                if (eye_aspect_ratios[i-1] > self.blink_threshold and 
                    eye_aspect_ratios[i] <= self.blink_threshold):
                    detected_blinks += 1
        
        required_blinks = challenge.get("required_blinks", 2)
        
        if detected_blinks >= required_blinks:
            challenge_data["completed"] = True
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            logger.info(f"Blink challenge passed: {detected_blinks}/{required_blinks} blinks detected")
            return {"success": True, "message": "Liveness verified - blink detection passed"}
        else:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {
                "success": False, 
                "error": f"Insufficient blinks detected: {detected_blinks}/{required_blinks}",
                "retry": True
            }
    
    def _verify_head_turn_challenge(self, challenge, response_data, challenge_data, cache_key):
        """Verify head turn challenge"""
        head_positions = response_data.get("head_positions", [])
        required_directions = challenge.get("directions", ["left", "right"])
        
        if not head_positions or len(head_positions) < 5:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {"success": False, "error": "Insufficient head movement data", "retry": True}
        
        # SWEEP DETECTION: Use range of movement (Max - Min)
        yaws = [p.get("yaw", 0) for p in head_positions]
        yaw_range = max(yaws) - min(yaws)
        
        # Check if required movement sweep was detected (e.g. 15 degrees instead of 20)
        movements_satisfied = yaw_range > 15
        
        if movements_satisfied:
            challenge_data["completed"] = True
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            logger.info(f"Head turn challenge passed: {detected_movements}")
            return {"success": True, "message": "Liveness verified - head movement detected"}
        else:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {
                "success": False,
                "error": f"Required head movements not detected. Need: {required_directions}",
                "retry": True
            }
    
    def _verify_smile_challenge(self, challenge, response_data, challenge_data, cache_key):
        """Verify smile detection challenge"""
        smile_confidence = response_data.get("smile_confidence", 0)
        smile_duration = response_data.get("smile_duration", 0)
        required_duration = challenge.get("duration", 2)
        
        if smile_confidence > 0.6 and smile_duration >= 0.8:
            challenge_data["completed"] = True
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            logger.info(f"Smile challenge passed: conf={smile_confidence}, dur={smile_duration}")
            return {"success": True, "message": "Liveness verified - smile detected"}
        else:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {
                "success": False, 
                "error": f"Smile not detected or duration too short (Confidence: {smile_confidence:.2f}, Duration: {smile_duration:.1f}s)",
                "retry": True
            }
    
    def _verify_nod_challenge(self, challenge, response_data, challenge_data, cache_key):
        """Verify head nod challenge"""
        head_positions = response_data.get("head_positions", [])
        required_movements = challenge.get("movements", ["up", "down"])
        
        if not head_positions or len(head_positions) < 5:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {"success": False, "error": "Insufficient head movement data", "retry": True}
        
        # SWEEP DETECTION: Use range of movement (Max - Min)
        pitches = [p.get("pitch", 0) for p in head_positions]
        pitch_range = max(pitches) - min(pitches)
        
        # Check if required movement sweep was detected (e.g. 8 degrees instead of 10)
        movements_satisfied = pitch_range > 8
        
        if movements_satisfied:
            challenge_data["completed"] = True
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            logger.info(f"Nod challenge passed: {detected_movements}")
            return {"success": True, "message": "Liveness verified - head nod detected"}
        else:
            cache.set(cache_key, challenge_data, timeout=self.challenge_timeout)
            return {
                "success": False,
                "error": f"Required head movements not detected. Need: {required_movements}",
                "retry": True
            }
    
    def is_challenge_completed(self, session_id):
        """Check if liveness challenge is completed for session"""
        cache_key = f"liveness_challenge_{session_id}"
        challenge_data = cache.get(cache_key)
        
        if challenge_data and challenge_data.get("completed", False):
            return True
        return False
    
    def cleanup_expired_challenges(self):
        """Cleanup expired liveness challenges (called by management command)"""
        # This would be implemented as a management command
        logger.info("Cleaning up expired liveness challenges")
    
    def cleanup_session(self, session_id):
        """Cleanup liveness detection data for a specific session"""
        try:
            cache_key = f"liveness_challenge_{session_id}"
            cache.delete(cache_key)
            logger.info(f"Cleaned up liveness session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup liveness session {session_id}: {e}")
            return False
        # Cache automatically handles expiration, but we could add additional cleanup logic
        logger.info("Liveness challenge cleanup completed")
        return True