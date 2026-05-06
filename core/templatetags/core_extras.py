from django import template
from core.url_encryption import encrypt_id as encrypt_id_func

register = template.Library()

@register.filter(name='encrypt_id')
def encrypt_id(value):
    """Encrypt an ID value for use in URLs"""
    if value is None:
        return ''
    return encrypt_id_func(value)

@register.filter(name='token')
def token(value, arg=None):
    """Alias for encrypt_id to support legacy or alternative naming"""
    return encrypt_id(value)

@register.filter(name='lookup')
def lookup(dictionary, key):
    """Lookup a key in a dictionary"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.simple_tag
def slot_exists(slots, day, period_id):
    """Check if a slot exists for given day and period"""
    for slot in slots:
        if slot.get('DayOfWeek') == int(day) and slot.get('PeriodID') == period_id:
            return True
    return False

@register.filter(name='split')
def split(value, arg):
    """Split a string by a delimiter"""
    return value.split(arg)

@register.filter(name='is_selected')
def is_selected(val1, val2):
    """Check if two values are equal as strings"""
    return str(val1) == str(val2)

@register.filter(name='trim')
def trim(value):
    """Strip whitespace from a string"""
    if isinstance(value, str):
        return value.strip()
    return value

@register.filter(name='safe_json')
def safe_json(value):
    """Convert a dictionary to a safe JSON string for JS attributes"""
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    return json.dumps(value, cls=DjangoJSONEncoder)
