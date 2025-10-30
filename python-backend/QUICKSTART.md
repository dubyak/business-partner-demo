# Quick Start Guide - Python/LangGraph Backend

Get the multi-agent backend running in 3 minutes!

## Prerequisites

- Python 3.10 or higher
- Your existing Anthropic API key
- Langfuse credentials (already configured in .env)

## Setup

### 1. Create Virtual Environment
```bash
cd python-backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (web server)
- LangGraph & LangChain (agent orchestration)
- Langfuse (observability)
- Anthropic SDK

### 3. Verify Environment Variables
```bash
# Check that .env exists and has required vars
cat .env
```

Should see:
- ✓ `ANTHROPIC_API_KEY`
- ✓ `LANGFUSE_SECRET_KEY`
- ✓ `LANGFUSE_PUBLIC_KEY`
- ✓ `LANGFUSE_BASE_URL`

### 4. Start the Server
```bash
python main.py
```

You should see:
```
🚀 Starting Business Partner AI (Python/LangGraph)
📍 Server: http://localhost:8000
🏥 Health: http://localhost:8000/health
💬 Chat API: http://localhost:8000/api/chat

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Test It

### Option 1: Test with curl
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, I own a grocery store"}],
    "session_id": "test-session-1"
  }'
```

### Option 2: Test with Frontend
1. Open `msme-assistant.html` in your browser
2. Update the API URL temporarily:
   ```javascript
   const API_URL = 'http://localhost:8000/api/chat';
   ```
3. Start chatting!

### Option 3: Test Health Endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "message": "Business Partner AI (Python/LangGraph) is running",
  "version": "2.0.0"
}
```

## Verify Langfuse Integration

1. Make a few test requests (send 2-3 messages with the frontend or curl)
2. Go to https://us.cloud.langfuse.com
3. Navigate to **Tracing** → **Traces**
4. Find your session
5. Expand to see agent executions:
   - conversation-agent-process
   - vision-agent-analyze (if you uploaded photos)
   - underwriting-agent-process (if info was complete)
   - coaching-agent-generate (if loan was accepted)

## What to Try

### Test Photo Analysis
1. Send a message about your business
2. Upload a photo (click the + button)
3. Watch in Langfuse:
   - `vision-agent-analyze` span appears
   - Check input/output to see extracted insights

### Test Underwriting
1. Complete the business info questions
2. Upload at least one photo
3. Watch in Langfuse:
   - `underwriting-agent-calculate-risk` span
   - `underwriting-agent-generate-offer` span
   - See risk score and loan offer in metadata

### Test Multi-Agent Flow
Have a complete conversation:
1. Introduce your business
2. Answer questions
3. Upload photos
4. Get loan offer
5. Accept the loan
6. Receive coaching

Check Langfuse - you'll see all agents being called in sequence!

## Common Issues

### "Module not found" Error
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### Port 8000 Already in Use
```bash
# Change port in .env
PORT=8001

# Or specify when running
PORT=8001 python main.py
```

### Langfuse Traces Not Appearing
- Wait 5-10 seconds for data to sync
- Check environment variables are correct
- Verify network access to Langfuse

### "Invalid API Key" from Anthropic
- Check `.env` has your real Anthropic API key
- Restart server after updating .env

## Next Steps

✅ **Server running?** Great! Now:

1. **Explore the Code**
   - Check out `agents/` to see how each specialist works
   - Look at `graph.py` to understand the orchestration
   - Read `state.py` to see what data flows between agents

2. **Compare Architectures**
   - Run both Node.js backend (port 3000) and Python backend (port 8000)
   - Toggle between them in the frontend
   - Compare Langfuse traces - single-agent vs multi-agent

3. **Extend It**
   - Add a new agent (e.g., document verification)
   - Modify underwriting logic
   - Connect to your production APIs

4. **Deploy It**
   - See README.md for deployment options
   - Docker, traditional hosting, or cloud platforms

## Getting Help

- Read the full [README.md](README.md) for detailed documentation
- Check LangGraph docs: https://langchain-ai.github.io/langgraph/
- Review Langfuse docs: https://langfuse.com/docs
- Look at agent code - it's well-commented!

---

**Happy building!** 🚀
