# core/url_security.py
"""
URL security utilities for obfuscating sensitive data in URLs.
Uses Django's cryptographic signing to create tamper-proof, opaque tokens.
"""
from django.core.signing import Signer, BadSignature, TimestampSigner
from django.template import Library
import base64
import hashlib

register = Library()

# Use TimestampSigner for expiring tokens (optional) or Signer for permanent tokens
_signer = Signer(salt='url-security-v1')


def encode_id(value):
    """
    Encode a value (student code, school ID, etc.) into a URL-safe opaque token.
    The token is signed to prevent tampering.
    """
    if not value:
        return ''
    signed = _signer.sign(str(value))
    # Make it URL-safe by base64 encoding
    return base64.urlsafe_b64encode(signed.encode()).decode()


def decode_id(token):
    """
    Decode an opaque token back to the original value.
    Returns None if the token is invalid or tampered with.
    """
    if not token:
        return None
    try:
        signed = base64.urlsafe_b64decode(token.encode()).decode()
        return _signer.unsign(signed)
    except (BadSignature, Exception):
        return None
