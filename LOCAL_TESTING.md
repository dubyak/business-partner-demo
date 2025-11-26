# 🧪 Local Testing Guide

## Quick Start - Test the Demo Locally

### Option 1: Simple File Opening (Frontend Only)
If you just want to see the UI and scenario selector:

1. **Open the HTML file directly:**
   ```bash
   open msme-assistant.html
   ```
   Or navigate to: `file:///Users/wkendall/Documents/GitHub/business-partner-demo/msme-assistant.html`

2. **Note:** The chat won't work without a backend, but you can see the scenario selector and UI!

### Option 2: Full Local Testing (Frontend + Backend)

#### Step 1: Start the Python Backend

```bash
cd python-backend
python main.py
```

You should see:
```
🚀 Starting Business Partner AI (Python/LangGraph)
📍 Server: http://localhost:8000
🏥 Health: http://localhost:8000/health
💬 Chat API: http://localhost:8000/api/chat
```

#### Step 2: Update Frontend API URL (if needed)

The frontend is currently configured to use `localhost:3000` for local development. You have two options:

**Option A: Use Python Backend (Port 8000)**
Update line 1963 in `msme-assistant.html`:
```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api/chat'  // Python backend
    : 'https://your-production-url.com/api/chat';
```

**Option B: Use Simple HTTP Server**
If you want to test with a simple server:

```bash
# Python 3
python3 -m http.server 3000

# Or Node.js (if you have it)
npx http-server -p 3000
```

Then open: **http://localhost:3000/msme-assistant.html**

### Option 3: Test Architecture Diagram

Just open the architecture diagram:
```bash
open architecture-diagram.html
```

Or navigate to: `file:///Users/wkendall/Documents/GitHub/business-partner-demo/architecture-diagram.html`

## 🎯 Recommended Testing Flow

1. **Start Backend:**
   ```bash
   cd python-backend
   python main.py
   ```

2. **Update API URL** in `msme-assistant.html` to point to `http://localhost:8000/api/chat`

3. **Open Frontend:**
   - Use a simple HTTP server: `python3 -m http.server 3000`
   - Or open directly: `open msme-assistant.html` (but update API URL first)

4. **Test Scenarios:**
   - Try "New Customer" scenario
   - Try "Active Loan - Good Standing" scenario  
   - Try "Past Due" scenario
   - Use the "Reset Demo" button to switch between scenarios

## 🔍 Verify It's Working

1. **Check Backend Health:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok",...}`

2. **Test Chat:**
   - Open the frontend
   - Select a scenario
   - Send a message
   - You should get a response!

## 🐛 Troubleshooting

**Backend won't start?**
- Check you're in the `python-backend` directory
- Make sure you have a `.env` file with `ANTHROPIC_API_KEY`
- Check Python version: `python --version` (needs 3.10+)

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify API_URL in `msme-assistant.html` matches your backend port

**CORS errors?**
- The Python backend has CORS enabled for all origins
- If you see CORS errors, check the backend is actually running

## 📝 Quick Reference URLs

- **Frontend (local):** `http://localhost:3000/msme-assistant.html` or `file:///path/to/msme-assistant.html`
- **Backend API:** `http://localhost:8000/api/chat`
- **Backend Health:** `http://localhost:8000/health`
- **Architecture Diagram:** `file:///path/to/architecture-diagram.html`

