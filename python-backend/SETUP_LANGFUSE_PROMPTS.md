# 🚀 Automated Langfuse Prompt Setup

I've created a script to automatically create the Langfuse prompts for you!

## 📋 What It Does

The script `setup-langfuse-prompts.py` will:
1. ✅ Create `vision-agent-system` prompt (if it doesn't exist)
2. ✅ Create `coaching-agent-system` prompt (if it doesn't exist)
3. ✅ Verify `business-partner-system` prompt exists

## 🔧 Option 1: Run Locally (Recommended)

### Step 1: Get Your Langfuse Credentials

Your Langfuse credentials are already set in Railway. You can:

**A. Get from Railway Dashboard:**
1. Go to Railway dashboard → Your project → Variables
2. Copy:
   - `LANGFUSE_SECRET_KEY`
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_BASE_URL` (if custom)

**B. Get from Railway CLI:**
```bash
railway variables
```

### Step 2: Set Credentials Locally

Create/update `python-backend/.env`:

```bash
cd python-backend
cat > .env << EOF
LANGFUSE_SECRET_KEY=your_secret_key_from_railway
LANGFUSE_PUBLIC_KEY=your_public_key_from_railway
LANGFUSE_BASE_URL=https://cloud.langfuse.com
EOF
```

### Step 3: Run the Script

```bash
cd python-backend
python3 setup-langfuse-prompts.py
```

You should see:
```
🚀 Setting up Langfuse prompts for all agents...

📍 Langfuse Base URL: https://cloud.langfuse.com
✓ Langfuse credentials found

📝 Creating prompt 'vision-agent-system'...
✓ Successfully created prompt 'vision-agent-system'
  Status: Published

📝 Creating prompt 'coaching-agent-system'...
✓ Successfully created prompt 'coaching-agent-system'
  Status: Published

🔍 Checking conversation prompt 'business-partner-system'...
✓ Prompt 'business-partner-system' exists (version 1)

============================================================
📊 Summary:
============================================================
✓ Vision Agent prompt: Ready
✓ Coaching Agent prompt: Ready
✓ Conversation Agent prompt: Ready

🎉 All prompts are ready!
```

---

## 🔧 Option 2: Run on Railway (Temporary)

You can also run the script on Railway temporarily:

1. **SSH into Railway deployment** (if available)
2. **Or add as one-time script** in Railway
3. Set environment variables in Railway
4. Run the script

---

## 🔧 Option 3: Manual Setup (If Script Fails)

If you prefer to create them manually:

### 1. Vision Agent Prompt

1. Go to https://cloud.langfuse.com → **Prompts**
2. Click **"+ New Prompt"**
3. Fill in:
   - **Name**: `vision-agent-system`
   - **Type**: Text
   - **Content**:
   ```
   You are a business consultant analyzing photos of small businesses.

   Your task: Analyze the photo and provide:
   1. Cleanliness score (0-10): How clean and well-maintained is the space?
   2. Organization score (0-10): How organized is the inventory/workspace?
   3. Stock level: "low", "medium", or "high" - how well-stocked does it appear?
   4. 2-3 specific observations about what you see
   5. 1-2 actionable coaching tips to improve the business

   Be specific, practical, and encouraging. Focus on visual signals that indicate business health.
   ```
4. Click **"Create"**
5. Click **"Publish"** (important!)

### 2. Coaching Agent Prompt

1. Same steps as above
2. **Name**: `coaching-agent-system`
3. **Content**:
   ```
   You are an experienced business coach helping small business owners grow.

   Your task: Provide 3-4 specific, actionable coaching tips based on:
   - Business type and operations
   - Visual insights from their photos
   - Their stated goals for the loan

   Be:
   - Specific and actionable (not generic advice)
   - Encouraging and supportive
   - Focused on practical next steps
   - Relevant to their specific business type

   Format your response as a friendly paragraph with 3-4 concrete suggestions.
   ```
4. Click **"Publish"**

---

## ✅ After Running

Once prompts are created:

1. **Verify in Langfuse Dashboard**: Go to Prompts → Check all 3 exist
2. **Deploy Code**: Push your changes to trigger Railway deployment
3. **Check Logs**: Railway logs should show:
   ```
   [LANGFUSE-VISION] ✓ Prompt fetched successfully (v1)
   [LANGFUSE-COACHING] ✓ Prompt fetched successfully (v1)
   [LANGFUSE] ✓ Prompt fetched successfully (v1)
   ```

---

## 🆘 Troubleshooting

### Error: "Invalid credentials"
- Check `.env` file has correct keys
- Verify keys match Railway variables
- Ensure `LANGFUSE_BASE_URL` is correct

### Error: "Prompt already exists"
- That's fine! Script will skip and report it exists
- You can update it manually in Langfuse UI

### Script Won't Run
- Make sure you're in `python-backend/` directory
- Verify `python3` is available
- Check Langfuse SDK is installed: `pip install langfuse`

---

**The automated script makes this much easier! Just get your credentials from Railway and run it locally.** 🚀


