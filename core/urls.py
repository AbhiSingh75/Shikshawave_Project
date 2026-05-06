from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from . import views, user_views, school_views, menus_views, section_api_views, student_promote_views, email_templates_views as email_tpl_views
from . import dashboard_views
from . import class_management_views
from . import student_views
from . import exam_views
from . import exam_timetable_views
from . import exam_result_views
from . import subscription_views
from . import salary_views
from . import template_views
from . import encrypt_api
from . import admission_instructions_views
from . import terms_conditions_views
from . import academic_year_views
from . import id_card_views
from . import fee_receipt_view
from . import salary_component_views
from . import staff_attendance_views
from . import smtp_config_views
from . import school_views # Ensure school_views is imported explicitly if needed, though usually covered by .
from . import payment_account_views
from .face_auth_views import (
    FaceAuthenticationView, 
    register_face_template_secure, 
    get_user_face_templates, 
    delete_face_template_secure, 
    face_auth_settings,
    get_user_photo,
    face_registration_page
)
from . import salary_slip_preview
from . import document_views
from . import admission_views
from .user_settings_view import user_settings
from .otp_template_views import otp_template_management, set_active_otp_template, preview_otp_template
from . import subject_views
from . import timetable_views
from . import leave_management_views as leave_views
from .staff_detail_view import staff_detail, update_staff_personal, update_staff_contact, update_staff_salary, update_staff_document, get_teacher_timetable, get_subject_list, update_staff_subjects
from . import fee_type_views as fee_views
from . import brand_profile_views
from . import holiday_views

def favicon_view(request):
    """Serve favicon.ico - Simple blue square favicon"""
    # Simple 16x16 blue square favicon
    # Replaced bytes literal with fromhex to avoid null byte issues in source file
    favicon_data = bytes.fromhex('0000010001001010000001002000680400001600000028000000100000002000000001002000000000000004000000000000000000000000000000000000')
    return HttpResponse(favicon_data, content_type='image/x-icon')

