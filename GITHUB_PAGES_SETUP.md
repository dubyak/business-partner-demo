# GitHub Pages Setup Guide

## 🎯 Overview

You now have a complete multi-agent AI demo with:
- **Frontend**: Static HTML in `docs/` folder (ready for GitHub Pages)
- **Backend**: Python FastAPI with LangGraph multi-agent system in `python-backend/`

## 📋 Step-by-Step Setup

### Step 1: Commit Your Changes

```bash
cd business-partner-ai

# Add the new directories
git add docs/
git add python-backend/

# Commit
git commit -m "Add Python multi-agent backend and GitHub Pages frontend

- Implemented LangGraph multi-agent architecture with 4 specialized agents
- Added conversation orchestrator, vision analyzer, underwriting engine, and coaching advisor
- Created GitHub Pages frontend with configurable backend URL
- Full Langfuse observability integration
- Compatible with existing demo flow

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### Step 2: Enable GitHub Pages

1. Go to your GitHub repository
2. Click **Settings** → **Pages** (in the left sidebar)
3. Under **Source**, select:
   - Branch: `main`
   - Folder: `/docs`
4. Click **Save**
5. Wait 1-2 minutes for deployment

Your site will be live at: `https://YOUR-USERNAME.github.io/business-partner-ai/`

### Step 3: Deploy Your Python Backend

You need to deploy the Python backend to a publicly accessible URL. Here are your options:

#### Option A: Railway (Recommended - Easiest)

```bash
cd python-backend

# Install Railway CLI
brew install railway  # Mac
# or visit: https://docs.railway.app/develop/cli

# Login and deploy
railway login
railway init
railway up

# Add environment variables
railway variables set ANTHROPIC_API_KEY="your-key"
railway variables set LANGFUSE_SECRET_KEY="your-key"
railway variables set LANGFUSE_PUBLIC_KEY="your-key"
railway variables set LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"

# Get your URL
railway status
```

#### Option B: Render

1. Go to [render.com](https://render.com) and sign up
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name**: `business-partner-ai`
   - **Root Directory**: `python-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment Variables**: Add all from `.env`
5. Click **Create Web Service**
6. Copy your service URL (e.g., `https://business-partner-ai.onrender.com`)

#### Option C: Fly.io

```bash
cd python-backend

# Install flyctl
brew install flyctl  # Mac
# or visit: https://fly.io/docs/hands-on/install-flyctl/

# Login and launch
fly auth login
fly launch

# Set secrets
fly secrets set ANTHROPIC_API_KEY="your-key"
fly secrets set LANGFUSE_SECRET_KEY="your-key"
fly secrets set LANGFUSE_PUBLIC_KEY="your-key"
fly secrets set LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"

# Deploy
fly deploy

# Get your URL
fly status
```

### Step 4: Test Your Deployment

1. Visit your GitHub Pages URL
2. In the config panel, enter your backend URL (from Step 3)
3. Click "Save & Connect"
4. You should see a green indicator in the top-right
5. Start chatting!

## 🔧 Configuration

### Frontend Configuration

The frontend will prompt you to enter your backend URL on first visit. It stores this in `localStorage`.

To change the backend URL:
- Clear your browser's localStorage for the site
- Or edit the URL in the config panel (refresh the page to see it again)

### Backend Configuration

Edit `python-backend/.env`:
```env
ANTHROPIC_API_KEY=your-api-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
PORT=8000
```

## 🎨 Customization

### Update Frontend Styling

Edit `docs/index.html` - all CSS is inline in the `<style>` tag.

### Modify Agent Behavior

Edit the agent files in `python-backend/agents/`:
- `conversation_agent.py` - Main orchestrator
- `vision_agent.py` - Photo analysis
- `underwriting_agent.py` - Loan decisions
- `coaching_agent.py` - Business advice

### Change System Prompt

The frontend sends messages to the backend, which fetches the system prompt from Langfuse. To update:
1. Go to Langfuse → Prompts
2. Edit "business-partner-system"
3. Create a new version
4. The backend will use it automatically (60s cache)

## 🐛 Troubleshooting

### "Error connecting to backend"

1. Check your backend is running (visit `https://your-backend.com/health`)
2. Verify the URL in the frontend config (no trailing slash)
3. Check browser console for CORS errors
4. Ensure `allow_origins=["*"]` is set in `main.py` (line 34)

### "API connection failed"

1. Backend might be sleeping (on free tiers like Render)
2. Wait 30-60 seconds and try again
3. Check backend logs for errors

### Photos not uploading

1. Check file size (should be < 5MB)
2. Only JPEG/PNG supported
3. Check browser console for errors

## 📊 Monitoring

### Langfuse Traces

Visit https://us.cloud.langfuse.com to see:
- Full conversation traces
- Individual agent executions
- Performance metrics
- Token usage

### Backend Logs

Depending on your deployment platform:
- **Railway**: `railway logs`
- **Render**: View in dashboard
- **Fly.io**: `fly logs`

## 🚀 Next Steps

1. **Custom Domain**: Add a custom domain in GitHub Pages settings
2. **Authentication**: Add user auth to the backend
3. **Database**: Store conversation history in a database
4. **More Agents**: Add specialist agents for specific tasks
5. **A/B Testing**: Use Langfuse experiments to test prompts

## 📚 Resources

- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Langfuse Docs](https://langfuse.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
