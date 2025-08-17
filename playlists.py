"""
Playlist management routes for YouTube API
"""

from flask import Blueprint, request, jsonify
from googleapiclient.errors import HttpError
import logging
from services.youtube_service import get_youtube_service

logger = logging.getLogger(__name__)

playlists_bp = Blueprint('playlists', __name__)

@playlists_bp.route('/', methods=['GET'])
def list_playlists():
    """List user's YouTube playlists"""
    try:
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        playlists = []
        next_page_token = None
        
        while True:
            request_params = {
                'part': 'snippet,status',
                'mine': True,
                'maxResults': 50
            }
            
            if next_page_token:
                request_params['pageToken'] = next_page_token
            
            response = youtube.playlists().list(**request_params).execute()
            
            for item in response.get('items', []):
                playlist_info = {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'thumbnail': item['snippet'].get('thumbnails', {}).get('default', {}).get('url'),
                    'privacy_status': item['status']['privacyStatus'],
                    'video_count': item.get('contentDetails', {}).get('itemCount', 0),
                    'created_at': item['snippet']['publishedAt']
                }
                playlists.append(playlist_info)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return jsonify({
            'playlists': playlists,
            'total_count': len(playlists),
            'status': 'success'
        })
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return jsonify({
            'error': f'YouTube API error: {e}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Error listing playlists: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@playlists_bp.route('/', methods=['POST'])
def create_playlist():
    """Create a new YouTube playlist"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title')
        description = data.get('description', '')
        privacy_status = data.get('privacy_status', 'private')
        
        if not title:
            return jsonify({'error': 'Playlist title is required'}), 400
        
        # Validate privacy status
        valid_privacy = ['private', 'public', 'unlisted']
        if privacy_status not in valid_privacy:
            privacy_status = 'private'
        
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        playlist_body = {
            'snippet': {
                'title': title,
                'description': description
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }
        
        response = youtube.playlists().insert(
            part='snippet,status',
            body=playlist_body
        ).execute()
        
        playlist_info = {
            'id': response['id'],
            'title': response['snippet']['title'],
            'description': response['snippet']['description'],
            'privacy_status': response['status']['privacyStatus'],
            'created_at': response['snippet']['publishedAt']
        }
        
        return jsonify({
            'playlist': playlist_info,
            'status': 'success',
            'message': 'Playlist created successfully'
        })
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return jsonify({
            'error': f'YouTube API error: {e}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Error creating playlist: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@playlists_bp.route('/<playlist_id>/videos', methods=['GET'])
def list_playlist_videos(playlist_id):
    """List videos in a specific playlist"""
    try:
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        videos = []
        next_page_token = None
        
        while True:
            request_params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': 50
            }
            
            if next_page_token:
                request_params['pageToken'] = next_page_token
            
            response = youtube.playlistItems().list(**request_params).execute()
            
            for item in response.get('items', []):
                video_info = {
                    'id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet'].get('thumbnails', {}).get('default', {}).get('url'),
                    'position': item['snippet']['position'],
                    'added_at': item['snippet']['publishedAt']
                }
                videos.append(video_info)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return jsonify({
            'videos': videos,
            'playlist_id': playlist_id,
            'total_count': len(videos),
            'status': 'success'
        })
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return jsonify({
            'error': f'YouTube API error: {e}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Error listing playlist videos: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@playlists_bp.route('/<playlist_id>/videos', methods=['POST'])
def add_video_to_playlist(playlist_id):
    """Add a video to a playlist"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({'error': 'Video ID is required'}), 400
        
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        playlist_item_body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        
        response = youtube.playlistItems().insert(
            part='snippet',
            body=playlist_item_body
        ).execute()
        
        return jsonify({
            'playlist_item_id': response['id'],
            'video_id': video_id,
            'playlist_id': playlist_id,
            'status': 'success',
            'message': 'Video added to playlist successfully'
        })
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return jsonify({
            'error': f'YouTube API error: {e}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Error adding video to playlist: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@playlists_bp.route('/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a YouTube playlist"""
    try:
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        youtube.playlists().delete(id=playlist_id).execute()
        
        return jsonify({
            'playlist_id': playlist_id,
            'status': 'success',
            'message': 'Playlist deleted successfully'
        })
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return jsonify({
            'error': f'YouTube API error: {e}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Error deleting playlist: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

