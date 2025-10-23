# Business Partner AI Demo - Backend Proxy

This backend proxy securely handles API calls to Anthropic's API, keeping your API key private.

## Quick Start (Local Development)

1. **Install dependencies:**
   ```bash
   cd backend
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   PORT=3000
   ```

3. **Start the server:**
   ```bash
   npm start
   ```
   
   Or with auto-reload during development:
   ```bash
   npm run dev
   ```

4. **Test it's working:**
   Open http://localhost:3000/health in your browser
   You should see: `{"status":"ok","message":"Business Partner API is running"}`

5. **Open the frontend:**
   Open `msme-assistant.html` in your browser. It will automatically use your local backend.

## Deploy to Vercel (Recommended for GitHub Pages)

Vercel is free and perfect for this use case.

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Deploy
```bash
cd backend
vercel
```

Follow the prompts:
- Set up and deploy? **Y**
- Which scope? Choose your account
- Link to existing project? **N**
- Project name? **business-partner-backend** (or your choice)
- Directory? **.** (current directory)
- Override settings? **N**

### Step 3: Add your API key to Vercel
```bash
vercel env add ANTHROPIC_API_KEY
```
- Environment: **Production**
- Value: Your Anthropic API key (sk-ant-xxxxx)

### Step 4: Redeploy with the environment variable
```bash
vercel --prod
```

### Step 5: Update the frontend
Vercel will give you a URL like `https://business-partner-backend.vercel.app`

Open `msme-assistant.html` and update this line:
```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:3000/api/chat'
    : 'https://your-backend.vercel.app/api/chat';  // ← UPDATE THIS
```

Change to your actual Vercel URL:
```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:3000/api/chat'
    : 'https://business-partner-backend.vercel.app/api/chat';
```

### Step 6: Deploy frontend to GitHub Pages

1. Create a new GitHub repository
2. Add `msme-assistant.html` to the repo
3. Go to Settings → Pages
4. Source: Deploy from branch
5. Branch: main (or master), folder: / (root)
6. Save

Your app will be live at: `https://yourusername.github.io/repo-name/msme-assistant.html`

## Alternative: Deploy Both to Vercel

You can also deploy the frontend to Vercel:

```bash
# In the directory with your HTML file
vercel
```

Then you'll have both frontend and backend on Vercel.

## Alternative: Deploy to Netlify

### Backend (Netlify Functions)
1. Create `netlify/functions/chat.js`:
```javascript
const fetch = require('node-fetch');

exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    try {
        const { model, max_tokens, system, messages } = JSON.parse(event.body);

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({ model, max_tokens, system, messages })
        });

        const data = await response.json();
        return {
            statusCode: 200,
            body: JSON.stringify(data)
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};
```

2. Deploy to Netlify
3. Add `ANTHROPIC_API_KEY` in Site Settings → Environment Variables

## Security Notes

✅ **DO:**
- Keep your `.env` file private (it's in `.gitignore`)
- Use environment variables for the API key
- Only share the frontend publicly

❌ **DON'T:**
- Commit `.env` to git
- Put your API key in the frontend code
- Share your backend `.env` file

## Troubleshooting

**"API request failed: 401"**
- Check your API key is correct in Vercel environment variables
- Redeploy after adding the key: `vercel --prod`

**"CORS error"**
- The backend includes CORS headers, but if you see this, check your backend URL is correct in the frontend

**"Cannot connect to backend"**
- For local dev: Make sure the backend is running on port 3000
- For production: Check the API_URL in the frontend matches your deployed backend URL

**Frontend works locally but not on GitHub Pages**
- Make sure you updated the API_URL to your production backend URL
- Check browser console for errors

## Cost Estimation

Anthropic API costs (as of 2025):
- Claude Sonnet 4: ~$3 per million input tokens, ~$15 per million output tokens
- A typical conversation: ~2,000 tokens input, ~500 tokens output = ~$0.01
- 100 demo sessions: ~$1.00

Hosting costs:
- Vercel: Free for hobby projects
- Netlify: Free for hobby projects  
- GitHub Pages: Free

## Questions?

- Vercel docs: https://vercel.com/docs
- Netlify docs: https://docs.netlify.com
- Anthropic API: https://docs.anthropic.com
