# Easy Deployment Options - Pick Your Platform

I've created deployment configs for multiple platforms. Choose whichever you're already logged into!

---

## 🎯 **Option 1: Render (Easiest - Web UI)**

**Best if:** You want to click through a web interface

### Steps:
1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. **Connect your GitHub repo** (or select "Deploy from Git URL")
4. Configure:
   - **Name**: `business-partner-ai`
   - **Root Directory**: `python-backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. **Environment Variables** - Add these:
   ```
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   LANGFUSE_SECRET_KEY=your-langfuse-secret-key-here
   LANGFUSE_PUBLIC_KEY=your-langfuse-public-key-here
   LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
   PORT=8000
   ```
6. Click **"Create Web Service"**
7. Wait 2-3 minutes for deployment
8. Copy your URL: `https://business-partner-ai.onrender.com`

**Free Tier:** ✅ Yes! (slower cold starts, but perfect for demos)

---

## 🚂 **Option 2: Railway (CLI - 2 Minutes)**

**Best if:** You want the fastest/best performance

### Steps:
```bash
cd "/Users/wkendall/Downloads/Claude Code Projects/business partner demo/business-partner-ai/python-backend"

# Login (opens browser)
railway login

# Initialize & deploy
railway init
railway up

# Add environment variables (easiest via dashboard)
railway open
# Click Variables tab, add the 5 variables from above

# Generate public URL
# In dashboard: Settings → Networking → Generate Domain
```

**Free Tier:** ✅ $5 credits (~500 hours)

---

## ✈️ **Option 3: Fly.io (CLI - If you have an account)**

**Best if:** You want global CDN and auto-scaling

### Steps:
```bash
cd "/Users/wkendall/Downloads/Claude Code Projects/business partner demo/business-partner-ai/python-backend"

# Check if logged in
fly auth whoami

# If not logged in:
# fly auth login

# Deploy (will auto-detect Dockerfile)
fly launch --no-deploy

# Set environment variables
fly secrets set ANTHROPIC_API_KEY="your-anthropic-api-key-here"
fly secrets set LANGFUSE_SECRET_KEY="your-langfuse-secret-key-here"
fly secrets set LANGFUSE_PUBLIC_KEY="your-langfuse-public-key-here"
fly secrets set LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"

# Deploy
fly deploy

# Get URL
fly status
```

**Free Tier:** ✅ 3 shared VMs

---

## 🐳 **Option 4: Any Docker Platform**

I've created a `Dockerfile` so you can deploy to:
- Google Cloud Run
- AWS ECS
- Azure Container Apps
- DigitalOcean App Platform
- Etc.

### Generic Docker deployment:
```bash
cd python-backend

# Build
docker build -t business-partner-ai .

# Run locally to test
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY="..." \
  -e LANGFUSE_SECRET_KEY="..." \
  -e LANGFUSE_PUBLIC_KEY="..." \
  -e LANGFUSE_BASE_URL="https://us.cloud.langfuse.com" \
  business-partner-ai

# Then push to your container registry and deploy
```

---

## 🔥 **Quick Comparison**

| Platform | Setup Time | Free Tier | Best For |
|----------|------------|-----------|----------|
| **Render** | 5 min (web UI) | ✅ Yes | Beginners, web UI lovers |
| **Railway** | 2 min (CLI) | ✅ $5 credits | Best performance/DX |
| **Fly.io** | 3 min (CLI) | ✅ 3 VMs | Global CDN, scaling |
| **Docker** | Varies | Depends | Any platform, full control |

---

## 🎯 **My Recommendation**

### For this demo: **Render**
1. No CLI needed - just use the web dashboard
2. Free tier works great
3. 5-minute setup
4. Auto-deploys from GitHub

### Steps right now:
1. Push your code to GitHub first:
   ```bash
   cd "/Users/wkendall/Downloads/Claude Code Projects/business partner demo/business-partner-ai"
   git add .
   git commit -m "Add Python multi-agent backend"
   git push origin main
   ```

2. Go to [render.com](https://render.com) → New Web Service → Select your repo

3. Done!

---

## 📱 **After Deployment**

Once you have a URL from any platform:

### Update Your Frontend:
1. Open your frontend (already open in browser)
2. Enter your backend URL
3. Click "Save & Connect"
4. Green indicator = success! 🎉

### Enable GitHub Pages:
```bash
# Already pushed code, so just:
# Go to repo Settings → Pages
# Source: main branch, /docs folder
# Save
```

Your demo will be live at: `https://YOUR-USERNAME.github.io/business-partner-ai/`

---

## 🆘 **Need Help?**

### Check if logged into platforms:
```bash
# Railway
railway whoami

# Fly.io
fly auth whoami

# Vercel (already logged in)
vercel whoami
```

### Test local backend right now:
Your Python backend is **running on http://localhost:8000**

Test it immediately:
1. Open frontend in browser
2. Backend URL: `http://localhost:8000`
3. Works perfectly! 🚀

---

**Pick any option above and you'll be deployed in under 5 minutes!**
