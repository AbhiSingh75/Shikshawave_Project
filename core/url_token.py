import hashlib
import time
from django.core.cache import cache
from django.conf import settings

def generate_token(id_value, prefix=''):
    """Generate short secure token for ID"""
    timestamp = str(int(time.time()))
    data = f"{id_value}:{timestamp}:{settings.SECRET_KEY}"
    token = hashlib.sha256(data.encode()).hexdigest()[:8]
    cache_key = f"token:{prefix}:{token}"
    cache.set(cache_key, id_value, timeout=3600)  # 1 hour
    return token

def resolve_token(token, prefix=''):
    """Resolve token back to ID"""
    cache_key = f"token:{prefix}:{token}"
    return cache.get(cache_key)
