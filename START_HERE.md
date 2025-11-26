# 🎯 START HERE - Supabase Setup

## Your Supabase project is ready to provision!

Everything has been prepared for you. Just follow the simple steps below.

---

## ⚡ Quick Start (3 minutes)

### Step 1: Run the setup script

```bash
cd /Users/wkendall/Documents/GitHub/business-partner-demo
./setup-supabase.sh
```

This will guide you through:
- Installing Supabase CLI
- Logging in to Supabase
- Creating/linking your project
- Applying all database migrations
- Getting your credentials

### Step 2: Add credentials to your .env files

After the script completes, add these to your environment files:

**`backend/.env`**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...
```

**`python-backend/.env`**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

### Step 3: Done! 🎉

Your database is now fully provisioned with:
- ✅ 6 tables (user_profiles, conversations, messages, business_profiles, loan_applications, photo_analyses)
- ✅ Row Level Security enabled
- ✅ Storage bucket for photos
- ✅ All indexes and triggers

---

## 📁 What's Available

### Automated Setup
- **`setup-supabase.sh`** ← Run this for automated setup

### Database Schema
- **`supabase/migrations/`** ← All migrations ready to deploy
  - `20241117000000_initial_schema.sql` - Tables, RLS, indexes
  - `20241117000001_storage_policies.sql` - Storage setup

### Configuration
- **`supabase/config.toml`** ← Supabase project config
- **`supabase/seed.sql`** ← Optional test data

### Documentation
- **`SETUP_COMPLETE.md`** ← Overview of what was created
- **`SUPABASE_README.md`** ← Main setup guide
- **`SUPABASE_CLI_SETUP.md`** ← Detailed CLI guide
- **`SUPABASE_QUICK_REFERENCE.md`** ← Command cheat sheet
- **`SUPABASE_INTEGRATION_CHECKLIST.md`** ← Code integration steps

### Standalone Files
- **`supabase-schema.sql`** ← SQL file (if you prefer manual dashboard setup)
- **`SUPABASE_SETUP_GUIDE.md`** ← Manual dashboard setup guide

---

## 🎬 Your Options

### Option A: Automated (Recommended) ⭐

```bash
./setup-supabase.sh
```

**Pros:**
- ✅ Fastest (3 minutes)
- ✅ Automated
- ✅ No manual steps
- ✅ Includes verification

### Option B: Manual CLI

```bash
npm install -g supabase
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

**Pros:**
- ✅ More control
- ✅ Good for existing projects

See: `SUPABASE_CLI_SETUP.md`

### Option C: Dashboard + SQL

1. Create project at https://app.supabase.com
2. Copy `supabase-schema.sql` contents
3. Paste in SQL Editor
4. Run

**Pros:**
- ✅ Visual interface
- ✅ No CLI needed

See: `SUPABASE_SETUP_GUIDE.md`

---

## 🔍 Verify Setup

After running setup, verify everything worked:

```bash
# Check CLI is logged in
supabase projects list

# Check migrations applied
supabase db diff
# Should output: "No schema differences detected"

# View in Studio (optional)
supabase start
open http://localhost:54323
```

---

## 📊 Your Database Schema

```
user_profiles         → User business information
  ├── user_id (PK)
  ├── business_name
  ├── business_type
  └── location

conversations         → Chat sessions
  ├── id (PK)
  ├── user_id (FK)
  ├── session_id
  └── started_at

messages              → Individual messages
  ├── id (PK)
  ├── conversation_id (FK)
  ├── role (user/assistant)
  └── content (JSONB)

business_profiles     → Detailed business data
  ├── id (PK)
  ├── user_id (FK)
  ├── monthly_revenue
  └── monthly_expenses

loan_applications     → Loan tracking
  ├── id (PK)
  ├── user_id (FK)
  ├── loan_amount
  ├── risk_score
  └── status

photo_analyses        → Vision AI results
  ├── id (PK)
  ├── user_id (FK)
  ├── cleanliness_score
  └── organization_score

storage.business-photos → Photo uploads
```

---

## 🚦 Next Steps After Setup

### 1. Install Client Libraries

```bash
cd backend
npm install @supabase/supabase-js

cd ../python-backend
pip install supabase
```

### 2. Initialize Supabase in Your Code

**Node.js Backend**
```javascript
const { createClient } = require('@supabase/supabase-js')
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)
```

**Python Backend**
```python
from supabase import create_client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
```

### 3. Implement Authentication

See `SUPABASE_INTEGRATION_CHECKLIST.md` for:
- Frontend signup/login UI
- Backend JWT verification
- Database operations

---

## 📚 Help & Documentation

| Question | See |
|----------|-----|
| How do I run the setup? | This file (START_HERE.md) |
| What CLI commands are available? | SUPABASE_QUICK_REFERENCE.md |
| How do I integrate into my code? | SUPABASE_INTEGRATION_CHECKLIST.md |
| Prefer manual setup? | SUPABASE_SETUP_GUIDE.md |
| Need detailed CLI help? | SUPABASE_CLI_SETUP.md |

---

## 🆘 Troubleshooting

### "supabase: command not found"
```bash
npm install -g supabase
```

### "Not logged in"
```bash
supabase login
```

### "No linked project"
```bash
supabase projects list
supabase link --project-ref YOUR_PROJECT_REF
```

---

## ✅ Success Checklist

After setup, you should have:

- [ ] Supabase CLI installed
- [ ] Logged in to Supabase
- [ ] Project created or linked
- [ ] Migrations applied (6 tables)
- [ ] Storage bucket created
- [ ] API keys retrieved
- [ ] .env files updated
- [ ] Verification complete

---

## 🎉 Ready?

**Run this command to get started:**

```bash
./setup-supabase.sh
```

**It's that simple!** ✨

The script will guide you through everything. When it's done, you'll have a fully provisioned Supabase database ready to use.

---

**Questions?** Check the documentation files or visit https://supabase.com/docs

