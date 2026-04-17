import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AccessibilityAudit(models.Model):
    """Accessibility compliance audits for WCAG 2.1"""

    WCAG_LEVEL_CHOICES = [
        ('a', 'Level A'),
        ('aa', 'Level AA'),
        ('aaa', 'Level AAA'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    COMPLIANCE_STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('partially_compliant', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('not_tested', 'Not Tested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Audit details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    wcag_level = models.CharField(max_length=5, choices=WCAG_LEVEL_CHOICES, default='aa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Target
    target_url = models.URLField(help_text="URL or section being audited")
    target_page = models.CharField(max_length=200, blank=True, help_text="Specific page or component name")
    
    # Compliance status
    overall_compliance = models.CharField(max_length=30, choices=COMPLIANCE_STATUS_CHOICES, default='not_tested')
    compliance_score = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Audit details
    audit_method = models.CharField(max_length=100, blank=True, help_text="e.g., Automated scan, Manual review, User testing")
    tools_used = models.JSONField(null=True, blank=True, help_text="List of accessibility testing tools used")
    
    # Auditor
    audited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='accessibility_audits')
    
    # Schedule
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Findings summary
    total_issues = models.PositiveIntegerField(default=0)
    critical_issues = models.PositiveIntegerField(default=0)
    serious_issues = models.PositiveIntegerField(default=0)
    moderate_issues = models.PositiveIntegerField(default=0)
    minor_issues = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Accessibility Audit'
        verbose_name_plural = 'Accessibility Audits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['wcag_level']),
            models.Index(fields=['overall_compliance']),
            models.Index(fields=['target_url']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_wcag_level_display()}"


class AccessibilityIssue(models.Model):
    """Individual accessibility issues found during audits"""

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('serious', 'Serious'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('verified', 'Verified'),
        ('deferred', 'Deferred'),
        ('wont_fix', 'Won\'t Fix'),
    ]

    WCAG_CRITERIA_CHOICES = [
        ('1.1.1', 'Non-text Content'),
        ('1.2.1', 'Audio-only and Video-only (Prerecorded)'),
        ('1.2.2', 'Captions (Prerecorded)'),
        ('1.2.3', 'Audio Description or Media Alternative (Prerecorded)'),
        ('1.2.4', 'Captions (Live)'),
        ('1.2.5', 'Audio Description (Prerecorded)'),
        ('1.3.1', 'Info and Relationships'),
        ('1.3.2', 'Meaningful Sequence'),
        ('1.3.3', 'Sensory Characteristics'),
        ('1.3.4', 'Orientation'),
        ('1.3.5', 'Identify Input Purpose'),
        ('1.4.1', 'Use of Color'),
        ('1.4.2', 'Audio Control'),
        ('1.4.3', 'Contrast (Minimum)'),
        ('1.4.4', 'Resize text'),
        ('1.4.5', 'Images of Text'),
        ('1.4.10', 'Reflow'),
        ('1.4.11', 'Non-text Contrast'),
        ('1.4.12', 'Text Spacing'),
        ('1.4.13', 'Content on Hover or Focus'),
        ('2.1.1', 'Keyboard'),
        ('2.1.2', 'No Keyboard Trap'),
        ('2.1.4', 'Character Key Shortcuts'),
        ('2.2.1', 'Timing Adjustable'),
        ('2.2.2', 'Pause, Stop, Hide'),
        ('2.3.1', 'Three Flashes or Below'),
        ('2.3.2', 'Three Flashes'),
        ('2.4.1', 'Bypass Blocks'),
        ('2.4.2', 'Page Titled'),
        ('2.4.3', 'Focus Order'),
        ('2.4.4', 'Link Purpose (In Context)'),
        ('2.4.5', 'Multiple Ways'),
        ('2.4.6', 'Headings and Labels'),
        ('2.4.7', 'Focus Visible'),
        ('2.5.1', 'Pointer Gestures'),
        ('2.5.2', 'Pointer Cancellation'),
        ('2.5.3', 'Label in Name'),
        ('2.5.4', 'Motion Actuation'),
        ('3.1.1', 'Language of Page'),
        ('3.1.2', 'Language of Parts'),
        ('3.2.1', 'On Focus'),
        ('3.2.2', 'On Input'),
        ('3.2.3', 'Consistent Navigation'),
        ('3.2.4', 'Consistent Identification'),
        ('3.2.5', 'Change on Request'),
        ('3.3.1', 'Error Identification'),
        ('3.3.2', 'Labels or Instructions'),
        ('3.3.3', 'Error Suggestion'),
        ('3.3.4', 'Error Prevention (Legal, Financial, Data)'),
        ('3.3.5', 'Help'),
        ('4.1.1', 'Parsing'),
        ('4.1.2', 'Name, Role, Value'),
        ('4.1.3', 'Status Messages'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(AccessibilityAudit, on_delete=models.CASCADE, related_name='issues')
    
    # Issue details
    title = models.CharField(max_length=300)
    description = models.TextField()
    wcag_criteria = models.CharField(max_length=20, choices=WCAG_CRITERIA_CHOICES, blank=True)
    
    # Severity and status
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='moderate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Location
    element_type = models.CharField(max_length=100, blank=True, help_text="e.g., Button, Form, Image, Link")
    element_selector = models.CharField(max_length=500, blank=True, help_text="CSS selector for the element")
    
    # Reproduction steps
    reproduction_steps = models.TextField(blank=True)
    
    # Expected behavior
    expected_behavior = models.TextField(blank=True)
    actual_behavior = models.TextField(blank=True)
    
    # Suggested fix
    suggested_fix = models.TextField(blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_accessibility_issues')
    
    # Resolution
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_accessibility_issues')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Accessibility Issue'
        verbose_name_plural = 'Accessibility Issues'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['audit', '-created_at']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['wcag_criteria']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"


class AccessibilityRemediation(models.Model):
    """Track remediation efforts for accessibility issues"""

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.OneToOneField(AccessibilityIssue, on_delete=models.CASCADE, related_name='remediation')
    
    # Remediation plan
    approach = models.TextField(help_text="Description of the remediation approach")
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)
    actual_hours = models.PositiveIntegerField(null=True, blank=True)
    
    # Schedule
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Implementation notes
    implementation_notes = models.TextField(blank=True)
    
    # Verification
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_remediations')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Accessibility Remediation'
        verbose_name_plural = 'Accessibility Remediations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['issue']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_end_date']),
        ]
    
    def __str__(self):
        return f"Remediation for {self.issue.title}"
