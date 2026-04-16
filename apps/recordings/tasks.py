"""
Celery tasks for async processing of meeting recordings.
Handles transcription, summarization, and AI analysis.
"""
import time
from celery import shared_task
from django.utils import timezone
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
from .services.zoom_service import ZoomService
from .services.teams_service import TeamsService
from .services.openai_service import OpenAIService


@shared_task
def process_zoom_webhook(webhook_data):
    """
    Process Zoom webhook event for recording completion.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.zoom_api_key or not settings.zoom_api_secret:
            raise Exception("Zoom API credentials not configured")
        
        zoom_service = ZoomService(
            api_key=settings.zoom_api_key,
            api_secret=settings.zoom_api_secret
        )
        
        processed_data = zoom_service.process_webhook(webhook_data)
        
        # Create recording entry
        recording = MeetingRecording.objects.create(
            platform="zoom",
            platform_meeting_id=processed_data.get("meeting_id"),
            title=processed_data.get("meeting_title", "Zoom Meeting"),
            status="processing",
            started_at=processed_data.get("started_at"),
            ended_at=processed_data.get("ended_at"),
            auto_transcribe=settings.auto_transcribe_enabled,
            auto_summarize=settings.auto_summarize_enabled,
        )
        
        # Download recordings
        recordings = processed_data.get("recordings", [])
        for rec in recordings:
            download_url = rec.get("download_url")
            if download_url:
                content = zoom_service.download_recording(download_url)
                # Save file and process
                # TODO: Implement file saving and trigger transcription
        
        return f"Processed Zoom webhook for meeting {processed_data.get('meeting_id')}"
    
    except Exception as e:
        raise Exception(f"Failed to process Zoom webhook: {str(e)}")


@shared_task
def process_teams_webhook(webhook_data):
    """
    Process Teams webhook event for recording completion.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.teams_tenant_id or not settings.teams_client_id:
            raise Exception("Teams API credentials not configured")
        
        teams_service = TeamsService(
            tenant_id=settings.teams_tenant_id,
            client_id=settings.teams_client_id,
            client_secret=settings.teams_client_secret
        )
        
        processed_data = teams_service.process_webhook(webhook_data)
        
        # Create recording entry
        recording = MeetingRecording.objects.create(
            platform="teams",
            platform_meeting_id=processed_data.get("meeting_id"),
            title="Teams Meeting",
            status="processing",
            auto_transcribe=settings.auto_transcribe_enabled,
            auto_summarize=settings.auto_summarize_enabled,
        )
        
        # Download and process recordings
        # TODO: Implement file saving and trigger transcription
        
        return f"Processed Teams webhook for meeting {processed_data.get('meeting_id')}"
    
    except Exception as e:
        raise Exception(f"Failed to process Teams webhook: {str(e)}")


