from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class MeetingRecording(models.Model):
    """
    Stores meeting recording metadata and file information.
    Supports recordings from Zoom, Teams, and in-app recordings.
    """
    PLATFORM_CHOICES = [
        ("zoom", "Zoom"),
        ("teams", "Microsoft Teams"),
        ("in_app", "In-App Recording"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("recording", "Recording"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to meeting
    meeting = models.ForeignKey(
        "meetings.Meeting",
        on_delete=models.CASCADE,
        related_name="ai_recordings",
        null=True,
        blank=True,
    )
    
    # Recording details
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    platform_meeting_id = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    
    # File information
    audio_file = models.FileField(upload_to="recordings/audio/%Y/%m/%d/", blank=True, null=True)
    video_file = models.FileField(upload_to="recordings/video/%Y/%m/%d/", blank=True, null=True)
    file_url = models.URLField(blank=True, null=True)  # For cloud storage
    
    # Duration and timing
    duration_seconds = models.IntegerField(blank=True, null=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
    
    # Recording settings
    auto_transcribe = models.BooleanField(default=True)
    auto_summarize = models.BooleanField(default=True)
    
    # Creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_recordings",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meeting_recordings"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["meeting"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.platform})"


class Transcription(models.Model):
    """
    Stores transcribed text from meeting recordings.
    Includes speaker identification and timestamps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recording = models.ForeignKey(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name="transcriptions",
    )
    
    # Transcription content
    full_text = models.TextField()
    language = models.CharField(max_length=10, default="en")
    confidence_score = models.FloatField(blank=True, null=True)
    
    # Processing metadata
    transcription_engine = models.CharField(max_length=50, default="whisper")
    processing_time_seconds = models.FloatField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transcriptions"

    def __str__(self):
        return f"Transcription for {self.recording.title}"


class TranscriptionSegment(models.Model):
    """
    Individual segments of transcribed text with timestamps and speaker info.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    transcription = models.ForeignKey(
        Transcription,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    
    # Segment content
    text = models.TextField()
    speaker = models.CharField(max_length=255, blank=True, null=True)
    speaker_confidence = models.FloatField(blank=True, null=True)
    
    # Timing
    start_time = models.FloatField()  # Seconds from start
    end_time = models.FloatField()  # Seconds from start
    
    class Meta:
        db_table = "transcription_segments"
        ordering = ["start_time"]

    def __str__(self):
        return f"Segment at {self.start_time}s: {self.text[:50]}..."


class MeetingSummary(models.Model):
    """
    AI-generated meeting summary using GPT-4.
    """
    SUMMARY_TYPE_CHOICES = [
        ("executive", "Executive Summary"),
        ("detailed", "Detailed Summary"),
        ("action_items", "Action Items Only"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recording = models.ForeignKey(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name="summaries",
    )
    
    # Summary content
    summary_type = models.CharField(max_length=50, choices=SUMMARY_TYPE_CHOICES)
    content = models.TextField()
    
    # AI metadata
    model_used = models.CharField(max_length=50, default="gpt-4")
    tokens_used = models.IntegerField(blank=True, null=True)
    processing_time_seconds = models.FloatField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meeting_summaries"

    def __str__(self):
        return f"{self.get_summary_type_display()} for {self.recording.title}"


class ActionItem(models.Model):
    """
    Action items extracted from meeting recordings using AI.
    """
    PRIORITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recording = models.ForeignKey(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name="action_items",
    )
    
    # Action item details
    description = models.TextField()
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_action_items",
        null=True,
        blank=True,
    )
    due_date = models.DateTimeField(blank=True, null=True)
    
    # Context
    context = models.TextField(blank=True, null=True)  # Relevant discussion context
    timestamp_in_recording = models.FloatField(blank=True, null=True)  # Where in the recording this was mentioned
    
    # Completion
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "action_items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["assigned_to"]),
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.description[:50]}... ({self.priority})"


class SentimentAnalysis(models.Model):
    """
    Sentiment analysis of meeting recordings.
    Tracks overall sentiment, emotion distribution, and engagement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recording = models.OneToOneField(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name="sentiment_analysis",
    )
    
    # Overall sentiment
    overall_sentiment = models.CharField(max_length=50)  # positive, negative, neutral
    sentiment_score = models.FloatField()  # -1.0 to 1.0
    
    # Emotion breakdown (JSON field)
    emotions = models.JSONField(blank=True, null=True)  # {"joy": 0.3, "anger": 0.1, ...}
    
    # Engagement metrics
    engagement_score = models.FloatField(blank=True, null=True)
    participation_rate = models.FloatField(blank=True, null=True)
    
    # Processing metadata
    model_used = models.CharField(max_length=50, default="gpt-4")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sentiment_analysis"

    def __str__(self):
        return f"Sentiment for {self.recording.title}: {self.overall_sentiment}"


class TopicDetection(models.Model):
    """
    Topics detected in meeting recordings using AI.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recording = models.ForeignKey(
        MeetingRecording,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    
    # Topic details
    topic = models.CharField(max_length=255)
    confidence = models.FloatField()  # 0.0 to 1.0
    relevance_score = models.FloatField(blank=True, null=True)
    
    # Timing
    start_time = models.FloatField(blank=True, null=True)
    end_time = models.FloatField(blank=True, null=True)
    
    # Keywords
    keywords = models.JSONField(blank=True, null=True)  # List of relevant keywords
    
    class Meta:
        db_table = "topic_detection"
        ordering = ["-confidence"]

    def __str__(self):
        return f"{self.topic} ({self.confidence:.2f})"


class RecordingSettings(models.Model):
    """
    Configuration settings for AI meeting recording integrations.
    Stores API credentials for Zoom, Teams, OpenAI, and cloud storage.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Zoom API settings
    zoom_api_key = models.CharField(max_length=255, blank=True, null=True)
    zoom_api_secret = models.CharField(max_length=255, blank=True, null=True)
    zoom_webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    
    # Microsoft Teams API settings
    teams_tenant_id = models.CharField(max_length=255, blank=True, null=True)
    teams_client_id = models.CharField(max_length=255, blank=True, null=True)
    teams_client_secret = models.CharField(max_length=255, blank=True, null=True)
    
    # OpenAI API settings
    openai_api_key = models.CharField(max_length=255, blank=True, null=True)
    openai_organization = models.CharField(max_length=255, blank=True, null=True)
    
    # Cloud storage settings
    storage_type = models.CharField(max_length=50, choices=[
        ("local", "Local Storage"),
        ("s3", "AWS S3"),
        ("gcs", "Google Cloud Storage"),
    ], default="local")
    
    # AWS S3 settings
    aws_access_key_id = models.CharField(max_length=255, blank=True, null=True)
    aws_secret_access_key = models.CharField(max_length=255, blank=True, null=True)
    aws_bucket_name = models.CharField(max_length=255, blank=True, null=True)
    aws_region = models.CharField(max_length=50, default="us-east-1")
    
    # Google Cloud Storage settings
    gcs_project_id = models.CharField(max_length=255, blank=True, null=True)
    gcs_bucket_name = models.CharField(max_length=255, blank=True, null=True)
    gcs_credentials = models.TextField(blank=True, null=True)  # JSON credentials
    
    # Recording defaults
    auto_transcribe_enabled = models.BooleanField(default=True)
    auto_summarize_enabled = models.BooleanField(default=True)
    auto_detect_topics = models.BooleanField(default=True)
    auto_analyze_sentiment = models.BooleanField(default=True)
    
    # Transcription settings
    transcription_language = models.CharField(max_length=10, default="en")
    transcription_model = models.CharField(max_length=50, default="whisper-1")
    
    # Summary settings
    summary_model = models.CharField(max_length=50, default="gpt-4")
    summary_type = models.CharField(max_length=50, choices=[
        ("executive", "Executive Summary"),
        ("detailed", "Detailed Summary"),
        ("both", "Both"),
    ], default="both")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recording_settings"
        verbose_name = "Recording Settings"
        verbose_name_plural = "Recording Settings"

    def __str__(self):
        return "Recording Settings"
