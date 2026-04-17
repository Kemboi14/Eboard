import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class APIKey(models.Model):
    """API keys for third-party integrations"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    SCOPE_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Key details
    name = models.CharField(max_length=200, help_text="Friendly name for the API key")
    key = models.CharField(max_length=255, unique=True, help_text="API key value")
    prefix = models.CharField(max_length=10, default="eboard_", help_text="Key prefix for identification")
    
    # Owner
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    organization = models.ForeignKey('agencies.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='api_keys')
    
    # Permissions
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='read')
    allowed_endpoints = models.JSONField(null=True, blank=True, help_text="List of allowed endpoint patterns")
    denied_endpoints = models.JSONField(null=True, blank=True, help_text="List of denied endpoint patterns")
    
    # Rate limiting
    rate_limit_per_minute = models.PositiveIntegerField(default=60, help_text="Requests per minute")
    rate_limit_per_hour = models.PositiveIntegerField(default=1000, help_text="Requests per hour")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.PositiveIntegerField(default=0)
    
    # Security
    ip_whitelist = models.JSONField(null=True, blank=True, help_text="List of allowed IP addresses")
    require_https = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.prefix}***{self.key[-4:]})"
    
    @property
    def is_valid(self):
        """Check if API key is valid and not expired"""
        if self.status != 'active':
            return False
        if self.expires_at and timezone.now() >= self.expires_at:
            return False
        return True


class APIRequestLog(models.Model):
    """Log of API requests for monitoring and analytics"""

    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('unauthorized', 'Unauthorized'),
        ('forbidden', 'Forbidden'),
        ('not_found', 'Not Found'),
        ('rate_limited', 'Rate Limited'),
        ('server_error', 'Server Error'),
        ('validation_error', 'Validation Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Request details
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, related_name='request_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_requests')
    
    # HTTP details
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    endpoint = models.CharField(max_length=500)
    query_params = models.JSONField(null=True, blank=True)
    
    # Response
    status_code = models.PositiveIntegerField()
    response_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time_ms = models.PositiveIntegerField(help_text="Response time in milliseconds")
    
    # Client info
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Request size
    request_size = models.PositiveIntegerField(null=True, blank=True, help_text="Request body size in bytes")
    response_size = models.PositiveIntegerField(null=True, blank=True, help_text="Response body size in bytes")
    
    # Timestamp
    requested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['api_key', '-requested_at']),
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
            models.Index(fields=['-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"


class Webhook(models.Model):
    """Webhook configurations for external integrations"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('disabled', 'Disabled'),
    ]

    EVENT_CHOICES = [
        ('meeting.created', 'Meeting Created'),
        ('meeting.updated', 'Meeting Updated'),
        ('meeting.started', 'Meeting Started'),
        ('meeting.ended', 'Meeting Ended'),
        ('motion.created', 'Motion Created'),
        ('motion.voted', 'Motion Voted'),
        ('motion.passed', 'Motion Passed'),
        ('document.created', 'Document Created'),
        ('document.approved', 'Document Approved'),
        ('user.created', 'User Created'),
        ('user.updated', 'User Updated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Webhook details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(help_text="Webhook URL to send events to")
    
    # Events
    events = models.JSONField(help_text="List of events to subscribe to")
    
    # Owner
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')
    organization = models.ForeignKey('agencies.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='webhooks')
    
    # Security
    secret = models.CharField(max_length=255, blank=True, help_text="HMAC secret for signature verification")
    require_https = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Retry configuration
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.PositiveIntegerField(default=3)
    retry_delay_seconds = models.PositiveIntegerField(default=60)
    
    # Headers
    custom_headers = models.JSONField(null=True, blank=True, help_text="Custom headers to send with webhook")
    
    # Usage tracking
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    failed_deliveries = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['events']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookDelivery(models.Model):
    """Log of webhook delivery attempts"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    
    # Event details
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField(help_text="Event payload")
    
    # Delivery details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    
    # Retry tracking
    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    delivered_at = models.DateTimeField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Webhook Delivery'
        verbose_name_plural = 'Webhook Deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} ({self.get_status_display()})"


class Integration(models.Model):
    """Third-party integrations (e.g., Slack, Salesforce, etc.)"""

    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('configuring', 'Configuring'),
    ]

    INTEGRATION_TYPE_CHOICES = [
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('salesforce', 'Salesforce'),
        ('hubspot', 'HubSpot'),
        ('zapier', 'Zapier'),
        ('custom', 'Custom Integration'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Integration details
    name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='configuring')
    
    # Owner
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integrations')
    organization = models.ForeignKey('agencies.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='integrations')
    
    # Configuration
    configuration = models.JSONField(help_text="Integration-specific configuration")
    credentials_encrypted = models.TextField(blank=True, help_text="Encrypted credentials")
    
    # Webhook URL for callbacks
    callback_url = models.URLField(blank=True)
    
    # Sync settings
    auto_sync = models.BooleanField(default=False)
    sync_interval_minutes = models.PositiveIntegerField(default=60)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=50, blank=True)
    
    # Error handling
    last_error = models.TextField(blank=True)
    error_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Integration'
        verbose_name_plural = 'Integrations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['integration_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
    
    @property
    def is_connected(self):
        """Check if integration is connected"""
        return self.status == 'connected'
