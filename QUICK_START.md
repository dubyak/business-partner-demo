# Quick Start Guide - Business Partner AI Demo

## What You Have

1. **Frontend**: `msme-assistant.html` - The chat interface
2. **Backend**: `backend/` folder - Secure API proxy server

## Fastest Way to Deploy (5 minutes)

### Option A: Vercel (Recommended)

**Step 1: Deploy Backend to Vercel**
```bash
# Install Vercel CLI
npm install -g vercel

# Go to backend folder
cd backend

# Install dependencies
npm install

# Deploy
vercel

# Add your API key
vercel env add ANTHROPIC_API_KEY
# Choose: Production
# Paste your Anthropic API key

# Deploy with the key
vercel --prod
```

Vercel will give you a URL like: `https://business-partner-backend.vercel.app`

**Step 2: Update Frontend**

Open `msme-assistant.html` and find this line (around line 383):
```javascript
: 'https://your-backend.vercel.app/api/chat';  // Production - UPDATE THIS
```

Replace with your actual Vercel URL:
```javascript
: 'https://business-partner-backend.vercel.app/api/chat';
```

**Step 3: Deploy Frontend to GitHub Pages**

1. Create a new GitHub repo
2. Upload `msme-assistant.html`
3. Go to Settings → Pages
4. Select: Deploy from branch → main → / (root)
5. Save

Done! Your app will be at: `https://yourusername.github.io/repo-name/msme-assistant.html`

---

### Option B: Just Test Locally (2 minutes)

**Step 1: Start Backend**
```bash
cd backend
npm install
cp .env.example .env
# Edit .env and add your API key
npm start
```

**Step 2: Open Frontend**
Just open `msme-assistant.html` in your browser. It automatically uses `http://localhost:3000`.

That's it! Test locally before deploying.

---

## Need Your Anthropic API Key?

1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Go to API Keys
4. Create a new key
5. Copy it (starts with `sk-ant-`)

## Sharing with Your Team

**After deploying to GitHub Pages:**
- Share the GitHub Pages URL
- Your API key stays secret on Vercel
- Team can use the app without any setup

**For testing:**
- Share the HTML file
- They need to run the backend locally with their own API key

## Troubleshooting

**Problem: "API request failed"**
- Solution: Check your API key in Vercel env variables

**Problem: Can't connect to backend**  
- Local: Is the backend running? (`npm start` in backend folder)
- Production: Did you update the API_URL in the frontend?

**Problem: CORS error**
- The backend should handle this. Double-check the API_URL is correct.

## Cost

- Hosting: Free (Vercel + GitHub Pages)
- API calls: ~$0.01 per demo conversation
- 100 demos ≈ $1

## Questions?

Check the detailed README.md in the backend folder!
