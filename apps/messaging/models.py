import uuid
from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Message(models.Model):
    """Secure messages between board members"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Sender and recipients
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    recipients = models.ManyToManyField(User, through='MessageRecipient', related_name='received_messages')
    
    # Message content
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    # Priority and status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Attachments
    attachments = models.ManyToManyField('documents.Document', blank=True, related_name='messages')
    
    # Context
    related_meeting = models.ForeignKey('meetings.Meeting', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    related_motion = models.ForeignKey('voting.Motion', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    
    # Metadata
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} - From {self.sender.get_full_name() if self.sender else 'Unknown'}"
    
    def send(self):
        """Send the message to all recipients"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
        
        # Mark recipients as having received the message
        for recipient in self.recipients.all():
            MessageRecipient.objects.filter(message=self, recipient=recipient).update(
                received_at=timezone.now()
            )


class MessageRecipient(models.Model):
    """Through model for message recipients with read status"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Read status
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Message Recipient'
        verbose_name_plural = 'Message Recipients'
        unique_together = ['message', 'recipient']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.message.subject}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])


class MessageThread(models.Model):
    """Threaded conversations for message replies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200)
    participants = models.ManyToManyField(User, related_name='message_threads')
    
    # Original message
    original_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    
    # Status
    active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Message Thread'
        verbose_name_plural = 'Message Threads'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['active', '-last_message_at']),
            models.Index(fields=['-last_message_at']),
        ]
    
    def __str__(self):
        return self.subject
    
    def add_participant(self, user):
        """Add a participant to the thread"""
        self.participants.add(user)
        self.save(update_fields=['updated_at'])
    
    def remove_participant(self, user):
        """Remove a participant from the thread"""
        self.participants.remove(user)
        self.save(update_fields=['updated_at'])


class Announcement(models.Model):
    """System announcements with targeting capabilities"""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('board_members', 'Board Members'),
        ('company_secretary', 'Company Secretary'),
        ('executive_management', 'Executive Management'),
        ('compliance_officer', 'Compliance Officer'),
        ('it_administrator', 'IT Administrator'),
        ('internal_audit', 'Internal Audit'),
        ('custom', 'Custom Selection'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Announcement details
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.CharField(max_length=300, blank=True, help_text="Brief summary for notifications")
    
    # Targeting
    target_audience = models.CharField(max_length=30, choices=TARGET_CHOICES, default='all')
    custom_targets = models.ManyToManyField(User, blank=True, related_name='targeted_announcements', help_text="Custom user selection when target_audience is 'custom'")
    
    # Priority and status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Scheduling
    publish_at = models.DateTimeField(null=True, blank=True, help_text="Schedule publication for future date")
    expire_at = models.DateTimeField(null=True, blank=True, help_text="When to expire/unpublish the announcement")
    
    # Attachments
    attachments = models.ManyToManyField('documents.Document', blank=True, related_name='announcements')
    
    # Context
    related_meeting = models.ForeignKey('meetings.Meeting', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    related_motion = models.ForeignKey('voting.Motion', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0)
    viewed_by = models.ManyToManyField(User, blank=True, related_name='viewed_announcements')
    
    # Author
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['publish_at']),
            models.Index(fields=['expire_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Check if announcement is currently active"""
        if self.status != 'published':
            return False
        now = timezone.now()
        if self.publish_at and now < self.publish_at:
            return False
        if self.expire_at and now > self.expire_at:
            return False
        return True
    
    @property
    def is_expired(self):
        """Check if announcement has expired"""
        if self.expire_at:
            return timezone.now() > self.expire_at
        return False
    
    def publish(self):
        """Publish the announcement"""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])
    
    def archive(self):
        """Archive the announcement"""
        self.status = 'archived'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_viewed(self, user):
        """Mark announcement as viewed by user"""
        if user not in self.viewed_by.all():
            self.viewed_by.add(user)
            self.view_count += 1
            self.save(update_fields=['view_count', 'updated_at'])
