import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Survey(models.Model):
    """Survey for gathering feedback and opinions"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    SURVEY_TYPE_CHOICES = [
        ('feedback', 'Feedback'),
        ('evaluation', 'Evaluation'),
        ('opinion', 'Opinion Poll'),
        ('compliance', 'Compliance Check'),
        ('satisfaction', 'Satisfaction Survey'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Survey details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES, default='feedback')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Targeting
    target_audience = models.CharField(max_length=100, blank=True, help_text="Target audience for the survey")
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_surveys')
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Anonymous option
    allow_anonymous = models.BooleanField(default=False, help_text="Allow anonymous responses")
    
    # Limits
    max_responses = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of responses allowed")
    
    # Author
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_surveys')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['survey_type']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Check if survey is currently active"""
        if self.status != 'active':
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class SurveyQuestion(models.Model):
    """Questions within a survey"""

    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('rating', 'Rating Scale'),
        ('yes_no', 'Yes/No'),
        ('date', 'Date'),
        ('number', 'Number'),
        ('comment', 'Comment/Feedback'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    
    # Question details
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='text')
    help_text = models.TextField(blank=True, help_text="Additional context for the question")
    
    # Options for choice questions
    choices = models.JSONField(null=True, blank=True, help_text="Options for choice questions (array)")
    
    # Validation
    required = models.BooleanField(default=True)
    
    # Rating scale configuration
    min_rating = models.PositiveIntegerField(null=True, blank=True, default=1)
    max_rating = models.PositiveIntegerField(null=True, blank=True, default=5)
    
    # Order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Survey Question'
        verbose_name_plural = 'Survey Questions'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.survey.title} - Question {self.order}"


class SurveyResponse(models.Model):
    """Response to a survey"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    
    # Respondent
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    is_anonymous = models.BooleanField(default=False)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # IP address for anonymous responses
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Survey Response'
        verbose_name_plural = 'Survey Responses'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['survey', '-submitted_at']),
            models.Index(fields=['user', '-submitted_at']),
        ]
    
    def __str__(self):
        respondent = "Anonymous" if self.is_anonymous else (self.user.get_full_name() if self.user else "Unknown")
        return f"{self.survey.title} - {respondent}"


class SurveyAnswer(models.Model):
    """Individual answer to a survey question"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='answers')
    
    # Answer value (stored as text for flexibility)
    answer_text = models.TextField(blank=True)
    answer_number = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    answer_date = models.DateField(null=True, blank=True)
    
    # For choice questions, store selected options as JSON array
    selected_choices = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Survey Answer'
        verbose_name_plural = 'Survey Answers'
        unique_together = [['response', 'question']]
    
    def __str__(self):
        return f"{self.response} - {self.question.question_text[:50]}"


class Poll(models.Model):
    """Quick polls for board decisions or opinions"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Poll details
    question = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Related content
    related_meeting = models.ForeignKey('meetings.Meeting', on_delete=models.SET_NULL, null=True, blank=True, related_name='polls')
    related_motion = models.ForeignKey('voting.Motion', on_delete=models.SET_NULL, null=True, blank=True, related_name='polls')
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Options
    allow_multiple_choices = models.BooleanField(default=False)
    
    # Author
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_polls')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Poll'
        verbose_name_plural = 'Polls'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['related_meeting']),
            models.Index(fields=['related_motion']),
        ]
    
    def __str__(self):
        return self.question


class PollOption(models.Model):
    """Options for a poll"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Poll Option'
        verbose_name_plural = 'Poll Options'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.poll.question} - {self.option_text}"
    
    @property
    def vote_count(self):
        """Get the number of votes for this option"""
        return self.votes.count()


class PollVote(models.Model):
    """Vote on a poll option"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    
    # Timestamp
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Poll Vote'
        verbose_name_plural = 'Poll Votes'
        ordering = ['-voted_at']
        unique_together = [['poll', 'user']]
        indexes = [
            models.Index(fields=['poll', '-voted_at']),
            models.Index(fields=['user', '-voted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.option.option_text}"
