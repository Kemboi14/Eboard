"""
Microsoft Teams API integration for meeting recording.
Handles authentication, recording retrieval, and webhook processing.
"""
import requests
from datetime import datetime, timedelta
from .base_service import BaseRecordingService


class TeamsService(BaseRecordingService):
    """
    Microsoft Teams API service for meeting recording integration.
    """
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, tenant_id=None, client_id=None, client_secret=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.session = requests.Session()
    
    def get_access_token(self):
        """
        Get OAuth access token for Microsoft Graph API.
        """
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }
        
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            return self.access_token
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Teams access token: {str(e)}")
    
    def get_headers(self):
        """
        Get headers for Teams API requests.
        """
        if not self.access_token:
            self.get_access_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    def get_meeting_recordings(self, meeting_id):
        """
        Get recordings for a specific Teams meeting.
        
        Args:
            meeting_id: Teams meeting ID
            
        Returns:
            List of recording objects
        """
        url = f"{self.BASE_URL}/communications/onlineMeetings/{meeting_id}/recordings"
        headers = self.get_headers()
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Teams recordings: {str(e)}")
    
    def download_recording(self, download_url):
        """
        Download a recording file from Teams.
        
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
            raise Exception(f"Failed to download Teams recording: {str(e)}")
    
    def get_meeting_details(self, meeting_id):
        """
        Get details for a specific Teams meeting.
        
        Args:
            meeting_id: Teams meeting ID
            
        Returns:
            Meeting details
        """
        url = f"{self.BASE_URL}/communications/onlineMeetings/{meeting_id}"
        headers = self.get_headers()
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Teams meeting details: {str(e)}")
    
    def process_webhook(self, webhook_data):
        """
        Process Teams webhook event.
        
        Args:
            webhook_data: Webhook event data
            
        Returns:
            Processed recording information
        """
        # Teams webhooks use Microsoft Graph API notifications
        resource = webhook_data.get("resource", {})
        change_type = webhook_data.get("changeType")
        
        if change_type == "created":
            return self._handle_recording_created(resource)
        elif change_type == "updated":
            return self._handle_recording_updated(resource)
        elif change_type == "deleted":
            return self._handle_recording_deleted(resource)
        
        return None
    
    def _handle_recording_created(self, resource):
        """
        Handle recording created webhook event.
        """
        meeting_id = resource.get("onlineMeetingId")
        recording_id = resource.get("id")
        
        return {
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "status": "created",
            "created_at": resource.get("createdDateTime"),
        }
    
    def _handle_recording_updated(self, resource):
        """
        Handle recording updated webhook event.
        """
        meeting_id = resource.get("onlineMeetingId")
        recording_id = resource.get("id")
        
        return {
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "status": "updated",
            "updated_at": resource.get("lastModifiedDateTime"),
        }
    
    def _handle_recording_deleted(self, resource):
        """
        Handle recording deleted webhook event.
        """
        meeting_id = resource.get("onlineMeetingId")
        recording_id = resource.get("id")
        
        return {
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "status": "deleted",
            "deleted_at": resource.get("deletedDateTime"),
        }