@shared_task
def transcribe_recording(recording_id):
    """
    Transcribe meeting recording using OpenAI Whisper.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.openai_api_key:
            raise Exception("OpenAI API credentials not configured")
        
        recording = MeetingRecording.objects.get(id=recording_id)
        recording.status = "processing"
        recording.save()
        
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        
        # Get audio file
        audio_file = recording.audio_file
        if not audio_file:
            audio_file = recording.video_file
        
        if not audio_file:
            raise Exception("No audio or video file found for transcription")
        
        # Transcribe
        start_time = time.time()
        result = openai_service.transcribe_audio(
            audio_file.path,
            language=settings.transcription_language,
            model=settings.transcription_model
        )
        processing_time = time.time() - start_time
        
        # Create transcription
        transcription = Transcription.objects.create(
            recording=recording,
            full_text=result.get("text"),
            language=result.get("language"),
            confidence_score=1.0,  # Whisper doesn't provide confidence by default
            transcription_engine=settings.transcription_model,
            processing_time_seconds=processing_time,
        )
        
        # Create transcription segments
        for segment in result.get("segments", []):
            TranscriptionSegment.objects.create(
                transcription=transcription,
                text=segment.get("text"),
                speaker=segment.get("speaker"),
                speaker_confidence=segment.get("speaker_confidence"),
                start_time=segment.get("start"),
                end_time=segment.get("end"),
            )
        
        # Update recording status
        recording.status = "completed"
        recording.save()
        
        # Trigger summarization if enabled
        if settings.auto_summarize_enabled:
            generate_meeting_summary.delay(transcription.id)
        
        return f"Transcribed recording {recording_id}"
    
    except Exception as e:
        recording = MeetingRecording.objects.get(id=recording_id)
        recording.status = "failed"
        recording.save()
        raise Exception(f"Failed to transcribe recording: {str(e)}")


@shared_task
def generate_meeting_summary(transcription_id):
    """
    Generate meeting summary using GPT-4.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.openai_api_key:
            raise Exception("OpenAI API credentials not configured")
        
        transcription = Transcription.objects.get(id=transcription_id)
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        
        # Generate executive summary
        if settings.summary_type in ["executive", "both"]:
            start_time = time.time()
            result = openai_service.generate_meeting_summary(
                transcription.full_text,
                summary_type="executive",
                model=settings.summary_model
            )
            processing_time = time.time() - start_time
            
            MeetingSummary.objects.create(
                recording=transcription.recording,
                summary_type="executive",
                content=result.get("content"),
                model_used=settings.summary_model,
                tokens_used=result.get("tokens_used"),
                processing_time_seconds=processing_time,
            )
        
        # Generate detailed summary
        if settings.summary_type in ["detailed", "both"]:
            start_time = time.time()
            result = openai_service.generate_meeting_summary(
                transcription.full_text,
                summary_type="detailed",
                model=settings.summary_model
            )
            processing_time = time.time() - start_time
            
            MeetingSummary.objects.create(
                recording=transcription.recording,
                summary_type="detailed",
                content=result.get("content"),
                model_used=settings.summary_model,
                tokens_used=result.get("tokens_used"),
                processing_time_seconds=processing_time,
            )
        
        # Extract action items
        start_time = time.time()
        result = openai_service.extract_action_items(
            transcription.full_text,
            model=settings.summary_model
        )
        processing_time = time.time() - start_time
        
        for item_data in result.get("action_items", []):
            ActionItem.objects.create(
                recording=transcription.recording,
                description=item_data.get("description"),
                priority=item_data.get("priority", "medium").lower(),
                context=item_data.get("context"),
            )
        
        # Analyze sentiment if enabled
        if settings.auto_analyze_sentiment:
            analyze_sentiment.delay(transcription.id)
        
        # Detect topics if enabled
        if settings.auto_detect_topics:
            detect_topics.delay(transcription.id)
        
        return f"Generated summary for transcription {transcription_id}"
    
    except Exception as e:
        raise Exception(f"Failed to generate summary: {str(e)}")


@shared_task
def analyze_sentiment(transcription_id):
    """
    Analyze sentiment of meeting transcription.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.openai_api_key:
            raise Exception("OpenAI API credentials not configured")
        
        transcription = Transcription.objects.get(id=transcription_id)
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        
        start_time = time.time()
        result = openai_service.analyze_sentiment(
            transcription.full_text,
            model=settings.summary_model
        )
        processing_time = time.time() - start_time
        
        sentiment_data = result.get("sentiment_data")
        
        SentimentAnalysis.objects.create(
            recording=transcription.recording,
            overall_sentiment=sentiment_data.get("overall_sentiment"),
            sentiment_score=sentiment_data.get("sentiment_score"),
            emotions=sentiment_data.get("emotions"),
            engagement_score=sentiment_data.get("engagement_score"),
            model_used=settings.summary_model,
        )
        
        return f"Analyzed sentiment for transcription {transcription_id}"
    
    except Exception as e:
        raise Exception(f"Failed to analyze sentiment: {str(e)}")


@shared_task
def detect_topics(transcription_id):
    """
    Detect topics in meeting transcription.
    """
    try:
        settings = RecordingSettings.objects.first()
        if not settings or not settings.openai_api_key:
            raise Exception("OpenAI API credentials not configured")
        
        transcription = Transcription.objects.get(id=transcription_id)
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        
        start_time = time.time()
        result = openai_service.detect_topics(
            transcription.full_text,
            model=settings.summary_model
        )
        processing_time = time.time() - start_time
        
        for topic_data in result.get("topics", []):
            TopicDetection.objects.create(
                recording=transcription.recording,
                topic=topic_data.get("topic"),
                confidence=topic_data.get("confidence"),
                keywords=topic_data.get("keywords"),
            )
        
        return f"Detected topics for transcription {transcription_id}"
    
    except Exception as e:
        raise Exception(f"Failed to detect topics: {str(e)}")
