"""
YouTube API service utilities
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from flask import current_app
import os
import logging

logger = logging.getLogger(__name__)

def get_youtube_service():
    """Get authenticated YouTube service instance"""
    try:
        creds = None
        token_path = current_app.config['TOKEN_FILE']
        
        # Load existing credentials
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    token_path, 
                    [
                        "https://www.googleapis.com/auth/youtube.upload",
                        "https://www.googleapis.com/auth/youtube.readonly",
                        "https://www.googleapis.com/auth/youtube.force-ssl",
                        "https://www.googleapis.com/auth/youtube"
                    ]
                )
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                return None
        
        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(token_path, 'w') as token_file:
                        token_file.write(creds.to_json())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    return None
            else:
                logger.warning("No valid credentials available")
                return None
        
        # Build and return YouTube service
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
        
    except Exception as e:
        logger.error(f"Error building YouTube service: {e}")
        return None

def get_channel_info(youtube_service):
    """Get authenticated user's channel information"""
    try:
        response = youtube_service.channels().list(
            part='id,snippet,statistics',
            mine=True
        ).execute()
        
        if response['items']:
            channel = response['items'][0]
            return {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                'video_count': channel['statistics'].get('videoCount', 0),
                'view_count': channel['statistics'].get('viewCount', 0)
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        return None

def validate_video_id(youtube_service, video_id):
    """Validate if a video ID exists and is accessible"""
    try:
        response = youtube_service.videos().list(
            part='id',
            id=video_id
        ).execute()
        
        return len(response['items']) > 0
        
    except Exception as e:
        logger.error(f"Error validating video ID: {e}")
        return False

def get_video_categories(youtube_service, region_code='US'):
    """Get available video categories for a region"""
    try:
        response = youtube_service.videoCategories().list(
            part='snippet',
            regionCode=region_code
        ).execute()
        
        categories = []
        for item in response['items']:
            if item['snippet']['assignable']:
                categories.append({
                    'id': item['id'],
                    'title': item['snippet']['title']
                })
        
        return categories
        
    except Exception as e:
        logger.error(f"Error getting video categories: {e}")
        return []

