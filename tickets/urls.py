from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Main views
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('view/<str:token>/', views.ticket_detail, name='ticket_detail'),
    
    # Actions
    path('assign/', views.ticket_assign, name='ticket_assign'),
    path('update-status/', views.ticket_update_status, name='ticket_update_status'),
    path('add-comment/', views.ticket_add_comment, name='ticket_add_comment'),
    
    # API endpoints
    path('api/list/', views.api_tickets_list, name='api_tickets_list'),
    path('api/support-executives/', views.api_support_executives, name='api_support_executives'),
    path('api/insights/', views.api_ticket_insights, name='api_ticket_insights'),
    
    # Attachment
    path('attachment/<str:token>/', views.ticket_attachment, name='ticket_attachment'),
]
