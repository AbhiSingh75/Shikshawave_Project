# SMTP Password Encryption Utility
# Uses Fernet (AES-128-CBC) encryption for secure password storage

from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib
import os

def get_encryption_key():
    """
    Get or generate encryption key from Django's SECRET_KEY.
    This derives a Fernet-compatible key from the Django secret key.
    """
    # Derive a 32-byte key from Django's SECRET_KEY using SHA-256
    secret = settings.SECRET_KEY.encode()
    # Use SHA-256 to generate a 32-byte key
    key = hashlib.sha256(secret).digest()
    # Fernet requires base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key)


def encrypt_smtp_password(password):
    """
    Encrypt SMTP password using Fernet (AES-128-CBC).
    
    Args:
        password: Plain text password string
        
    Returns:
        Encrypted password string (base64 encoded)
    """
    if not password:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()  # Return as string for database storage


def decrypt_smtp_password(encrypted_password):
    """
    Decrypt SMTP password.
    
    Args:
        encrypted_password: Encrypted password string from database
        
    Returns:
        Decrypted plain text password
    """
    if not encrypted_password:
        return None
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails, might be old format (Signer)
        # Try to handle legacy format
        try:
            from django.core.signing import Signer
            signer = Signer()
            return signer.unsign(encrypted_password)
        except Exception:
            # If all fails, return as-is (might be plain text legacy)
            return encrypted_password


def is_encrypted(value):
    """
    Check if a value appears to be Fernet encrypted.
    Fernet tokens start with 'gAAAAA' pattern.
    """
    if not value:
        return False
    return value.startswith('gAAAAA')
