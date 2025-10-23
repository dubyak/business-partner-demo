# 🚀 Deploy Commands - Copy & Paste

## 1️⃣ Push to GitHub (Do this first)

```bash
# Create a new repo on GitHub first, then run these commands:

cd /mnt/user-data/outputs

git commit -m "Initial commit: Business Partner AI demo"

git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

git branch -M main

git push -u origin main
```

**Replace YOUR_USERNAME and YOUR_REPO_NAME with your actual GitHub info!**

---

## 2️⃣ Deploy Backend to Vercel

### Option A: Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repo
4. Set Root Directory to: `backend`
5. In Environment Variables, add: `ANTHROPIC_API_KEY` (use your existing key)
6. Click Deploy

### Option B: Via CLI
```bash
cd /mnt/user-data/outputs/backend

vercel --prod
```

You'll get a URL like: `https://business-partner-backend-xyz.vercel.app`

---

## 3️⃣ Update Frontend with Your Backend URL

Open `msme-assistant.html` and find this line (~line 383):
```javascript
: 'https://your-backend.vercel.app/api/chat';
```

Replace with YOUR actual Vercel URL, then save.

Push the update:
```bash
cd /mnt/user-data/outputs

git add msme-assistant.html

git commit -m "Update backend API URL"

git push
```

---

## 4️⃣ Enable GitHub Pages

1. Go to your GitHub repo
2. Settings → Pages
3. Source: Deploy from branch
4. Branch: `main`, Folder: `/ (root)`
5. Save

Your app will be live at:
`https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/msme-assistant.html`

---

## ✅ Test Your Deployment

1. Open your GitHub Pages URL
2. Try uploading a photo and chatting
3. If it works, you're done! 🎉

---

## 🐛 Quick Troubleshooting

**Can't connect to backend?**
- Did you update the API_URL in msme-assistant.html?
- Did you push the change to GitHub?

**Backend not working?**
- Check Vercel dashboard for errors
- Test: `https://your-backend-url.vercel.app/health`

**Need help?**
See VERCEL_DEPLOYMENT.md for detailed troubleshooting.
