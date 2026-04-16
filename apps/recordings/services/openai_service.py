"""
OpenAI integration for transcription (Whisper) and summarization (GPT-4).
Handles speech-to-text, meeting summaries, action item extraction, and sentiment analysis.
"""
import requests
import json
from typing import List, Dict, Optional
from .base_service import BaseRecordingService


class OpenAIService:
    """
    OpenAI service for AI-powered meeting analysis.
    """
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, api_key=None, organization=None):
        self.api_key = api_key
        self.organization = organization
        self.session = requests.Session()
    
    def get_headers(self):
        """
        Get headers for OpenAI API requests.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        return headers
    
    def transcribe_audio(self, audio_file, language="en", model="whisper-1"):
        """
        Transcribe audio file using OpenAI Whisper.
        
        Args:
            audio_file: Audio file path or file object
            language: Language code (e.g., 'en', 'es')
            model: Whisper model to use (whisper-1, whisper-large-v3, etc.)
            
        Returns:
            Transcription result with text and metadata
        """
        url = f"{self.BASE_URL}/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        data = {
            "model": model,
            "language": language,
            "response_format": "verbose_json",  # Get timestamps and segments
            "timestamp_granularities": ["segment"],
        }
        
        try:
            with open(audio_file, "rb") as f:
                files = {"file": f}
                response = self.session.post(url, headers=headers, data=data, files=files)
                response.raise_for_status()
                result = response.json()
            
            return {
                "text": result.get("text"),
                "language": result.get("language"),
                "duration": result.get("duration"),
                "segments": result.get("segments", []),
                "words": result.get("words", []),
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_audio_from_url(self, audio_url, language="en", model="whisper-1"):
        """
        Transcribe audio from URL using OpenAI Whisper.
        
        Args:
            audio_url: URL to audio file
            language: Language code
            model: Whisper model to use
            
        Returns:
            Transcription result
        """
        # Download audio first, then transcribe
        try:
            response = self.session.get(audio_url, stream=True)
            response.raise_for_status()
            
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                temp_path = f.name
            
            # Transcribe
            result = self.transcribe_audio(temp_path, language, model)
            
            # Clean up
            import os
            os.unlink(temp_path)
            
            return result
        except Exception as e:
            raise Exception(f"Failed to transcribe audio from URL: {str(e)}")
    
    def generate_meeting_summary(self, transcription_text, summary_type="detailed", model="gpt-4"):
        """
        Generate meeting summary using GPT-4.
        
        Args:
            transcription_text: Transcribed meeting text
            summary_type: Type of summary (executive, detailed, action_items)
            model: GPT model to use (gpt-4, gpt-3.5-turbo)
            
        Returns:
            Generated summary
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self.get_headers()
        
        if summary_type == "executive":
            system_prompt = """You are an executive assistant. Create a concise executive summary of the meeting.
            Include:
            - Main topics discussed
            - Key decisions made
            - Important outcomes
            Keep it under 300 words."""
        elif summary_type == "action_items":
            system_prompt = """You are a project manager. Extract all action items from the meeting.
            For each action item, include:
            - Description
            - Assigned person (if mentioned)
            - Due date (if mentioned)
            - Priority level (if mentioned)
            Format as a bulleted list."""
        else:  # detailed
            system_prompt = """You are a meeting secretary. Create a detailed summary of the meeting.
            Include:
            - Overview of the meeting
            - Main topics discussed
            - Key decisions made
            - Action items and next steps
            - Any concerns or issues raised"""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text},
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "tokens_used": result["usage"]["total_tokens"],
                "model_used": model,
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    def extract_action_items(self, transcription_text, model="gpt-4"):
        """
        Extract action items from meeting transcription.
        
        Args:
            transcription_text: Transcribed meeting text
            model: GPT model to use
            
        Returns:
            List of action items
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self.get_headers()
        
        system_prompt = """Extract all action items from the meeting transcript.
        For each action item, provide:
        - description: What needs to be done
        - assigned_to: Who is responsible (if mentioned)
        - due_date: When it's due (if mentioned)
        - priority: High, Medium, or Low (based on context)
        - context: Relevant discussion context
        
        Return as JSON array with these fields."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text},
            ],
            "max_tokens": 1500,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            action_items = json.loads(content)
            
            return {
                "action_items": action_items,
                "tokens_used": result["usage"]["total_tokens"],
                "model_used": model,
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to extract action items: {str(e)}")
    
    def analyze_sentiment(self, transcription_text, model="gpt-4"):
        """
        Analyze sentiment of meeting transcription.
        
        Args:
            transcription_text: Transcribed meeting text
            model: GPT model to use
            
        Returns:
            Sentiment analysis result
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self.get_headers()
        
        system_prompt = """Analyze the sentiment of this meeting.
        Provide:
        - overall_sentiment: positive, negative, or neutral
        - sentiment_score: -1.0 (very negative) to 1.0 (very positive)
        - emotions: JSON object with emotion scores (joy, anger, sadness, fear, surprise, disgust)
        - engagement_score: 0.0 to 1.0 (how engaged participants were)
        
        Return as JSON."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text},
            ],
            "max_tokens": 500,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            sentiment_data = json.loads(content)
            
            return {
                "sentiment_data": sentiment_data,
                "tokens_used": result["usage"]["total_tokens"],
                "model_used": model,
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to analyze sentiment: {str(e)}")
    
    def detect_topics(self, transcription_text, model="gpt-4"):
        """
        Detect main topics discussed in the meeting.
        
        Args:
            transcription_text: Transcribed meeting text
            model: GPT model to use
            
        Returns:
            List of detected topics with confidence scores
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self.get_headers()
        
        system_prompt = """Identify the main topics discussed in this meeting.
        For each topic, provide:
        - topic: Name of the topic
        - confidence: 0.0 to 1.0 (how confident you are this is a main topic)
        - keywords: List of relevant keywords
        
        Return as JSON array of topics."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text},
            ],
            "max_tokens": 800,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            topics_data = json.loads(content)
            
            return {
                "topics": topics_data.get("topics", []),
                "tokens_used": result["usage"]["total_tokens"],
                "model_used": model,
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to detect topics: {str(e)}")
