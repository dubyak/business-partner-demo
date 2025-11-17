# Supabase Integration Checklist

## Overview
This checklist guides you through integrating Supabase into the Business Partner AI Demo for user authentication, conversation persistence, and data management.

---

## Phase 1: Setup & Configuration

- [ ] **Create Supabase Project**
  - [ ] Go to https://supabase.com
  - [ ] Create new project
  - [ ] Note: Supabase URL (e.g., `https://xxxxx.supabase.co`)
  - [ ] Note: Supabase Anon Key (public key)
  - [ ] Note: Supabase Service Role Key (private - for backend only)

- [ ] **Setup Environment Variables**
  - [ ] Add to `backend/.env`:
    ```
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
    ```
  - [ ] Keep Supabase Anon Key in frontend code (it's public)

- [ ] **Install Dependencies**
  - [ ] Frontend: No npm needed (use Supabase CDN or import)
  - [ ] Backend: `npm install @supabase/supabase-js`
  - [ ] Python: `pip install supabase`

---

## Phase 2: Database Setup

- [ ] **Create Tables in Supabase**
  - [ ] Go to SQL Editor in Supabase Dashboard
  - [ ] Run the SQL schema from CODEBASE_EXPLORATION.md
  - [ ] Verify tables created:
    - [ ] `user_profiles`
    - [ ] `conversations`
    - [ ] `messages`
    - [ ] `business_profiles`
    - [ ] `loan_applications`
    - [ ] `photo_analyses`

- [ ] **Enable Row Level Security (RLS)**
  - [ ] Enable RLS on all tables
  - [ ] Create policy: Users can only see their own data
  - [ ] Policies to create:
    ```sql
    -- Allow users to read own data
    CREATE POLICY "Users can read own data" 
      ON user_profiles 
      FOR SELECT 
      USING (auth.uid() = user_id);
    
    -- Similar for conversations, messages, etc.
    ```

- [ ] **Configure Auth Settings**
  - [ ] Go to Authentication → Providers
  - [ ] Enable Email/Password (or Google, GitHub, etc.)
  - [ ] Configure redirect URLs for your frontend
  - [ ] Set email templates if needed

---

## Phase 3: Frontend Implementation

### File: `/msme-assistant.html`

- [ ] **Add Supabase SDK**
  - [ ] Import at top: `<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>`
  - [ ] Or: `npm install @supabase/supabase-js` if using build tool

- [ ] **Initialize Supabase Client**
  ```javascript
  const SUPABASE_URL = 'https://xxxxx.supabase.co';
  const SUPABASE_ANON_KEY = 'your-anon-key';
  const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  ```

- [ ] **Add Authentication UI**
  - [ ] Create login/signup form before chat
  - [ ] Replace form HTML in initial state
  - [ ] Functions to add:
    - [ ] `signUp(email, password)` - Supabase auth.signUp()
    - [ ] `signIn(email, password)` - Supabase auth.signInWithPassword()
    - [ ] `signOut()` - Supabase auth.signOut()
    - [ ] `checkAuth()` - Check if user is logged in on page load

- [ ] **Update Session Management**
  - [ ] Replace: `sessionId = localStorage.getItem('sessionId')`
  - [ ] With: Get user ID from Supabase: `const user = await supabase.auth.getUser()`
  - [ ] Still keep sessionId for conversation grouping
  - [ ] Get JWT token: `const session = await supabase.auth.getSession()`

- [ ] **Update sendMessage() Function**
  - [ ] Get current user JWT: `const { data, error } = await supabase.auth.getSession()`
  - [ ] Add JWT to API call headers:
    ```javascript
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.session.access_token}`
    }
    ```

- [ ] **Add Conversation History Display**
  - [ ] Add button/sidebar to show previous conversations
  - [ ] Query Supabase: `conversations` table where `user_id = current_user`
  - [ ] Click to load: Fetch messages for that conversation
  - [ ] Populate chat UI with loaded messages

- [ ] **Show User Profile**
  - [ ] Display logged-in user email/name
  - [ ] Show account settings link
  - [ ] Add logout button

---

## Phase 4: Backend Implementation

### File: `/backend/server.js`

- [ ] **Install Supabase Client**
  ```bash
  npm install @supabase/supabase-js
  ```

- [ ] **Initialize Supabase in server.js**
  ```javascript
  const { createClient } = require('@supabase/supabase-js');
  const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY
  );
  ```

- [ ] **Add JWT Verification Middleware**
  - [ ] Extract JWT from request headers
  - [ ] Verify with Supabase
  - [ ] Attach user_id to request object
  - [ ] Return 401 if invalid

- [ ] **Update `/api/chat` Endpoint**
  - [ ] Extract JWT from header
  - [ ] Verify and get user_id
  - [ ] After Anthropic API call:
    - [ ] Get or create conversation record
    - [ ] Save user message to `messages` table
    - [ ] Save assistant response to `messages` table
  - [ ] Return same response format (no changes to frontend)

- [ ] **Add Conversation Retrieval**
  - [ ] New endpoint: `GET /api/conversations`
    - [ ] Return list of user's conversations
    - [ ] Filter by user_id from JWT
  - [ ] New endpoint: `GET /api/conversations/:id/messages`
    - [ ] Return messages for that conversation

- [ ] **Update Business Profile on Chat**
  - [ ] When user provides business info in chat
  - [ ] Save to `business_profiles` table
  - [ ] Extract from conversation state

- [ ] **Save Loan Offer When Generated**
  - [ ] After underwriting agent responds
  - [ ] Save to `loan_applications` table
  - [ ] Include loan terms, risk score, user_id

---

## Phase 5: Python Backend (if using)

### File: `/python-backend/main.py`

- [ ] **Install Supabase Client**
  ```bash
  pip install supabase
  ```

- [ ] **Initialize Supabase Client**
  ```python
  from supabase import create_client
  supabase = create_client(
      os.getenv("SUPABASE_URL"),
      os.getenv("SUPABASE_SERVICE_ROLE_KEY")
  )
  ```

- [ ] **Add JWT Verification**
  - [ ] Use FastAPI dependency to verify JWT
  - [ ] Extract user_id from token
  - [ ] Pass to agent functions

- [ ] **Persist State to Database**
  - [ ] After each agent processes state
  - [ ] Save updated `business_profiles`
  - [ ] Save `photo_analyses` results
  - [ ] Save `loan_applications` offers

- [ ] **Update Response Handler**
  - [ ] Save messages to `messages` table
  - [ ] Create conversation if needed
  - [ ] Return same format (compatible with frontend)

---

## Phase 6: Testing

- [ ] **Local Testing**
  - [ ] Start backend: `npm start` (or `python main.py`)
  - [ ] Open frontend in browser
  - [ ] Create new account with email
  - [ ] Have a conversation
  - [ ] Check Supabase dashboard → Logs
  - [ ] Verify data in tables

- [ ] **Test Conversation History**
  - [ ] Refresh page → should stay logged in
  - [ ] Click conversation history
  - [ ] Load previous conversation
  - [ ] Verify all messages load correctly

- [ ] **Test Data Persistence**
  - [ ] Check `messages` table has entries
  - [ ] Check `conversations` table has entry
  - [ ] Check `business_profiles` updated
  - [ ] Check `loan_applications` created

- [ ] **Test Authorization**
  - [ ] Create another user account
  - [ ] Verify can't see first user's data
  - [ ] Verify RLS policies working

- [ ] **Test JWT Handling**
  - [ ] Verify expired token returns 401
  - [ ] Verify missing token returns 401
  - [ ] Verify valid token works

---

## Phase 7: Deployment

- [ ] **Update Environment Variables**
  - [ ] Vercel (if deploying backend there):
    - [ ] Add `SUPABASE_URL`
    - [ ] Add `SUPABASE_SERVICE_ROLE_KEY`
  - [ ] Frontend (if GitHub Pages):
    - [ ] `SUPABASE_URL` and `SUPABASE_ANON_KEY` can be in code (public)

- [ ] **Deploy Backend**
  - [ ] `vercel --prod` (if using Vercel)
  - [ ] Or deploy to your chosen platform

- [ ] **Deploy Frontend**
  - [ ] Update API_URL to production backend
  - [ ] Push to GitHub
  - [ ] GitHub Pages auto-deploys

- [ ] **Test Production**
  - [ ] Create new account
  - [ ] Test full flow
  - [ ] Verify data in production Supabase

---

## Phase 8: Monitoring & Optimization

- [ ] **Set Up Supabase Monitoring**
  - [ ] Check database performance
  - [ ] Monitor authentication events
  - [ ] Set up backups (automatic in paid plans)

- [ ] **Optimize Queries**
  - [ ] Add indexes on frequently filtered columns
  - [ ] Consider pagination for large result sets
  - [ ] Use connection pooling if high traffic

- [ ] **Security Review**
  - [ ] Verify RLS policies are correct
  - [ ] Never expose Service Role Key in frontend
  - [ ] Verify JWT validation on all endpoints
  - [ ] Check CORS settings

---

## Common Issues & Solutions

### Issue: CORS Error on Frontend
**Solution:** Ensure backend adds correct CORS headers, Supabase URL is correct

### Issue: 401 Unauthorized on API Calls
**Solution:** Check JWT is being extracted correctly, verify token not expired

### Issue: Data appears in Supabase but not in app
**Solution:** Check RLS policies aren't blocking queries, verify user_id filter correct

### Issue: User sees another user's data
**Solution:** RLS policy not working, check policy is enabled on table

### Issue: Conversations not saving
**Solution:** Check Supabase insert permissions, verify user_id is correct, check no SQL errors

---

## Next Steps After Integration

1. **Add Real-time Updates** (Optional)
   - Use Supabase Realtime for live message updates
   - Multiple users in same conversation?

2. **Add File Storage**
   - Upload photos to Supabase Storage instead of base64
   - Reference in `photo_analyses` table

3. **Add User Profiles**
   - Allow users to edit business name, location
   - Add profile picture upload

4. **Add Notifications**
   - Email when loan offer created
   - SMS status updates

5. **Analytics**
   - Combine Langfuse traces with Supabase data
   - Track user journeys through database

---

## Files to Modify Summary

```
Frontend:
  - msme-assistant.html (largest changes)

Backend:
  - backend/server.js (add Supabase client, JWT verification, database saves)
  - backend/package.json (add @supabase/supabase-js)
  - backend/.env (add SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

Python Backend (if applicable):
  - python-backend/main.py (add Supabase client)
  - python-backend/requirements.txt (add supabase)
  - python-backend/.env (add Supabase vars)

New Files:
  - Database schema SQL
```

---

## Success Criteria

- [ ] Users can sign up/login
- [ ] Conversation history persists across sessions
- [ ] Messages are saved to database
- [ ] User can see previous conversations
- [ ] Loan offers are tracked in database
- [ ] Business profile data is stored
- [ ] Unauthorized users can't see other users' data
- [ ] All RLS policies working correctly
- [ ] Production deployment works end-to-end

