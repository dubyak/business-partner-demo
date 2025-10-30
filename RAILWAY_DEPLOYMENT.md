# Deploy to Railway - Step by Step

## 🚂 Railway Deployment (5 Minutes)

Railway is **perfect** for this application - it runs Python apps as persistent servers, not serverless functions.

### Free Tier:
- ✅ $5 in credits (500 execution hours)
- ✅ Perfect for demos and testing
- ✅ No credit card required for trial

---

## Step 1: Login to Railway

Open your terminal and run:

```bash
cd "/Users/wkendall/Downloads/Claude Code Projects/business partner demo/business-partner-ai/python-backend"

railway login
```

This will open your browser for authentication.

---

## Step 2: Initialize Project

```bash
railway init
```

You'll be asked:
- **"Starting Point"**: Select "Empty Project"
- **"Project Name"**: Enter "business-partner-ai" (or whatever you like)

---

## Step 3: Deploy

```bash
railway up
```

This will:
- Upload your code
- Install dependencies from requirements.txt
- Start the server

Wait for it to complete (1-2 minutes).

---

## Step 4: Add Environment Variables

You can do this two ways:

### Option A: Via Dashboard (Easiest)

1. Run: `railway open`
2. Click on your service
3. Go to "Variables" tab
4. Add these variables:

```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
LANGFUSE_SECRET_KEY=your-langfuse-secret-key-here
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key-here
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
PORT=8000
```

5. Click "Deploy" (it will restart with the new variables)

### Option B: Via CLI

```bash
railway variables set ANTHROPIC_API_KEY="your-anthropic-api-key-here"

railway variables set LANGFUSE_SECRET_KEY="your-langfuse-secret-key-here"

railway variables set LANGFUSE_PUBLIC_KEY="your-langfuse-public-key-here"

railway variables set LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"

railway variables set PORT="8000"
```

---

## Step 5: Get Your Public URL

### Option A: Via Dashboard
1. Run: `railway open`
2. Click "Settings" tab
3. Scroll to "Networking"
4. Click "Generate Domain"
5. Copy your URL (e.g., `https://business-partner-ai-production-xxxx.up.railway.app`)

### Option B: Via CLI
```bash
railway domain
```

Follow the prompts to generate a domain.

---

## Step 6: Test Your Deployment

```bash
# Replace with your Railway URL
curl https://your-app.up.railway.app/health
```

You should see:
```json
{"status":"ok","message":"Business Partner AI (Python/LangGraph) is running","version":"2.0.0"}
```

---

## Step 7: Update Your Frontend

1. Open your GitHub Pages frontend
2. Enter your Railway URL: `https://your-app.up.railway.app`
3. Click "Save & Connect"
4. You should see a green indicator!
5. Start chatting! 🎉

---

## Troubleshooting

### "Build failed"
- Check logs: `railway logs`
- Usually means a missing dependency in requirements.txt

### "App not responding"
- Check if it's running: `railway status`
- View logs: `railway logs`
- Restart: `railway up`

### "Health endpoint returns error"
- Wait 30 seconds for app to fully start
- Check environment variables are set: `railway variables`

### "Out of memory"
- Your app needs more RAM
- Upgrade to Railway Pro ($5/month per service)

---

## Quick Commands Reference

```bash
# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open

# Restart app
railway up

# List environment variables
railway variables

# SSH into your running container (for debugging)
railway shell
```

---

## Cost Monitoring

To check your usage:
```bash
railway open
```

Then click on "Usage" in the left sidebar.

You'll see:
- CPU hours used
- Memory usage
- Credits remaining

**Typical usage for this app**: ~0.5-1 credits per day of active testing

---

## After Deployment

### Push to GitHub
Once everything works:

```bash
cd "/Users/wkendall/Downloads/Claude Code Projects/business partner demo/business-partner-ai"

git add docs/ python-backend/ *.md
git commit -m "Add Python multi-agent backend with Railway deployment"
git push origin main
```

### Enable GitHub Pages
1. Go to repo Settings → Pages
2. Source: main branch, /docs folder
3. Save

Your frontend will be at: `https://YOUR-USERNAME.github.io/business-partner-ai/`

---

## 🎯 Expected Result

After following these steps:

✅ Backend running on Railway: `https://your-app.up.railway.app`
✅ Frontend on GitHub Pages: `https://your-username.github.io/business-partner-ai/`
✅ Full multi-agent conversation flow working
✅ Langfuse tracing all interactions
✅ Professional demo ready to share!

---

## Need Help?

If you get stuck at any step, the error messages are usually clear. Common fixes:
- Wait a bit longer (initial deploy takes 1-2 min)
- Check environment variables are set
- View logs: `railway logs`
- Restart: `railway up`

**Your local backend is still running on http://localhost:8000 - you can test with that while setting up Railway!**
