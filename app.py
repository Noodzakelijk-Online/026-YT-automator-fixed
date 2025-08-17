"""
YouTube Automator Unified Backend
Main Flask application combining functionality from both projects
"""

from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
import os
import json
import openai
from datetime import datetime, timezone
from dateutil import parser
import speedtest
import tempfile
import logging

# Import route modules
from routes.auth import auth_bp
from routes.upload import upload_bp
from routes.metadata import metadata_bp
from routes.playlists import playlists_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enable CORS for frontend communication
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])

# YouTube API scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"
]

# Configuration
app.config.update({
    'GOOGLE_CLIENT_SECRETS_FILE': os.environ.get('GOOGLE_CLIENT_SECRETS_FILE', 'credentials.json'),
    'TOKEN_FILE': os.environ.get('TOKEN_FILE', 'token.json'),
    'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
    'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads'),
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024  # 500MB max file size
})

# Set OpenAI API key
if app.config['OPENAI_API_KEY']:
    openai.api_key = app.config['OPENAI_API_KEY']

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(metadata_bp, url_prefix='/api/metadata')
app.register_blueprint(playlists_bp, url_prefix='/api/playlists')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/speed-test')
def speed_test():
    """Test upload speed"""
    try:
        logger.info("Starting speed test...")
        stest = speedtest.Speedtest()
        stest.get_best_server()
        upload_speed = stest.upload() / (1024 * 1024)  # Convert to MB/s
        
        return jsonify({
            'upload_speed_mbps': round(upload_speed, 2),
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

def get_youtube_service():
    """Get authenticated YouTube service"""
    creds = None
    token_path = app.config['TOKEN_FILE']
    
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                return None
        else:
            return None
    
    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Error building YouTube service: {e}")
        return None

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

