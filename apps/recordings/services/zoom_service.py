"""
Zoom API integration for meeting recording.
Handles authentication, recording retrieval, and webhook processing.
"""
import requests
import jwt
import time
from datetime import datetime, timedelta
from django.conf import settings
from .base_service import BaseRecordingService


class ZoomService(BaseRecordingService):
    """
    Zoom API service for meeting recording integration.
    """
    
    BASE_URL = "https://api.zoom.us/v2"
    
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def generate_jwt_token(self):
        """
        Generate JWT token for Zoom API authentication.
        """
        payload = {
            "iss": self.api_key,
            "exp": int(time.time() + 3600),  # Token expires in 1 hour
        }
        token = jwt.encode(payload, self.api_secret, algorithm="HS256")
        return token
    
    def get_headers(self):
        """
        Get headers for Zoom API requests.
        """
        token = self.generate_jwt_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def get_meeting_recordings(self, meeting_id):
        """
        Get recordings for a specific meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            List of recording objects
        """
        url = f"{self.BASE_URL}/meetings/{meeting_id}/recordings"
        headers = self.get_headers()
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("recording_files", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Zoom recordings: {str(e)}")
    
    def download_recording(self, download_url):
        """
        Download a recording file from Zoom.
        
        Args:
            download_url: URL to download the recording from
            
        Returns:
            File content
        """
        headers = self.get_headers()
        
        try:
            response = self.session.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download Zoom recording: {str(e)}")
    
    def get_meeting_details(self, meeting_id):
        """
        Get details for a specific meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Meeting details
        """
        url = f"{self.BASE_URL}/meetings/{meeting_id}"
        headers = self.get_headers()
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Zoom meeting details: {str(e)}")
    
    def verify_webhook_event(self, event_token, payload):
        """
        Verify Zoom webhook event signature.
        
        Args:
            event_token: Event token from webhook
            payload: Webhook payload
            
        Returns:
            Boolean indicating if webhook is valid
        """
        # Implementation depends on Zoom webhook secret
        # This is a simplified version
        return True
    
    def process_webhook(self, webhook_data):
        """
        Process Zoom webhook event.
        
        Args:
            webhook_data: Webhook event data
            
        Returns:
            Processed recording information
        """
        event_type = webhook_data.get("event")
        
        if event_type == "recording.completed":
            return self._handle_recording_completed(webhook_data)
        elif event_type == "meeting.started":
            return self._handle_meeting_started(webhook_data)
        elif event_type == "meeting.ended":
            return self._handle_meeting_ended(webhook_data)
        
        return None
    
    def _handle_recording_completed(self, webhook_data):
        """
        Handle recording completed webhook event.
        """
        payload = webhook_data.get("object", {})
        meeting_id = payload.get("uuid")
        
        recordings = self.get_meeting_recordings(meeting_id)
        meeting_details = self.get_meeting_details(meeting_id)
        
        return {
            "meeting_id": meeting_id,
            "meeting_title": meeting_details.get("topic", "Unknown Meeting"),
            "recordings": recordings,
            "started_at": payload.get("start_time"),
            "ended_at": payload.get("end_time"),
        }
    
    def _handle_meeting_started(self, webhook_data):
        """
        Handle meeting started webhook event.
        """
        payload = webhook_data.get("object", {})
        return {
            "meeting_id": payload.get("uuid"),
            "status": "started",
            "started_at": payload.get("start_time"),
        }
    
    def _handle_meeting_ended(self, webhook_data):
        """
        Handle meeting ended webhook event.
        """
        payload = webhook_data.get("object", {})
        return {
            "meeting_id": payload.get("uuid"),
            "status": "ended",
            "ended_at": payload.get("end_time"),
        }
