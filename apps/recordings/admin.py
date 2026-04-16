from django.contrib import admin
from .models import (
    MeetingRecording,
    Transcription,
    TranscriptionSegment,
    MeetingSummary,
    ActionItem,
    SentimentAnalysis,
    TopicDetection,
    RecordingSettings,
)


@admin.register(RecordingSettings)
class RecordingSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for managing AI recording settings and API credentials.
    """
    fieldsets = (
        ("Zoom API Settings", {
            "fields": ("zoom_api_key", "zoom_api_secret", "zoom_webhook_secret"),
            "classes": ("collapse",),
        }),
        ("Microsoft Teams API Settings", {
            "fields": ("teams_tenant_id", "teams_client_id", "teams_client_secret"),
            "classes": ("collapse",),
        }),
        ("OpenAI API Settings", {
            "fields": ("openai_api_key", "openai_organization"),
            "classes": ("collapse",),
        }),
        ("Cloud Storage Settings", {
            "fields": ("storage_type", "aws_access_key_id", "aws_secret_access_key", 
                      "aws_bucket_name", "aws_region", "gcs_project_id", 
                      "gcs_bucket_name", "gcs_credentials"),
            "classes": ("collapse",),
        }),
        ("Recording Defaults", {
            "fields": ("auto_transcribe_enabled", "auto_summarize_enabled", 
                      "auto_detect_topics", "auto_analyze_sentiment"),
        }),
        ("Transcription Settings", {
            "fields": ("transcription_language", "transcription_model"),
            "classes": ("collapse",),
        }),
        ("Summary Settings", {
            "fields": ("summary_model", "summary_type"),
            "classes": ("collapse",),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not RecordingSettings.objects.exists()


class TranscriptionSegmentInline(admin.TabularInline):
    """
    Inline admin for transcription segments.
    """
    model = TranscriptionSegment
    extra = 0
    readonly_fields = ("start_time", "end_time", "speaker")
    fields = ("text", "speaker", "start_time", "end_time")


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing transcriptions.
    """
    list_display = ("id", "recording", "language", "confidence_score", "created_at")
    list_filter = ("language", "transcription_engine", "created_at")
    search_fields = ("full_text", "recording__title")
    readonly_fields = ("created_at", "updated_at", "processing_time_seconds")
    inlines = [TranscriptionSegmentInline]


@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    """
    Admin interface for managing meeting summaries.
    """
    list_display = ("id", "recording", "summary_type", "model_used", "created_at")
    list_filter = ("summary_type", "model_used", "created_at")
    search_fields = ("content", "recording__title")
    readonly_fields = ("created_at", "updated_at", "tokens_used", "processing_time_seconds")


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    """
    Admin interface for managing action items.
    """
    list_display = ("id", "description", "priority", "status", "assigned_to", "due_date")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("description", "context")
    readonly_fields = ("created_at", "updated_at", "timestamp_in_recording", "completed_at")


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    """
    Admin interface for managing sentiment analysis.
    """
    list_display = ("id", "recording", "overall_sentiment", "sentiment_score", "created_at")
    list_filter = ("overall_sentiment", "created_at")
    readonly_fields = ("created_at", "updated_at", "model_used")


@admin.register(TopicDetection)
class TopicDetectionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing topic detection.
    """
    list_display = ("id", "recording", "topic", "confidence")
    list_filter = ("confidence",)
    search_fields = ("topic", "keywords")
    readonly_fields = ("start_time", "end_time")


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    """
    Admin interface for managing meeting recordings.
    """
    list_display = ("id", "title", "platform", "status", "started_at", "created_by")
    list_filter = ("platform", "status", "started_at", "created_at")
    search_fields = ("title", "platform_meeting_id")
    readonly_fields = ("created_at", "updated_at", "duration_seconds")
    
    fieldsets = (
        ("Meeting Details", {
            "fields": ("meeting", "title", "platform", "platform_meeting_id"),
        }),
        ("Recording Status", {
            "fields": ("status", "started_at", "ended_at", "duration_seconds"),
        }),
        ("Files", {
            "fields": ("audio_file", "video_file", "file_url"),
        }),
        ("Settings", {
            "fields": ("auto_transcribe", "auto_summarize"),
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
