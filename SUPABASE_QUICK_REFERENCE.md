# Supabase Quick Reference Card
## Business Partner AI Demo

---

## 🔑 Your Project Credentials

```bash
# Save these immediately after project creation:
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...     # Frontend safe ✅
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Backend only ⚠️
```

**Where to find them**: Dashboard → Settings → API

---

## 📋 Setup Checklist (Quick)

1. ✅ Create project at https://app.supabase.com
2. ✅ Save credentials (URL + keys)
3. ✅ Run `supabase-schema.sql` in SQL Editor
4. ✅ Verify 6 tables created (Table Editor)
5. ✅ Check RLS enabled (shield icons 🛡️)
6. ✅ Configure Auth providers (Authentication → Providers)
7. ✅ Add redirect URLs (Authentication → URL Configuration)
8. ✅ Create storage bucket: `business-photos`
9. ✅ Add storage policies (3 policies)
10. ✅ Update `.env` files in your project
11. ✅ Test with a user signup

---

## 📊 Database Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `user_profiles` | User business info | user_id, business_name, location |
| `conversations` | Chat sessions | id, user_id, session_id |
| `messages` | Individual messages | conversation_id, role, content |
| `business_profiles` | Detailed business data | user_id, revenue, expenses |
| `loan_applications` | Loan tracking | user_id, loan_amount, status |
| `photo_analyses` | Vision AI results | user_id, scores, insights |

---

## 🔐 Authentication Setup

### Enable Email Auth
**Path**: Authentication → Providers → Email

### Configure Redirect URLs
**Path**: Authentication → URL Configuration

```
Add these URLs:
- http://localhost:3000/**
- http://127.0.0.1:3000/**
- https://yourdomain.com/**
- https://*.github.io/**
```

### Create Test User
**Path**: Authentication → Users → Add user

```
Email: test@example.com
Password: TestPassword123!
Auto Confirm: ✅ (for testing)
```

---

## 📦 Storage Setup

### Create Bucket
**Path**: Storage → Create bucket

```
Name: business-photos
Public: ❌ (use RLS)
Size limit: 5MB
Types: image/jpeg, image/png, image/webp
```

### Add Policies (Run in SQL Editor)

```sql
-- Upload policy
CREATE POLICY "Users can upload own photos"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
  bucket_id = 'business-photos' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- View policy
CREATE POLICY "Users can view own photos"
ON storage.objects FOR SELECT TO authenticated
USING (
  bucket_id = 'business-photos' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Delete policy
CREATE POLICY "Users can delete own photos"
ON storage.objects FOR DELETE TO authenticated
USING (
  bucket_id = 'business-photos' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

---

## 🧪 Testing Queries

### Verify Tables
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

### Check RLS Enabled
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

### Count Policies
```sql
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;
```

### View All Indexes
```sql
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

### Check Triggers
```sql
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY event_object_table;
```

---

## 💻 Installation Commands

### Node.js Backend
```bash
cd backend
npm install @supabase/supabase-js
```

### Python Backend
```bash
cd python-backend
pip install supabase
```

---

## 📝 Environment Variables Template

### `/backend/.env`
```bash
# Existing
ANTHROPIC_API_KEY=sk-ant-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_PROMPT_NAME=business-partner-system

# NEW: Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...

PORT=3000
```

### `/python-backend/.env`
```bash
# Existing
ANTHROPIC_API_KEY=sk-ant-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# NEW: Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

---

## 🎯 Client Initialization Code

### JavaScript (Frontend)
```javascript
// Add to msme-assistant.html
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://xxxxxxxxxxxxx.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGc...'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
```

### Node.js (Backend)
```javascript
// Add to backend/server.js
const { createClient } = require('@supabase/supabase-js')

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)
```

### Python (Backend)
```python
# Add to python-backend/main.py
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
```

---

## 🔍 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "relation does not exist" | Run SQL schema again |
| "permission denied" | Check RLS policies created |
| Can't insert data | RLS working! Need auth user |
| Storage upload fails | Verify storage policies |
| "Invalid API key" | Check using correct key type |
| CORS errors | Check redirect URLs configured |

---

## 🛡️ Security Reminders

- ❌ **NEVER** commit `.env` files
- ❌ **NEVER** use service_role key in frontend
- ✅ **ALWAYS** use anon key for client-side
- ✅ **ALWAYS** verify RLS policies working
- ✅ **ALWAYS** enable email confirmation in production

---

## 📱 Dashboard Quick Links

Once logged in to your Supabase project:

- **Tables**: https://app.supabase.com/project/_/editor
- **SQL Editor**: https://app.supabase.com/project/_/sql
- **Authentication**: https://app.supabase.com/project/_/auth/users
- **Storage**: https://app.supabase.com/project/_/storage/buckets
- **API Settings**: https://app.supabase.com/project/_/settings/api
- **Database**: https://app.supabase.com/project/_/database/tables
- **Logs**: https://app.supabase.com/project/_/logs

*(Replace `_` with your project ID)*

---

## 📚 Essential Documentation

- Main Docs: https://supabase.com/docs
- Auth Guide: https://supabase.com/docs/guides/auth
- RLS Guide: https://supabase.com/docs/guides/auth/row-level-security
- Storage Guide: https://supabase.com/docs/guides/storage
- JS Reference: https://supabase.com/docs/reference/javascript
- Python Reference: https://supabase.com/docs/reference/python

---

## ✨ Useful Admin Queries

### View user count
```sql
SELECT COUNT(*) FROM auth.users;
```

### Recent conversations
```sql
SELECT * FROM conversation_summaries
ORDER BY last_message_at DESC
LIMIT 10;
```

### Data summary
```sql
SELECT 
  'users' as entity, COUNT(*) as count FROM auth.users
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'loan_applications', COUNT(*) FROM loan_applications;
```

### Delete test data
```sql
-- Delete messages first (due to foreign keys)
DELETE FROM messages WHERE conversation_id IN (
  SELECT id FROM conversations WHERE user_id = 'test-user-id'
);

-- Then delete conversations
DELETE FROM conversations WHERE user_id = 'test-user-id';
```

---

## 🎉 Success Indicators

You're ready to integrate when you see:

✅ 6 tables in Table Editor
✅ Shield icon on every table
✅ Policies tab shows multiple policies
✅ Test user in Authentication tab
✅ Storage bucket `business-photos` exists
✅ No errors when running test queries
✅ Environment variables set

**Happy building! 🚀**

