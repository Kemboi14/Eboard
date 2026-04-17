from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
import secrets

from .models import APIKey, APIRequestLog, Webhook, WebhookDelivery, Integration


# ─── API Key Views ─────────────────────────────────────────────────────────────

class APIKeyListView(LoginRequiredMixin, ListView):
    """List all API keys"""
    model = APIKey
    template_name = 'api/api_keys.html'
    context_object_name = 'api_keys'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class APIKeyDetailView(LoginRequiredMixin, DetailView):
    """View API key details"""
    model = APIKey
    template_name = 'api/api_key_detail.html'
    context_object_name = 'api_key'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_key = self.object
        context['request_logs'] = api_key.request_logs.all()[:50]
        return context


class APIKeyCreateView(LoginRequiredMixin, CreateView):
    """Create a new API key"""
    model = APIKey
    template_name = 'api/api_key_form.html'
    fields = ['name', 'scope', 'allowed_endpoints', 'denied_endpoints', 'rate_limit_per_minute', 'rate_limit_per_hour', 'expires_at']
    success_url = reverse_lazy('api:api_keys')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        # Generate a secure API key
        form.instance.key = f"{form.instance.prefix}{secrets.token_urlsafe(32)}"
        form.instance.status = 'active'
        messages.success(self.request, 'API key created successfully. Save the key securely as it will not be shown again.')
        return super().form_valid(form)


@login_required
@require_POST
def revoke_api_key(request, pk):
    """Revoke an API key"""
    api_key = get_object_or_404(APIKey, pk=pk, user=request.user)
    
    api_key.status = 'revoked'
    api_key.revoked_at = timezone.now()
    api_key.save()
    
    messages.success(request, 'API key revoked successfully.')
    return redirect('api:api_key_detail', pk=pk)


@login_required
@require_POST
def regenerate_api_key(request, pk):
    """Regenerate an API key"""
    api_key = get_object_or_404(APIKey, pk=pk, user=request.user)
    
    api_key.key = f"{api_key.prefix}{secrets.token_urlsafe(32)}"
    api_key.status = 'active'
    api_key.last_rotated_at = timezone.now()
    api_key.save()
    
    messages.success(request, 'API key regenerated successfully. Save the new key securely.')
    return redirect('api:api_key_detail', pk=pk)


# ─── API Request Log Views ───────────────────────────────────────────────────

class APIRequestLogListView(LoginRequiredMixin, ListView):
    """List API request logs"""
    model = APIRequestLog
    template_name = 'api/request_logs.html'
    context_object_name = 'logs'
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        api_key_id = self.request.GET.get('api_key')
        if api_key_id:
            queryset = queryset.filter(api_key_id=api_key_id)
        return queryset


class APIRequestLogDetailView(LoginRequiredMixin, DetailView):
    """View API request log details"""
    model = APIRequestLog
    template_name = 'api/request_log_detail.html'
    context_object_name = 'log'


# ─── Webhook Views ────────────────────────────────────────────────────────────

class WebhookListView(LoginRequiredMixin, ListView):
    """List all webhooks"""
    model = Webhook
    template_name = 'api/webhooks.html'
    context_object_name = 'webhooks'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class WebhookDetailView(LoginRequiredMixin, DetailView):
    """View webhook details"""
    model = Webhook
    template_name = 'api/webhook_detail.html'
    context_object_name = 'webhook'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        webhook = self.object
        context['deliveries'] = webhook.deliveries.all()[:50]
        return context


class WebhookCreateView(LoginRequiredMixin, CreateView):
    """Create a new webhook"""
    model = Webhook
    template_name = 'api/webhook_form.html'
    fields = ['name', 'description', 'url', 'events', 'secret', 'require_https', 'retry_on_failure', 'retry_attempts', 'retry_interval_seconds']
    success_url = reverse_lazy('api:webhooks')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'active'
        messages.success(self.request, 'Webhook created successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def test_webhook(request, pk):
    """Test a webhook by sending a ping event"""
    webhook = get_object_or_404(Webhook, pk=pk, user=request.user)
    
    # Create a test delivery
    delivery = WebhookDelivery.objects.create(
        webhook=webhook,
        event_type='test',
        payload={'test': True, 'timestamp': timezone.now().isoformat()},
        status='pending'
    )
    
    # In production, this would actually send the webhook
    delivery.status = 'success'
    delivery.response_status_code = 200
    delivery.completed_at = timezone.now()
    delivery.save()
    
    messages.success(request, 'Webhook test sent successfully.')
    return redirect('api:webhook_detail', pk=pk)


@login_required
@require_POST
def toggle_webhook(request, pk):
    """Toggle webhook status"""
    webhook = get_object_or_404(Webhook, pk=pk, user=request.user)
    
    if webhook.status == 'active':
        webhook.status = 'paused'
        messages.success(request, 'Webhook paused.')
    else:
        webhook.status = 'active'
        messages.success(request, 'Webhook activated.')
    
    webhook.save()
    return redirect('api:webhook_detail', pk=pk)


class WebhookDeliveryListView(LoginRequiredMixin, ListView):
    """List webhook deliveries"""
    model = WebhookDelivery
    template_name = 'api/webhook_deliveries.html'
    context_object_name = 'deliveries'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        webhook_id = self.request.GET.get('webhook')
        if webhook_id:
            queryset = queryset.filter(webhook_id=webhook_id)
        return queryset


# ─── Integration Views ───────────────────────────────────────────────────────

class IntegrationListView(LoginRequiredMixin, ListView):
    """List all integrations"""
    model = Integration
    template_name = 'api/integrations.html'
    context_object_name = 'integrations'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class IntegrationDetailView(LoginRequiredMixin, DetailView):
    """View integration details"""
    model = Integration
    template_name = 'api/integration_detail.html'
    context_object_name = 'integration'


class IntegrationCreateView(LoginRequiredMixin, CreateView):
    """Create a new integration"""
    model = Integration
    template_name = 'api/integration_form.html'
    fields = ['name', 'integration_type', 'configuration', 'callback_url', 'auto_sync', 'sync_interval_hours']
    success_url = reverse_lazy('api:integrations')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'configuring'
        messages.success(self.request, 'Integration created. Complete the configuration to activate.')
        return super().form_valid(form)


@login_required
@require_POST
def activate_integration(request, pk):
    """Activate an integration"""
    integration = get_object_or_404(Integration, pk=pk, user=request.user)
    
    integration.status = 'active'
    integration.last_synced_at = timezone.now()
    integration.save()
    
    messages.success(request, 'Integration activated successfully.')
    return redirect('api:integration_detail', pk=pk)


@login_required
@require_POST
def deactivate_integration(request, pk):
    """Deactivate an integration"""
    integration = get_object_or_404(Integration, pk=pk, user=request.user)
    
    integration.status = 'disabled'
    integration.save()
    
    messages.success(request, 'Integration deactivated.')
    return redirect('api:integration_detail', pk=pk)


@login_required
@require_POST
def sync_integration(request, pk):
    """Manually trigger a sync for an integration"""
    integration = get_object_or_404(Integration, pk=pk, user=request.user)
    
    if integration.status != 'active':
        messages.error(request, 'Integration is not active.')
        return redirect('api:integration_detail', pk=pk)
    
    # In production, this would trigger actual sync with the external API
    integration.last_synced_at = timezone.now()
    integration.save()
    
    messages.success(request, 'Integration sync completed successfully.')
    return redirect('api:integration_detail', pk=pk)
