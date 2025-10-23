# Vercel Deployment Guide

Since you already have Vercel set up with your API key, deployment will be super quick!

## Step 1: Push to GitHub

```bash
# In the outputs folder
git add .
git commit -m "Initial commit: Business Partner AI demo"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy Backend to Vercel

### Option A: Via Vercel Dashboard (Easiest)

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `backend`
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
5. **Environment Variables**: 
   - Click "Add" 
   - Name: `ANTHROPIC_API_KEY`
   - Value: (select from your existing Vercel secrets if available, or paste your key)
6. Click "Deploy"

### Option B: Via Vercel CLI (Faster if you have CLI)

```bash
cd backend
vercel --prod

# When prompted:
# - Link to existing project? N
# - Project name: business-partner-backend (or your choice)
# - Root directory: . (current)
# - Override settings? N

# If you need to add the API key:
vercel env add ANTHROPIC_API_KEY production
# Then paste your API key when prompted

# Redeploy to pick up the env variable:
vercel --prod
```

Your backend will be deployed to something like:
`https://business-partner-backend.vercel.app`

## Step 3: Update Frontend with Backend URL

1. Open `msme-assistant.html`
2. Find line ~383:
   ```javascript
   : 'https://your-backend.vercel.app/api/chat';  // Production - UPDATE THIS
   ```
3. Replace with your actual Vercel URL:
   ```javascript
   : 'https://business-partner-backend.vercel.app/api/chat';
   ```
4. Commit and push:
   ```bash
   git add msme-assistant.html
   git commit -m "Update backend API URL"
   git push
   ```

## Step 4: Enable GitHub Pages

1. Go to your GitHub repo
2. Click "Settings"
3. Click "Pages" in the left sidebar
4. Under "Source":
   - Branch: `main`
   - Folder: `/ (root)`
5. Click "Save"

GitHub will deploy your site to:
`https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/msme-assistant.html`

## Step 5: Test It!

1. Open your GitHub Pages URL
2. Try the demo flow:
   - Answer questions about your business
   - Upload some photos
   - Get a loan offer
   - Try the coaching feature

## Troubleshooting

### Backend not responding
- Check Vercel dashboard for deployment logs
- Verify `ANTHROPIC_API_KEY` is set in environment variables
- Test the health endpoint: `https://your-backend.vercel.app/health`

### Frontend can't connect to backend
- Check browser console for errors
- Verify the API_URL in `msme-assistant.html` matches your Vercel URL
- Make sure you pushed the updated file to GitHub

### CORS errors
- The backend is configured to allow all origins
- If you see CORS errors, check the backend is actually running

## Vercel Environment Variables

If you need to check/update your API key on Vercel:

1. Go to your project on Vercel dashboard
2. Click "Settings" tab
3. Click "Environment Variables"
4. You should see `ANTHROPIC_API_KEY` listed
5. To update: Delete and re-add with new value
6. Redeploy for changes to take effect

## Updating the App

To make changes:
```bash
# Make your edits
git add .
git commit -m "Description of changes"
git push

# Backend changes auto-deploy via Vercel
# Frontend changes auto-deploy via GitHub Pages
```

## Need to Redeploy Backend?

```bash
cd backend
vercel --prod
```

That's it! 🎉
