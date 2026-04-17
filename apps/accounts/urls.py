from django.urls import path
from . import views
from .custom_logout import logout_view

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', views.ProfileView, name='profile'),
    path('change-password/', views.ChangePasswordView, name='change_password'),
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('login-2fa/', views.login_2fa, name='login_2fa'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # SSO Providers
    path('sso-providers/', views.SSOProviderListView.as_view(), name='sso_providers'),
    path('sso-providers/<uuid:pk>/', views.SSOProviderDetailView.as_view(), name='sso_provider_detail'),
    path('sso-providers/create/', views.SSOProviderCreateView.as_view(), name='sso_provider_create'),
    
    # Session Management
    path('sessions/', views.UserSessionListView.as_view(), name='user_sessions'),
    path('sessions/<uuid:pk>/revoke/', views.revoke_session, name='revoke_session'),
    path('sessions/revoke-all/', views.revoke_all_other_sessions, name='revoke_all_sessions'),
    
    # Encryption Keys
    path('encryption-keys/', views.EncryptionKeyListView.as_view(), name='encryption_keys'),
    path('encryption-keys/create/', views.EncryptionKeyCreateView.as_view(), name='encryption_key_create'),
    path('encryption-keys/<uuid:pk>/rotate/', views.rotate_encryption_key, name='rotate_encryption_key'),
    
    # Multi-Language Support
    path('languages/', views.LanguageListView.as_view(), name='languages'),
    path('translations/', views.TranslationListView.as_view(), name='translations'),
    path('translations/create/', views.TranslationCreateView.as_view(), name='translation_create'),
    path('translations/<uuid:pk>/update/', views.TranslationUpdateView.as_view(), name='translation_update'),
]
