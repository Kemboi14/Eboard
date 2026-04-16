"""
URL configuration for AI-powered meeting recording system.
"""
from django.urls import path
from . import views

app_name = "recordings"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Recordings
    path("recordings/", views.recording_list, name="recording_list"),
    path("recordings/<uuid:recording_id>/", views.recording_detail, name="recording_detail"),
    
    # Transcription
    path("transcriptions/<uuid:transcription_id>/", views.transcription_view, name="transcription_view"),
    
    # Action Items
    path("action-items/", views.action_items_list, name="action_items_list"),
    path("action-items/<uuid:action_item_id>/", views.action_item_detail, name="action_item_detail"),
    path("action-items/<uuid:action_item_id>/update-status/", views.update_action_item_status, name="update_action_item_status"),
    
    # Summaries
    path("summaries/", views.meeting_summaries_list, name="summaries_list"),
]
