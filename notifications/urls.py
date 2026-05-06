from django.urls import path
from . import views

urlpatterns = [
    path('api/list/', views.get_notifications, name='notifications_list'),
    path('api/unread-count/', views.get_unread_count, name='notifications_unread_count'),
    path('api/mark-read/<int:notification_id>/', views.mark_as_read, name='notifications_mark_read'),
    path('api/mark-all-read/', views.mark_all_as_read, name='notifications_mark_all_read'),
]
