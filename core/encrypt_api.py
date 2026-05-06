from django.http import JsonResponse
from .views import custom_login_required
from .url_encryption import encrypt_id

@custom_login_required
def encrypt_id_api(request):
    id_value = request.GET.get('id')
    if not id_value:
        return JsonResponse({'error': 'ID required'}, status=400)
    return JsonResponse({'encrypted': encrypt_id(id_value)})
