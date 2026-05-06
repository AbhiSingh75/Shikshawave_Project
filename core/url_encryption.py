from cryptography.fernet import Fernet
from django.conf import settings
import base64

def get_cipher():
    key = getattr(settings, 'URL_ENCRYPTION_KEY', b'8cozhW9kSi6zJQGLbZxQX-3bN5H9TqZ8xPqYvF5YFQM=')
    return Fernet(key)

def encrypt_id(id_value):
    cipher = get_cipher()
    encrypted = cipher.encrypt(str(id_value).encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_id(encrypted_value):
    """Decrypt an encrypted URL token back to the original string value."""
    if not encrypted_value:
        return None
    try:
        cipher = get_cipher()
        # Add padding if necessary
        padding = len(encrypted_value) % 4
        if padding > 0:
            encrypted_value += "=" * (4 - padding)
            
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    except Exception:
        return None


def decrypt_id_int(encrypted_value):
    """Decrypt an encrypted URL token and return as integer (for numeric IDs)."""
    result = decrypt_id(encrypted_value)
    if result is None:
        return None
    try:
        return int(result)
    except (ValueError, TypeError):
        return None
