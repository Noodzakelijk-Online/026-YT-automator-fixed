"""
Video upload routes for YouTube API
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import tempfile
import logging
from services.youtube_service import get_youtube_service

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/video', methods=['POST'])
def upload_video():
    """Upload video to YouTube"""
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get metadata from form data
        title = request.form.get('title', 'Untitled Video')
        description = request.form.get('description', '')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        category_id = request.form.get('category_id', '22')  # Default to People & Blogs
        privacy_status = request.form.get('privacy_status', 'private')
        playlist_id = request.form.get('playlist_id')
        
        # Clean tags
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Get YouTube service
        youtube = get_youtube_service()
        if not youtube:
            return jsonify({'error': 'YouTube authentication required'}), 401
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'embeddable': True,
                    'license': 'youtube',
                    'publicStatsViewable': True
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                temp_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            # Upload video
            logger.info(f"Starting upload for video: {title}")
            insert_request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute upload with progress tracking
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            logger.info(f"Video uploaded successfully: {video_id}")
            
            # Add to playlist if specified
            if playlist_id:
                try:
                    playlist_item_body = {
                        'snippet': {
                            'playlistId': playlist_id,
                            'resourceId': {
                                'kind': 'youtube#video',
                                'videoId': video_id
                            }
                        }
                    }
                    
                    youtube.playlistItems().insert(
                        part='snippet',
                        body=playlist_item_body
                    ).execute()
                    
                    logger.info(f"Video added to playlist: {playlist_id}")
                except HttpError as e:
                    logger.warning(f"Failed to add video to playlist: {e}")
            
            return jsonify({
                'video_id': video_id,
                'video_url': f'https://www.youtube.com/watch?v={video_id}',
                'title': title,
                'status': 'success',
                'message': 'Video uploaded successfully'
            })
            
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_path)
                os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
    
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_content = e.content.decode('utf-8') if e.content else str(e)
        return jsonify({
            'error': f'YouTube API error: {error_content}',
            'status': 'error'
        }), 400
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@upload_bp.route('/progress/<video_id>')
def upload_progress(video_id):
    """Get upload progress for a video (placeholder for future implementation)"""
    # This would require implementing a more sophisticated upload tracking system
    return jsonify({
        'video_id': video_id,
        'progress': 100,  # Placeholder
        'status': 'completed'
    })

@upload_bp.route('/validate', methods=['POST'])
def validate_upload():
    """Validate video file before upload"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'valid': False,
                'error': f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size (YouTube limit is 256GB, but we'll set a reasonable limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)
        if file_size > max_size:
            return jsonify({
                'valid': False,
                'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }), 400
        
        return jsonify({
            'valid': True,
            'filename': secure_filename(file.filename),
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

