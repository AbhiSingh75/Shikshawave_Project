from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.import_dashboard, name='import_dashboard'),
    path('template/download/<str:import_type>/', views.download_template, name='download_template'),
    path('upload/', views.upload_file, name='upload_import_file'),
    path('preview/<int:import_id>/', views.preview_data, name='preview_import_data'),
    path('staging/preview/<int:import_id>/', views.get_staging_preview, name='get_staging_preview'),
    path('columns/<str:import_type>/', views.get_expected_columns, name='get_expected_columns'),
    path('grid/save/', views.save_grid_data, name='save_grid_data'),
    path('execute/<int:import_id>/', views.execute_import, name='execute_import'),
    path('status/<int:import_id>/', views.import_status, name='import_status'),
    path('errors/<int:import_id>/', views.download_errors, name='download_import_errors'),
]
