from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # API Keys
    path('api-keys/', views.APIKeyListView.as_view(), name='api_keys'),
    path('api-keys/<uuid:pk>/', views.APIKeyDetailView.as_view(), name='api_key_detail'),
    path('api-keys/create/', views.APIKeyCreateView.as_view(), name='api_key_create'),
    path('api-keys/<uuid:pk>/revoke/', views.revoke_api_key, name='revoke_api_key'),
    path('api-keys/<uuid:pk>/regenerate/', views.regenerate_api_key, name='regenerate_api_key'),
    
    # API Request Logs
    path('request-logs/', views.APIRequestLogListView.as_view(), name='request_logs'),
    path('request-logs/<uuid:pk>/', views.APIRequestLogDetailView.as_view(), name='request_log_detail'),
    
    # Webhooks
    path('webhooks/', views.WebhookListView.as_view(), name='webhooks'),
    path('webhooks/<uuid:pk>/', views.WebhookDetailView.as_view(), name='webhook_detail'),
    path('webhooks/create/', views.WebhookCreateView.as_view(), name='webhook_create'),
    path('webhooks/<uuid:pk>/test/', views.test_webhook, name='test_webhook'),
    path('webhooks/<uuid:pk>/toggle/', views.toggle_webhook, name='toggle_webhook'),
    path('webhook-deliveries/', views.WebhookDeliveryListView.as_view(), name='webhook_deliveries'),
    
    # Integrations
    path('integrations/', views.IntegrationListView.as_view(), name='integrations'),
    path('integrations/<uuid:pk>/', views.IntegrationDetailView.as_view(), name='integration_detail'),
    path('integrations/create/', views.IntegrationCreateView.as_view(), name='integration_create'),
    path('integrations/<uuid:pk>/activate/', views.activate_integration, name='activate_integration'),
    path('integrations/<uuid:pk>/deactivate/', views.deactivate_integration, name='deactivate_integration'),
    path('integrations/<uuid:pk>/sync/', views.sync_integration, name='sync_integration'),
]
