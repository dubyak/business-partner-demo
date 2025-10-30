# Business Partner AI - Multi-Agent Demo Frontend

This is a GitHub Pages frontend for the Business Partner AI multi-agent demo, powered by LangGraph and Langfuse.

## Features

- 🤖 **Multi-Agent Architecture**: Vision, Underwriting, and Coaching agents orchestrated by LangGraph
- 📊 **Full Observability**: Complete tracing via Langfuse
- 🖼️ **Image Support**: Upload photos for vision analysis
- 💬 **Conversational UI**: Natural loan application flow
- ⚙️ **Configurable**: Point to any backend URL (local or production)

## Quick Start

### For Local Development

1. Start the Python backend:
   ```bash
   cd python-backend
   source venv/bin/activate
   python main.py
   ```

2. Open the frontend:
   - Visit: `http://localhost:8000` (or open `docs/index.html` in a browser)
   - Configure API URL: `http://localhost:8000`
   - Start chatting!

### For Production

1. Deploy the Python backend (see deployment options below)
2. Visit the GitHub Pages site
3. Enter your production backend URL
4. Start using the demo!

## Deployment

### Frontend (GitHub Pages)

Already set up! Just push to the `main` branch and GitHub Pages will serve from the `docs/` folder.

### Backend Deployment Options

#### Option 1: Railway
```bash
cd python-backend
railway login
railway init
railway up
```

#### Option 2: Render
1. Connect your GitHub repo to Render
2. Create a new Web Service
3. Build command: `cd python-backend && pip install -r requirements.txt`
4. Start command: `cd python-backend && python main.py`
5. Add environment variables from `.env`

#### Option 3: Fly.io
```bash
cd python-backend
fly launch
fly deploy
```

## Architecture

```
Frontend (GitHub Pages)
    ↓ HTTP POST /api/chat
Python Backend (FastAPI)
    ↓
LangGraph Multi-Agent System
    ├── Conversation Agent (orchestrator)
    ├── Vision Agent (photo analysis)
    ├── Underwriting Agent (loan decisions)
    └── Coaching Agent (business advice)
    ↓
Langfuse (observability & tracing)
```

## Configuration

The frontend stores two items in localStorage:
- `business-partner-api-url`: Your backend URL
- `business-partner-session-id`: Unique session for Langfuse tracking

## Development

To modify the frontend:
1. Edit `docs/index.html`
2. Test locally by opening in a browser
3. Commit and push to deploy to GitHub Pages

## Support

For issues or questions:
- Check the backend logs for API errors
- Verify CORS is enabled on your backend
- Check Langfuse traces for detailed execution logs
