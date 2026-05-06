from django.contrib import admin
from django.urls import path, include
from core import error_handlers

urlpatterns = [
    path('', include('core.urls')),
    path('notifications/', include('notifications.urls')),
]

# Custom error handlers
handler404 = error_handlers.custom_404
# handler500 = error_handlers.custom_500
handler403 = error_handlers.custom_403
handler400 = error_handlers.custom_400
