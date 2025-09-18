from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),  # Duplicate to '' but may be intentional
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),

    path('request-access/', views.request_access_view, name='request_access'),  # Confirm view name

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-email/<uidb64>/<token>/', views.email_verification_success, name='email_verification_success'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset-password/done/', views.password_reset_done, name='password_reset_done'),

    path('process-request/<int:request_id>/', views.process_access_request, name='process_access_request'),

    # Informational pages
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('feedback/', views.feedback_page, name='feedback'),
    path('settings/', views.settings_page, name='settings'),
]
