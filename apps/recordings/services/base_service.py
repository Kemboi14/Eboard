"""
Base service class for recording platform integrations.
Provides common functionality for all recording services.
"""
from abc import ABC, abstractmethod
import requests


class BaseRecordingService(ABC):
    """
    Abstract base class for recording platform services.
    """
    
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    @abstractmethod
    def get_meeting_recordings(self, meeting_id):
        """
        Get recordings for a specific meeting.
        
        Args:
            meeting_id: Platform-specific meeting ID
            
        Returns:
            List of recording objects
        """
        pass
    
    @abstractmethod
    def download_recording(self, download_url):
        """
        Download a recording file.
        
        Args:
            download_url: URL to download the recording from
            
        Returns:
            File content
        """
        pass
    
    @abstractmethod
    def get_meeting_details(self, meeting_id):
        """
        Get details for a specific meeting.
        
        Args:
            meeting_id: Platform-specific meeting ID
            
        Returns:
            Meeting details
        """
        pass
    
    @abstractmethod
    def process_webhook(self, webhook_data):
        """
        Process webhook event from the platform.
        
        Args:
            webhook_data: Webhook event data
            
        Returns:
            Processed recording information
        """
        pass
