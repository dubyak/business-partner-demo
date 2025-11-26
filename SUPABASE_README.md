# Supabase Setup - Automated CLI Approach

This directory contains everything you need to provision your Supabase project automatically using the CLI.

## 🚀 Quick Start (Automated)

Just run the setup script:

```bash
./setup-supabase.sh
```

This script will:
1. ✅ Install Supabase CLI (if not present)
2. ✅ Authenticate with Supabase
3. ✅ Create or link your project
4. ✅ Apply all database migrations
5. ✅ Generate TypeScript types (optional)
6. ✅ Install client libraries (optional)

**That's it!** Your Supabase project will be fully provisioned.

---

## 📁 What's Been Created

### Directory Structure
```
supabase/
├── config.toml                          # Supabase configuration
├── migrations/
│   ├── 20241117000000_initial_schema.sql    # Main database schema
│   └── 20241117000001_storage_policies.sql  # Storage bucket & policies
└── seed.sql                             # Test data (optional)
```

### What the Migrations Include

**Migration 1: Initial Schema**
- 6 database tables (user_profiles, conversations, messages, business_profiles, loan_applications, photo_analyses)
- Row Level Security (RLS) enabled on all tables
- Complete RLS policies for data isolation
- Indexes for performance
- Triggers for auto-updating timestamps
- Helper views for common queries

**Migration 2: Storage Policies**
- Storage bucket for business photos
- RLS policies for secure file uploads
- File size and type restrictions

---

## 📋 Manual Steps (If Preferred)

If you prefer to run commands manually:

```bash
# 1. Install CLI
brew install supabase/tap/supabase
# or: npm install -g supabase

# 2. Login
supabase login

# 3. Link project (if existing)
supabase link --project-ref YOUR_PROJECT_REF

# 4. Apply migrations
supabase db push

# 5. Get credentials
supabase projects api-keys --project-ref YOUR_PROJECT_REF
```

---

## 🔐 After Setup - Get Your Credentials

Run this command to get your API keys:

```bash
supabase projects api-keys --project-ref YOUR_PROJECT_REF
```

Then add to your `.env` files:

**Backend (.env)**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...
```

---

## 🧪 Testing Your Setup

### 1. Verify Tables Created
```bash
# Start local Supabase
supabase start

# Check tables in Studio
open http://localhost:54323
```

### 2. Test Schema Locally
```bash
# Reset and apply all migrations
supabase db reset

# Create a test user in Studio
# Then query the database
```

### 3. Check Remote Database
```bash
# View remote schema
supabase db pull

# Should show: "Database schema is up to date"
```

---

## 📚 Documentation Files

- **SUPABASE_CLI_SETUP.md** - Detailed CLI commands and workflow
- **SUPABASE_QUICK_REFERENCE.md** - Quick reference for common tasks
- **SUPABASE_SETUP_GUIDE.md** - Manual setup via dashboard (alternative)
- **supabase-schema.sql** - Standalone SQL file (for dashboard use)

---

## 🛠️ Development Workflow

### Working Locally
```bash
# Start local Supabase instance
supabase start

# Your local URLs:
# API: http://localhost:54321
# Studio: http://localhost:54323
# Email testing: http://localhost:54324

# Make schema changes
supabase migration new my_new_feature

# Edit: supabase/migrations/TIMESTAMP_my_new_feature.sql

# Apply locally
supabase db reset

# Push to remote when ready
supabase db push
```

### Generating Types
```bash
# Generate TypeScript types from your schema
supabase gen types typescript --linked > types/supabase.ts

# Use in your code for type safety!
```

---

## 🔍 Verifying Everything Works

Run these commands to verify your setup:

```bash
# 1. Check CLI is logged in
supabase projects list

# 2. Verify migrations are applied
supabase db diff
# Should output: "No schema differences detected"

# 3. Check tables exist
# In Studio or run SQL:
# SELECT table_name FROM information_schema.tables 
# WHERE table_schema = 'public';
```

Expected tables:
- ✅ user_profiles
- ✅ conversations  
- ✅ messages
- ✅ business_profiles
- ✅ loan_applications
- ✅ photo_analyses

---

## 🚨 Troubleshooting

### "supabase: command not found"
```bash
# Install via npm
npm install -g supabase

# Or via homebrew (Mac)
brew install supabase/tap/supabase
```

### "Not logged in"
```bash
supabase login
```

### "No linked project"
```bash
# List your projects
supabase projects list

# Link to one
supabase link --project-ref YOUR_PROJECT_REF
```

### "Migration failed"
```bash
# Check the error message
# Common issues:
# - Syntax error in SQL
# - Missing dependencies
# - Table already exists

# To rollback locally:
supabase db reset

# To fix, edit the migration file and try again
```

---

## ✨ Next Steps

After Supabase is provisioned:

1. **Install client libraries** (if not done by script):
   ```bash
   cd backend && npm install @supabase/supabase-js
   cd python-backend && pip install supabase
   ```

2. **Initialize Supabase in your code**:
   - See `SUPABASE_INTEGRATION_CHECKLIST.md` for code examples
   - Backend: Initialize with service role key
   - Frontend: Initialize with anon key

3. **Implement authentication**:
   - Add signup/login UI to frontend
   - Add JWT verification to backend
   - Test user creation and login

4. **Test database operations**:
   - Create a test user
   - Send a message
   - Verify it saves to database

---

## 📞 Need Help?

- **Supabase CLI Docs**: https://supabase.com/docs/guides/cli
- **Local Development**: https://supabase.com/docs/guides/cli/local-development
- **Migrations Guide**: https://supabase.com/docs/guides/cli/local-development#database-migrations

---

## Success Checklist

Before proceeding to code integration, ensure:

- ✅ Supabase CLI installed and logged in
- ✅ Project created or linked
- ✅ Migrations applied successfully
- ✅ All 6 tables visible in Studio
- ✅ RLS enabled on all tables (shield icons 🛡️)
- ✅ Storage bucket created
- ✅ API keys retrieved
- ✅ Environment variables configured
- ✅ Client libraries installed

**You're ready to integrate Supabase into your application! 🎉**

