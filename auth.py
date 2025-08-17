"""
Authentication routes for YouTube API OAuth2 flow
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import json
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/status')
def auth_status():
    """Check authentication status"""
    token_path = current_app.config['TOKEN_FILE']
    
    if not os.path.exists(token_path):
        return jsonify({'authenticated': False, 'message': 'No token file found'})
    
    try:
        creds = Credentials.from_authorized_user_file(token_path, current_app.config.get('SCOPES', []))
        
        if not creds or not creds.valid:
            return jsonify({'authenticated': False, 'message': 'Invalid or expired credentials'})
        
        return jsonify({
            'authenticated': True,
            'message': 'User is authenticated',
            'expires_at': creds.expiry.isoformat() if creds.expiry else None
        })
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({'authenticated': False, 'message': 'Error checking authentication'}), 500

@auth_bp.route('/login')
def login():
    """Initiate OAuth2 flow"""
    try:
        flow = Flow.from_client_secrets_file(
            current_app.config['GOOGLE_CLIENT_SECRETS_FILE'],
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/youtube.force-ssl",
                "https://www.googleapis.com/auth/youtube"
            ],
            redirect_uri=url_for('auth.callback', _external=True)
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for verification
        session['oauth_state'] = state
        
        return jsonify({
            'auth_url': auth_url,
            'state': state,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@auth_bp.route('/callback')
def callback():
    """Handle OAuth2 callback"""
    try:
        # Verify state parameter
        if 'oauth_state' not in session:
            return jsonify({'error': 'Invalid session state'}), 400
        
        state = session.get('oauth_state')
        
        flow = Flow.from_client_secrets_file(
            current_app.config['GOOGLE_CLIENT_SECRETS_FILE'],
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/youtube.force-ssl",
                "https://www.googleapis.com/auth/youtube"
            ],
            state=state,
            redirect_uri=url_for('auth.callback', _external=True)
        )
        
        # Fetch token using authorization response
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        # Save credentials to file
        token_path = current_app.config['TOKEN_FILE']
        with open(token_path, 'w') as token_file:
            token_file.write(credentials.to_json())
        
        # Clear session state
        session.pop('oauth_state', None)
        
        # Return success page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .success {
                    color: #4CAF50;
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                }
                .message {
                    color: #666;
                    margin-bottom: 1rem;
                }
                .close-btn {
                    background: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1rem;
                }
                .close-btn:hover {
                    background: #1976D2;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓ Authentication Successful!</div>
                <div class="message">You can now close this window and return to the application.</div>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .error {{
                    color: #f44336;
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">✗ Authentication Failed</div>
                <div>Error: {str(e)}</div>
            </div>
        </body>
        </html>
        ''', 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user by removing token file"""
    try:
        token_path = current_app.config['TOKEN_FILE']
        
        if os.path.exists(token_path):
            os.remove(token_path)
        
        # Clear session
        session.clear()
        
        return jsonify({
            'message': 'Successfully logged out',
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

