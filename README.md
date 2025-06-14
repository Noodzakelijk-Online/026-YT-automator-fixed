  # YouTube Automator Unified

A comprehensive YouTube automation tool that combines video processing, AI-powered metadata generation, and direct YouTube upload capabilities.

## Features

### Frontend (React/TypeScript)
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Video Upload**: Drag-and-drop video file selection
- **Real-time Processing**: Live updates on video processing status
- **Metadata Management**: Edit and customize video metadata before upload
- **Authentication**: Secure Google OAuth integration
- **Progress Tracking**: Visual upload progress indicators

### Backend (Python/Flask)
- **YouTube API Integration**: Direct video upload to YouTube
- **AI-Powered Metadata**: OpenAI GPT-4 integration for title and description generation
- **Authentication**: Google OAuth2 flow with token management
- **Playlist Management**: Create and manage YouTube playlists
- **Speed Testing**: Network upload speed measurement
- **Transcription**: Video-to-text conversion (extensible)
- **Thumbnail Generation**: Automated thumbnail creation

## Architecture

```
youtube-automator-unified/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   └── assets/         # Static assets
│   ├── public/
│   └── package.json
├── backend/                  # Flask API server
│   ├── app.py              # Main Flask application
│   ├── routes/             # API route modules
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── upload.py       # Video upload endpoints
│   │   ├── metadata.py     # Metadata generation endpoints
│   │   └── playlists.py    # Playlist management endpoints
│   ├── services/           # Business logic services
│   │   ├── youtube_service.py
│   │   ├── transcription_service.py
│   │   └── thumbnail_service.py
│   └── requirements.txt
├── shared/                   # Shared configurations
├── docs/                     # Documentation
└── README.md
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- Google Cloud Project with YouTube Data API v3 enabled
- OpenAI API key (optional, for AI features)

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up Google API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file as `credentials.json`
   - Place it in the `backend/` directory

3. **Configure environment variables:**
   ```bash
   # Create .env file in backend directory
   GOOGLE_CLIENT_SECRETS_FILE=credentials.json
   TOKEN_FILE=token.json
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   ```

4. **Run the backend server:**
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   # Create .env file in frontend directory
   REACT_APP_API_URL=http://localhost:5000/api
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:5173`

## API Endpoints

### Authentication
- `GET /api/auth/status` - Check authentication status
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - Handle OAuth callback
- `POST /api/auth/logout` - Logout user

### Video Upload
- `POST /api/upload/video` - Upload video to YouTube
- `POST /api/upload/validate` - Validate video file

### Metadata Generation
- `POST /api/metadata/generate` - Generate complete metadata
- `POST /api/metadata/title` - Generate title only
- `POST /api/metadata/description` - Generate description only
- `POST /api/metadata/keywords` - Generate keywords

### Playlist Management
- `GET /api/playlists/` - List user playlists
- `POST /api/playlists/` - Create new playlist
- `GET /api/playlists/{id}/videos` - List playlist videos
- `POST /api/playlists/{id}/videos` - Add video to playlist
- `DELETE /api/playlists/{id}` - Delete playlist

### Utilities
- `GET /api/health` - Health check
- `GET /api/speed-test` - Test upload speed

## Usage

1. **Start both servers** (backend and frontend)
2. **Open the application** in your browser
3. **Authenticate** with your Google account
4. **Upload a video** using the file selector
5. **Review and edit** the AI-generated metadata
6. **Upload to YouTube** with a single click

## Features in Detail

### AI-Powered Metadata Generation
The system uses OpenAI's GPT-4 to generate:
- Compelling video titles (max 60 characters)
- Detailed descriptions (200-500 words)
- SEO-optimized tags
- Appropriate category suggestions

### Authentication Flow
- Secure OAuth2 implementation
- Token refresh handling
- Session management
- Graceful error handling

### Video Processing
- File validation and size checking
- Progress tracking during upload
- Error handling and retry logic
- Support for multiple video formats

### Extensible Architecture
- Modular service design
- Easy to add new features
- Configurable AI prompts
- Plugin-ready structure

## Development

### Adding New Features
1. **Backend**: Add new routes in `routes/` directory
2. **Frontend**: Create new components in `src/components/`
3. **Services**: Add business logic in `services/` directory

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Deployment
The application can be deployed using:
- **Frontend**: Vercel, Netlify, or any static hosting
- **Backend**: Heroku, Railway, or any Python hosting service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## Roadmap

- [ ] Advanced transcription with Whisper integration
- [ ] Custom thumbnail templates
- [ ] Batch video processing
- [ ] Analytics dashboard
- [ ] Social media cross-posting
- [ ] Video scheduling with calendar integration
- [ ] Advanced SEO optimization
- [ ] Multi-language support