from . import Student_Fee_management_Views
urlpatterns = [
    path('favicon.ico', cache_control(max_age=86400)(favicon_view), name='favicon'),
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('add-user/', views.add_user_view, name='add_user'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('set-dark-mode/', views.set_dark_mode, name='set_dark_mode'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('api/school-list/', school_views.get_school_list_api, name='school_list_api'),
    path('settings/', user_settings, name='user_settings'),
    path('users/create/', user_views.create_user, name='create_user'),
    path('users/list/load-more/', user_views.load_more_users, name='load_more_users'),
    path('users/list/', user_views.user_list, name='user_list'),
    path('users/export/', user_views.users_export, name='users_export'),
    path('load-more-users/', user_views.load_more_users, name='load_more_users'),
    path('schools/create/', school_views.schools_create, name='schools_create'),
    path('schools/list/', school_views.schools_list, name='schools_list'),
    path('schools/export/', school_views.schools_export, name='schools_export'),
    path('schools/edit/<str:encrypted_id>/', school_views.school_update, name='school_update'),
    path('schools/update/<str:encrypted_id>/', school_views.school_update_submit, name='school_update_submit'),
    path('schools/<int:school_id>/delete/', school_views.school_soft_delete, name='school_soft_delete'),
    path('schools/<int:school_id>/restore/', school_views.school_restore, name='school_restore'),
    path('schools/<int:school_id>/stats/', school_views.school_stats, name='school_stats'),
    path('users/<str:encrypted_id>/update/', user_views.update_user, name='update_user'),
    path('users/<int:user_id>/delete/', user_views.user_soft_delete, name='user_soft_delete'),
    path('users/<int:user_id>/restore/', user_views.user_restore, name='user_restore'),
    path('users/<int:user_id>/password/', user_views.get_user_password, name='get_user_password'),
    
    # Blocked Users Management
    path('users/blocked/', user_views.blocked_users_list, name='blocked_users_list'),
    path('users/unblock/<int:user_id>/', user_views.unblock_user, name='unblock_user'),
    path('users/admin-password-reset/', user_views.admin_password_reset, name='admin_password_reset'),
    
    path('api/geo/countries/', views.api_countries, name='api_countries'),
    path('api/geo/states/', views.api_states, name='api_states'),
    path('api/geo/districts/', views.api_districts, name='api_districts'),
    path('api/classes/', student_promote_views.api_classes, name='api_classes'),
    path('api/sections/', student_promote_views.api_sections, name='api_sections'),
    path('api/students/', student_promote_views.api_students, name='api_students'),
    path('api/academic-years/', student_promote_views.api_academic_years, name='api_academic_years'),
    path('api/boards/', views.api_boards, name='api_boards'),
    path('api/mediums/', views.api_mediums, name='api_mediums'),
    path('api/dashboard/students/', dashboard_views.api_dashboard_students, name='api_dashboard_students'),
    path('api/staff-profiles/', dashboard_views.api_staff_profiles, name='api_staff_profiles'),
    path('api/dashboard/employees/', dashboard_views.api_dashboard_employees, name='api_dashboard_employees'),
    path('api/dashboard/attendance/', dashboard_views.api_dashboard_attendance, name='api_dashboard_attendance'),
    path('api/dashboard/attendance/trend/', dashboard_views.api_dashboard_attendance_trend, name='api_dashboard_attendance_trend'),
    path('api/dashboard/staff-attendance/', dashboard_views.api_dashboard_staff_attendance, name='api_dashboard_staff_attendance'),
    path('api/dashboard/expense/', dashboard_views.api_dashboard_expense, name='api_dashboard_expense'),
    path('api/dashboard/revenue/', dashboard_views.api_dashboard_revenue, name='api_dashboard_revenue'),
    path('api/dashboard/ticket-stats/', dashboard_views.api_dashboard_ticket_stats, name='api_dashboard_ticket_stats'),
    path('api/dashboard/subscription-revenue/', dashboard_views.api_dashboard_subscription_revenue, name='api_dashboard_subscription_revenue'),
    path('api/user-menus/', dashboard_views.api_user_menus, name='api_user_menus'),     
    path('api/check-aadhaar-duplicate/', views.check_aadhaar_duplicate, name='check_aadhaar_duplicate'),
    path('admission/new/', admission_views.student_admission, name='student_admission'),  
    path('admission/get-monthly-fees/', admission_views.get_monthly_fee_types, name='get_monthly_fee_types'),
    
    # Master Data - Payment Accounts
    path('master-data/payment-accounts/', payment_account_views.payment_account_list, name='payment_account_list'),
    path('master-data/payment-accounts/save/', payment_account_views.save_payment_account, name='payment_account_save'),
    path('master-data/payment-accounts/delete/', payment_account_views.delete_payment_account, name='payment_account_delete'),
    
    # Master Data - Brand Profile
    path('master-data/brand-profile/', brand_profile_views.brand_profile_management, name='brand_profile_management'),

    path('admission/payment/', admission_views.payment_page, name='payment_page'),
    path('admission/complete/', admission_views.admission_complete, name='admission_complete'),
    path('admission/print-ack/', admission_views.print_acknowledgment, name='print_acknowledgment'),
    path('admission/print-receipt/', admission_views.print_receipt, name='print_receipt'),
    path('admission/clear-receipt/', admission_views.clear_receipt_session, name='clear_receipt_session'),
    path('admission/applicants/', admission_views.view_applications, name='admission_applicants'),
    path('applications/', admission_views.view_applications, name='view_applications'),
    path('applications/<str:encrypted_code>/', admission_views.view_application_detail, name='view_application_detail'),
    path('api/student/update-section/', admission_views.update_student_section, name='update_student_section'),
    path('api/student/update-documents/', admission_views.update_student_documents, name='update_student_documents'),
    path('applications/load-more/', admission_views.load_more_applications, name='load_more_applications'),
    path('accounts/login/', views.login_view, name='accounts_login'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),

    # User validation API for face authentication
    path('api/validate-user/', user_views.validate_user_api, name='validate_user_api'),
    
    # Secure Face Authentication API endpoints
    path('api/face-auth/', FaceAuthenticationView.as_view(), name='face_auth_api'),
    path('api/face-auth/cleanup/', FaceAuthenticationView.as_view(), name='face_auth_cleanup'),
    path('api/face-template/register/', register_face_template_secure, name='register_face_template_secure'),
    path('api/face-template/list/', get_user_face_templates, name='get_user_face_templates'),
    path('api/face-template/delete/<int:template_id>/', delete_face_template_secure, name='delete_face_template_secure'),
    path('api/face-auth/settings/', face_auth_settings, name='face_auth_settings'),
    
    # Face ID Registration Page (for logged-in users only)
    path('face-registration/', face_registration_page, name='face_registration'),
    
    # Legacy Face Template API endpoints (deprecated)
    path('api/register-face-template/', views.register_face_template, name='register_face_template'),
    path('api/register-face-template-by-identifier/', views.register_face_template_by_identifier, name='register_face_template_by_identifier'),
    path('api/get-face-template/', views.get_face_template_by_identifier, name='get_face_template_by_identifier'),
    path('api/face-template/get-photo/', get_user_photo, name='get_user_photo_api'),
    
    # Email Queue Monitoring
    path('admin/email-queue/', views.email_queue_status, name='email_queue_status'),
    path('api/email-queue-status/', views.email_queue_status_api, name='email_queue_status_api'),
    path('admin/email-queue/retry/', views.retry_failed_emails, name='retry_failed_emails'),
    path('admin/email-queue/cleanup/', views.cleanup_old_emails, name='cleanup_old_emails'),
    path('admin/email-queue/debug/', views.email_track_debug, name='email_track_debug'),
    
    # Global APIs
    path('api/school-dropdown/', views.school_dropdown_api, name='school_dropdown_api'),
    path('api/user/photo/<str:user_id>/', views.serve_user_photo, name='serve_user_photo'),
    path('api/school/logo/<str:school_id>/', views.serve_school_logo, name='serve_school_logo'),
    path('api/themes/', user_views.get_themes_api, name='get_themes_api'),
    path('api/set-theme/', user_views.update_theme_api, name='update_theme_api'),

    # Student Management URLs
    path('students/list/', student_views.view_students, name='view_students'),
    path('students/cards/', student_views.view_students_cards, name='view_students_cards'),
    path('students/export/', student_views.students_export, name='students_export'),
    path('students/profile/', views.student_profile, name='student_profile'),
    path('students/promote/', student_promote_views.promote_students, name='promote_students'),
    path('students/promote/submit/', student_promote_views.promote_students_submit, name='promote_students_submit'),
    
    # Employee Management URLs
    path('employees/add/', views.add_employee_view, name='add_employee'),
    path('employees/add/submit/', views.add_employee_submit, name='add_employee_submit'),
    path('employees/export/', views.export_teachers, name='export_teachers'),
    path('employees/print-acknowledgment/', views.print_employee_acknowledgment, name='print_employee_acknowledgment'),
    path('employees/print-job-letter/', template_views.print_job_letter, name='print_job_letter'),
    path('employees/check-national-id/', views.check_national_id, name='check_national_id'),
    path('teachers/list/', views.view_teachers, name='view_teachers'),
    path('staff/list/', views.view_teachers, name='view_staff'),
    path('staff/get-teacher-timetable/', get_teacher_timetable, name='get_teacher_timetable'),
    path('staff/<str:token>/', staff_detail, name='staff_detail'),
    path('staff/<str:token>/update-personal/', update_staff_personal, name='update_staff_personal'),
    path('staff/<str:token>/update-contact/', update_staff_contact, name='update_staff_contact'),
    path('staff/<str:token>/get-subject-list/', get_subject_list, name='get_subject_list'),
    path('staff/<str:token>/update-subjects/', update_staff_subjects, name='update_staff_subjects'),
    path('staff/<str:token>/update-salary/', update_staff_salary, name='update_staff_salary'),
    path('staff/<str:token>/update-document/', update_staff_document, name='update_staff_document'),
    path('staff/assign-classes/', views.assign_classes_view, name='assign_classes'),
    path('staff/assign-classes/submit/', views.assign_classes_submit, name='assign_classes_submit'),
    path('staff/assign-classes/test/', views.assign_classes_test, name='assign_classes_test'),
    path('staff/view-assign-class/', views.view_assign_class, name='view_assign_class'),
    path('api/subjects-by-class/', views.get_subjects_by_class, name='get_subjects_by_class'),
    path('api/check-class-teacher/', views.check_class_teacher_conflict, name='check_class_teacher_conflict'),
    
    # Class Management URLs
    path('class/add/', class_management_views.add_class, name='add_class'),
    path('class/view/', class_management_views.view_class, name='view_class'),
    path('class/<str:class_id>/sections/', class_management_views.get_class_sections, name='get_class_sections'),
    path('class/<str:class_id>/data/', class_management_views.get_class_data, name='get_class_data'),
    path('class/<str:class_id>/edit/', class_management_views.edit_class, name='edit_class'),
    path('class/<str:class_id>/update/', class_management_views.update_class, name='update_class'),
    path('class/<str:class_id>/delete/', class_management_views.delete_class, name='delete_class'),
    path('class/<str:class_id>/restore/', class_management_views.restore_class, name='restore_class'),
    path('section/<str:section_id>/update/', section_api_views.update_section, name='update_section'),
    path('section/<str:section_id>/delete/', section_api_views.delete_section, name='delete_section'),
    
    # Student Attendance URLs
    path('attendance/mark/', views.student_attendance, name='student_attendance'),
    path('attendance/view/', views.view_attendance, name='view_attendance'),
    path('attendance/load-students/', views.load_students_ajax, name='load_students_ajax'),
    path('attendance/submit/', views.submit_attendance_ajax, name='submit_attendance_ajax'),
    
    # Staff Attendance URLs
    path('attendance/mark-employee/', staff_attendance_views.mark_staff_attendance, name='mark_staff_attendance'),
    path('attendance/view-employee/', staff_attendance_views.view_staff_attendance, name='view_staff_attendance'),
    path('attendance/approve-employee/', staff_attendance_views.approve_staff_attendance, name='pending_staff_attendance'),
    path('attendance/approve-ajax/', staff_attendance_views.approve_attendance_ajax, name='approve_attendance_ajax'),
    path('api/school-employees/', staff_attendance_views.get_school_employees, name='get_school_employees'),
    
    # Fee Collection URLs
    path('fees/collect/', Student_Fee_management_Views.fee_collection_new, name='fee_collection'),  # Redirect old URL to new page
    path('fees/collect-new/', Student_Fee_management_Views.fee_collection_new, name='fee_collection_new'),
    path('fees/get-student-fee-details/', Student_Fee_management_Views.get_student_fee_details, name='get_student_fee_details'),
    path('fees/get-student-fee-history/', Student_Fee_management_Views.get_student_fee_history, name='get_student_fee_history'),
    path('fees/submit-fee-collection/', Student_Fee_management_Views.submit_fee_collection, name='submit_fee_collection'),
    path('fees/collect-new/submit/', Student_Fee_management_Views.fee_collection_new_submit, name='fee_collection_new_submit'),
    path('fees/receipt/', Student_Fee_management_Views.fee_collection_receipt, name='fee_collection_receipt'),
    path('api/get-receipt-data/', Student_Fee_management_Views.get_receipt_data, name='get_receipt_data'),
    path('fees/clear-receipt/', Student_Fee_management_Views.clear_fee_receipt_session, name='clear_fee_receipt_session'),
    path('fees/receipt/<str:receipt_id>/', Student_Fee_management_Views.fee_receipt_view, name='fee_receipt_view'),
    path('fees/receipt/<str:receipt_id>/print/', Student_Fee_management_Views.print_fee_receipt, name='print_fee_receipt'),
    path('fees/generate-receipt/', Student_Fee_management_Views.generate_fee_receipt, name='generate_fee_receipt'),
    path('fees/test-procedure/', Student_Fee_management_Views.test_receipt_procedure, name='test_receipt_procedure'),
    path('fees/test-session-receipt/', Student_Fee_management_Views.test_fee_receipt_with_session, name='test_fee_receipt_with_session'),
    
    # Fee Report URLs
    path('fees/reports/', Student_Fee_management_Views.fee_report, name='fee_report'),
    path('fees/reports/ajax/', Student_Fee_management_Views.fee_report_ajax, name='fee_report_ajax'),
    path('fees/reports/export/', Student_Fee_management_Views.fee_report_export, name='fee_report_export'),
    
    # Menu Data Management URLs
    path('master-data/menu-data/', menus_views.menu_data_list, name='menu_data_list'),
    path('debug/menu-data/', menus_views.menu_data_list_debug, name='menu_data_debug'),
    path('test/menu-data/', menus_views.menu_data_list_test, name='menu_data_test'),
    path('master-data/menu-data/add/', menus_views.menu_data_add, name='menu_data_add'),
    path('master-data/menu-data/<int:menu_id>/edit/', menus_views.menu_data_edit, name='menu_data_edit'),
    path('master-data/menu-data/<int:menu_id>/delete/', menus_views.menu_data_delete, name='menu_data_delete'),
    path('master-data/menu-data/<int:menu_id>/restore/', menus_views.menu_data_restore, name='menu_data_restore'),
    
    # Email Template Management URLs
    path('master-data/email-templates/', email_tpl_views.email_template_list, name='email_template_list'),
    path('master-data/email-templates/add/', email_tpl_views.email_template_add, name='email_template_add'),
    path('master-data/email-templates/<int:template_id>/edit/', email_tpl_views.email_template_edit, name='email_template_edit'),
    path('master-data/email-templates/<int:template_id>/delete/', email_tpl_views.email_template_delete, name='email_template_delete'),
    path('master-data/email-templates/<int:template_id>/restore/', email_tpl_views.email_template_restore, name='email_template_restore'),
    
    # Profile Menu Mapping URLs
    path('master-data/profile-menu-mapping/', menus_views.profile_menu_mapping_list, name='profile_menu_mapping_list'),
    path('master-data/profile-menu-mapping/add/', menus_views.profile_menu_mapping_add, name='profile_menu_mapping_add'),
    path('master-data/profile-menu-mapping/<int:mapping_id>/edit/', menus_views.profile_menu_mapping_edit, name='profile_menu_mapping_edit'),
    path('master-data/profile-menu-mapping/<int:mapping_id>/delete/', menus_views.profile_menu_mapping_delete, name='profile_menu_mapping_delete'),
    path('master-data/profile-menu-mapping/<int:mapping_id>/restore/', menus_views.profile_menu_mapping_restore, name='profile_menu_mapping_restore'),
    path('debug/profile-menu-mapping/', menus_views.profile_menu_mapping_debug, name='profile_menu_mapping_debug'),
    
    # FeeType Master URLs
    path('master-data/fee-type/', fee_views.fee_type_list, name='fee_type_list'),
    path('master-data/fee-type/ajax/', fee_views.fee_type_list_ajax, name='fee_type_list_ajax'),
    path('master-data/fee-type/classes-ajax/', fee_views.fee_type_classes_ajax, name='fee_type_classes_ajax'),
    path('master-data/fee-type/add/', fee_views.fee_type_add, name='fee_type_add'),
    path('master-data/fee-type/<int:fee_type_id>/edit/', fee_views.fee_type_edit, name='fee_type_edit'),
    path('master-data/fee-type/<int:fee_type_id>/delete/', fee_views.fee_type_delete, name='fee_type_delete'),
    path('master-data/fee-type/<int:fee_type_id>/restore/', fee_views.fee_type_restore, name='fee_type_restore'),
    
    # Salary Component Master URLs
    path('master-data/salary-component/', salary_component_views.salary_component_list, name='salary_component_list'),
    path('master-data/salary-component/save/', salary_component_views.salary_component_save, name='salary_component_save'),
    path('master-data/salary-component/delete/', salary_component_views.salary_component_delete_ajax, name='salary_component_delete_ajax'),
    path('master-data/salary-component/restore/', salary_component_views.salary_component_restore_ajax, name='salary_component_restore_ajax'),
    
    # SMTP Configuration URLs
    path('master-data/smtp-configuration/', smtp_config_views.smtp_config_list, name='smtp_config_list'),
    path('master-data/smtp-configuration/save/', smtp_config_views.smtp_config_save, name='smtp_config_save'),
    path('master-data/smtp-configuration/delete/', smtp_config_views.smtp_config_delete_ajax, name='smtp_config_delete_ajax'),
    path('master-data/smtp-configuration/restore/', smtp_config_views.smtp_config_restore_ajax, name='smtp_config_restore_ajax'),
    path('master-data/smtp-configuration/test/', smtp_config_views.smtp_config_test, name='smtp_config_test'),
    
    # Error testing URLs (remove in production)
    path('test/404/', views.test_404, name='test_404'),
    path('test/500/', views.test_500, name='test_500'),
    path('test/403/', views.test_403, name='test_403'),
    path('test/400/', views.test_400, name='test_400'),
    
    # Custom 404 handler for debug mode
    path('custom-404/', views.custom_404_view, name='custom_404'),
    
    # Exam Management URLs
    path('exam/management/', exam_views.exam_management, name='exam_management'),
    path('exam-management/', exam_views.exam_management, name='exam_management_dash'),
    path('exams/manage/', exam_views.exam_management, name='exam_management_alias'),
    path('exam/save/', exam_views.exam_save, name='exam_save'),
    path('exam/delete/', exam_views.exam_delete, name='exam_delete'),
    path('exam/restore/', exam_views.exam_restore, name='exam_restore'),
    path('exam/get/<int:exam_id>/', exam_views.exam_get, name='exam_get'),
    path('exam/list/ajax/', exam_views.exam_list_ajax, name='exam_list_ajax'),
    path('exam/timetable/preview/', template_views.exam_timetable_preview, name='exam_timetable_preview'),
    path('exam/timetable/save/', exam_timetable_views.exam_timetable_save, name='exam_timetable_save'),
    path('exam/timetable/delete/', exam_timetable_views.exam_timetable_delete, name='exam_timetable_delete'),
    path('exam/timetable/get/<str:encrypted_timetable_id>/', exam_timetable_views.exam_timetable_get, name='exam_timetable_get'),
    path('exam/timetable/print/<str:encrypted_exam_id>/<str:encrypted_class_id>/', exam_timetable_views.exam_timetable_print, name='exam_timetable_print'),
    path('exam/timetable/filter/<str:encrypted_exam_id>/<str:encrypted_class_id>/', exam_timetable_views.exam_timetable_filter, name='exam_timetable_filter'),
    path('api/exam/timetable/send-email/', exam_timetable_views.exam_timetable_send_email, name='exam_timetable_send_email'),
    path('exam/timetable/<str:encrypted_exam_id>/', exam_timetable_views.exam_timetable, name='exam_timetable'),

    path('get-subjects-by-class/', views.get_subjects_by_class, name='get_subjects_by_class'),
    
    # Exam Result Entry URLs
    path('exams/results/enter/', exam_result_views.exam_result_entry, name='exam_result_entry'),
    path('exams/results/students/', exam_result_views.exam_result_students, name='exam_result_students'),
    path('exams/results/save/', exam_result_views.exam_result_save, name='exam_result_save'),
    path('exams/results/student-subjects/', exam_result_views.get_student_exam_subjects, name='get_student_exam_subjects'),
    path('api/exams/', exam_result_views.api_exams, name='api_exams'),
    path('api/subjects-by-class/', exam_result_views.api_subjects_by_class, name='api_subjects_by_class'),
    path('api/classes-by-exam/', exam_result_views.api_classes_by_exam, name='api_classes_by_exam'),
    
    # Exam Result View URLs
    path('exams/results/view/', exam_result_views.exam_result_view, name='exam_result_view'),
    path('exams/results/list/', exam_result_views.get_student_result_list, name='get_student_result_list'),
    path('exams/results/detail/', exam_result_views.get_student_result, name='get_student_result'),
    path('exams/results/print/', exam_result_views.exam_result_print, name='exam_result_print'),
    
    # Subscription Management URLs
    path('subscription/my/', subscription_views.my_subscription, name='my_subscription'),
    path('subscription/my/data/', subscription_views.my_subscription_data, name='my_subscription_data'),
    path('subscription/history/', subscription_views.subscription_history, name='subscription_history'),
    path('subscription/plans/', subscription_views.subscription_plans, name='subscription_plans'),
    path('subscription/plans/list/', subscription_views.get_plans, name='get_plans'),
    path('subscription/plans/save/', subscription_views.save_plan, name='save_plan'),
    path('subscription/plans/delete/', subscription_views.delete_plan, name='delete_plan'),
    path('subscription/subscribers/', subscription_views.subscribers, name='subscribers'),
    path('subscription/subscribers/list/', subscription_views.get_subscribers, name='get_subscribers'),
    path('subscription/subscribers/save/', subscription_views.save_subscriber, name='save_subscriber'),
    path('subscription/subscribers/delete/', subscription_views.delete_subscriber, name='delete_subscriber'),
    path('subscription/schools-list/', subscription_views.get_schools_list, name='get_schools_list'),
    path('subscription/add-school/', subscription_views.add_school, name='add_school'),
    path('api/users-list/', subscription_views.get_users_list, name='get_users_list'),
    path('subscription/report/', subscription_views.subscription_report, name='subscription_report'),
    path('subscription/reports/', subscription_views.subscription_report, name='subscription_reports'),
    path('subscription/report/data/', subscription_views.subscription_report_data, name='subscription_report_data'),
    path('subscription/report/details/', subscription_views.subscription_report_details, name='subscription_report_details'),
    path('subscription/referrals/', subscription_views.referrals, name='referrals'),
    path('subscription/referrals/list/', subscription_views.get_referral_list, name='get_referral_list'),
    path('subscription/referrals/stats/', subscription_views.get_referral_stats, name='get_referral_stats'),
    path('subscription/payment-methods/', subscription_views.get_payment_methods, name='get_subscription_payment_methods'),
    path('subscription/referral-partners/list/', subscription_views.get_referral_partners, name='get_referral_partners'),
    
    # Public Subscription Endpoints (No login required)
    path('public/plans/', subscription_views.get_plans_public, name='get_plans_public'),
    path('public/register/', subscription_views.public_registration, name='public_registration'),
    path('public/save-draft/', subscription_views.save_registration_draft, name='save_registration_draft'),
    
    # Salary Management URLs
    path('salary/', salary_views.salary_management, name='salary_management'),
    path('salary/employees/', salary_views.get_employees, name='get_employees'),
    path('salary/list/', salary_views.get_salary_list, name='get_salary_list'),
    path('salary/pay/', salary_views.pay_salary, name='pay_salary'),
    path('salary/generate/', salary_views.generate_salary_records, name='generate_salary_records'),
    path('salary/slip/<str:encrypted_payment_id>/preview/', salary_views.preview_salary_slip, name='preview_salary_slip'),
    path('salary/slip/<str:encrypted_payment_id>/download/', salary_views.download_salary_slip, name='download_salary_slip'),
    path('salary/slip/<str:encrypted_payment_id>/resend/', salary_views.resend_salary_slip, name='resend_salary_slip'),
    
    # Template Management URLs
    path('template-management/', template_views.template_management, name='template_management'),
    path('template-management/save/', template_views.template_management_save, name='template_management_save'),
    path('payment/receipt/preview/', template_views.payment_receipt_preview, name='payment_receipt_preview'),
    path('fee/receipt/preview/', template_views.fee_receipt_preview, name='fee_receipt_preview'),
    path('student/card/preview/', template_views.student_card_preview, name='student_card_preview'),
    path('exams/results/preview/', template_views.exam_result_preview, name='exam_result_preview'),
    path('salary/slip/preview/', salary_slip_preview.salary_slip_preview, name='salary_slip_preview'),
    path('otp-email/preview/', template_views.otp_email_preview, name='otp_email_preview'),
    path('admission/acknowledgment/preview/', template_views.admission_acknowledgment_preview, name='admission_acknowledgment_preview'),
    path('promotion/email/preview/', template_views.promotion_email_preview, name='promotion_email_preview'),
    path('employee/job-letter/preview/', template_views.job_letter_preview, name='job_letter_preview'),
    path('subscription-invoice/preview/', template_views.subscription_invoice_preview, name='subscription_invoice_preview'),
    path('security-email/preview/', template_views.security_email_preview, name='security_email_preview'),
    path('api/encrypt-id/', encrypt_api.encrypt_id_api, name='encrypt_id_api'),
    
    # Student ID Card URLs
    path('student/idcard/<int:student_id>/', id_card_views.student_id_card_view, name='student_id_card'),
    
    # Admission Instructions URLs
    path('master-data/admission-instructions/', admission_instructions_views.admission_instructions, name='admission_instructions'),
    path('master-data/admission-instructions/save/', admission_instructions_views.admission_instructions_save, name='admission_instructions_save'),
    path('master-data/admission-instructions/delete/', admission_instructions_views.admission_instructions_delete, name='admission_instructions_delete'),
    path('master-data/admission-instructions/load/', admission_instructions_views.admission_instructions_load, name='admission_instructions_load'),
    
    # Terms & Conditions URLs
    path('master-data/terms-conditions/', terms_conditions_views.terms_conditions, name='terms_conditions'),
    path('master-data/terms-conditions/save/', terms_conditions_views.terms_conditions_save, name='terms_conditions_save'),
    path('master-data/terms-conditions/delete/', terms_conditions_views.terms_conditions_delete, name='terms_conditions_delete'),
    path('master-data/terms-conditions/load/', terms_conditions_views.terms_conditions_load, name='terms_conditions_load'),
    
    # Academic Year URLs
    path('master-data/academic-year/', academic_year_views.academic_year, name='academic_year'),
    path('master-data/academic-year/save/', academic_year_views.academic_year_save, name='academic_year_save'),
    path('master-data/academic-year/delete/', academic_year_views.academic_year_delete, name='academic_year_delete'),
    path('master-data/academic-year/load/', academic_year_views.academic_year_load, name='academic_year_load'),
    
    # Subject Master URLs
    path('master-data/subject/', subject_views.subject_master, name='subject_master'),
    path('master-data/subject/save/', subject_views.subject_save, name='subject_save'),
    path('master-data/subject/delete/<str:subject_id>/', subject_views.subject_delete, name='subject_delete'),
    path('master-data/subject/by-class/', subject_views.subject_get_by_class, name='subject_get_by_class'),
    path('master-data/subject/load/', subject_views.subject_load, name='subject_load'),
    
    # Test Email URL
    path('test/send-admission-email/<str:student_code>/', admission_views.test_send_admission_email, name='test_send_admission_email'),
    
    # Test Documents URL
    path('test/documents/', views.test_documents_view, name='test_documents_view'),
    path('debug/documents/', views.test_documents_view, name='debug_documents'),
    
    # Data Import URLs
    path('data-import/', include('core.data_import.urls')),
    
    # Ticket Management URLs
    path('tickets/', include('tickets.urls')),
    
    # Document Management URLs
    path('documents/generate/', document_views.generate_document, name='generate_document'),
    path('documents/view/', document_views.view_documents, name='view_documents'),
    path('documents/download/<int:certificate_id>/', document_views.download_certificate, name='download_certificate'),
    
    # OTP Template Management URLs
    path('otp-template-management/', otp_template_management, name='otp_template_management'),
    path('otp-template/activate/', set_active_otp_template, name='set_active_otp_template'),
    path('otp-template/preview/<str:template_code>/', preview_otp_template, name='preview_otp_template'),
    
    # Timetable Management URLs
    path('timetable/management/', timetable_views.timetable_management, name='timetable_management'),
    path('timetable/view-page/', timetable_views.view_timetable_page, name='view_timetable_page'),
    path('timetable/detail/<str:encrypted_timetable_id>/', timetable_views.view_timetable_detail, name='view_timetable_detail'),
    path('timetable/periods/', timetable_views.get_periods, name='get_periods'),
    path('timetable/period/save/', timetable_views.save_period, name='save_period'),
    path('timetable/period/delete/', timetable_views.delete_period, name='delete_period'),
    path('timetable/list/', timetable_views.get_timetables, name='get_timetables'),
    path('timetable/create/', timetable_views.create_timetable, name='create_timetable'),
    path('timetable/view/<str:encrypted_timetable_id>/', timetable_views.view_timetable, name='view_timetable'),
    path('timetable/slot/save/', timetable_views.save_timetable_slot, name='save_timetable_slot'),
    path('timetable/slot/delete/', timetable_views.delete_timetable_slot, name='delete_timetable_slot'),
    path('timetable/delete/', timetable_views.delete_timetable, name='delete_timetable'),
    path('timetable/teachers/', timetable_views.get_teachers, name='get_teachers'),
    path('timetable/preview/', timetable_views.timetable_preview, name='timetable_preview'),
    path('timetable/print/<str:encrypted_timetable_id>/', timetable_views.print_timetable, name='print_timetable'),
    path('timetable/set-school/', timetable_views.set_school_session, name='set_school_session'),

    # Leave Management URLs
    path('leave/', leave_views.leave_dashboard, name='leave_dashboard'),
    path('leave/types/save/', leave_views.leave_type_save, name='leave_type_save'),
    path('leave/types/delete/', leave_views.leave_type_delete_ajax, name='leave_type_delete_ajax'),
    path('leave/types/restore/', leave_views.leave_type_restore_ajax, name='leave_type_restore_ajax'),
    path('leave/balance/', leave_views.leave_balance_api, name='leave_balance_api'),
    path('leave/balance/init/', leave_views.leave_balance_init, name='leave_balance_init'),
    path('leave/apply/', leave_views.leave_apply, name='leave_apply'),
    path('leave/requests/', leave_views.leave_request_list, name='leave_request_list'),
    path('leave/approve/', leave_views.leave_approve_ajax, name='leave_approve_ajax'),
    path('leave/cancel/', leave_views.leave_cancel_ajax, name='leave_cancel_ajax'),
    path('leave/report/', leave_views.leave_report, name='leave_report'),
    path('leave/report/data/', leave_views.leave_report_data, name='leave_report_data'),
    path('leave/employees/', leave_views.get_school_employees, name='get_school_employees'),
    path('leave/staff-balances/', leave_views.api_staff_leave_balances, name='api_staff_leave_balances'),
    path('subscription/invoice/<int:subscription_id>/', subscription_views.view_subscription_invoice, name='view_subscription_invoice'),
    
    # Holiday Management URLs
    path('calendar/', holiday_views.holiday_calendar, name='holiday_calendar'),
    path('master-data/holidays/', holiday_views.holiday_list, name='holiday_list'),
    path('master-data/holidays/manage/', holiday_views.holiday_manage, name='holiday_manage'),
    path('master-data/holidays/generate-weekly/', holiday_views.generate_weekly_offs, name='generate_weekly_offs'),
]
