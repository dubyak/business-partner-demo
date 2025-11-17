# Business Partner AI - Quick Reference Card

## Project at a Glance

| Aspect | Details |
|--------|---------|
| **Type** | AI-powered lending assistant chatbot (NOT a kanban board) |
| **Main Tech** | Claude Sonnet 4 + LangGraph + FastAPI/Express |
| **Database** | NONE (stateless) - Supabase needed for integration |
| **Frontend** | Single HTML file, vanilla JavaScript |
| **Architecture** | Multi-agent system (4 specialist agents) |

---

## The 4 Agents (Workflow)

```
Conversation Agent (Main)
  ├─ Takes user messages
  ├─ Routes to specialists:
  │   ├─ Vision Agent (photos) → analyzes images
  │   ├─ Underwriting Agent (loans) → generates offers
  │   └─ Coaching Agent (advice) → business tips
  └─ Integrates results back
```

---

## Tech Stack at a Glance

**Frontend:** HTML5 + Vanilla JS + CSS3
**Backend:** Express.js (Node) or FastAPI (Python)
**LLM:** Anthropic Claude Sonnet 4
**Observability:** Langfuse + LangSmith (traces only)
**Deployment:** Vercel (backend), GitHub Pages (frontend)
**Target Integration:** Supabase (for persistence)

---

## Key Files You Need to Know

| File | Purpose | Modify for Supabase? |
|------|---------|----------------------|
| `msme-assistant.html` | Frontend UI | YES |
| `backend/server.js` | API proxy | YES |
| `python-backend/main.py` | Python API | YES |
| `python-backend/graph.py` | Agent orchestration | MAYBE |
| `python-backend/state.py` | Data structures | NO |

---

## Current Data Flow

```
User Types Message
  ↓
Frontend sends to Backend
  ↓
Backend adds tracing metadata
  ↓
Anthropic Claude processes
  ↓
Response sent back to Frontend
  ↓
[LOST - only stored in browser memory]
```

---

## After Supabase Integration

```
User Types Message (with JWT token)
  ↓
Frontend sends to Backend
  ↓
Backend verifies JWT, saves to Supabase
  ↓
Backend adds tracing metadata
  ↓
Anthropic Claude processes
  ↓
Response sent back, also saved to Supabase
  ↓
Frontend displays & refreshes from database
```

---

## What Needs to be Built

### Frontend Changes
- Add login/signup UI
- Get JWT token from Supabase Auth
- Include JWT in API calls
- Add conversation history sidebar
- Load previous conversations

### Backend Changes
- Initialize Supabase client
- Verify JWT tokens
- Save messages after each API call
- Retrieve previous messages
- Expose conversation endpoints

### Database Changes
- Create 6 tables
- Enable RLS (Row Level Security)
- Create auth policies
- Set up indexes

---

## Critical Info for Integration

### Supabase Keys (Don't Mix Them Up!)

| Key | Use | Where |
|-----|-----|-------|
| `SUPABASE_URL` | Connection endpoint | Frontend & Backend |
| `SUPABASE_ANON_KEY` | Frontend queries | Frontend ONLY (public) |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend operations | Backend ONLY (secret) |

### Table Structure Needed

```
user_profiles          (stores business info)
conversations          (groups messages)
messages               (stores chat history)
business_profiles      (detailed business data)
loan_applications      (tracks offers)
photo_analyses         (vision analysis results)
```

---

## Development Checklist (Priority Order)

1. Create Supabase project
2. Create database tables + RLS policies
3. Add Supabase to backend (server.js)
4. Test backend saves messages
5. Add auth UI to frontend
6. Add JWT to API calls
7. Add conversation history UI
8. Test full flow locally
9. Deploy and test production

---

## Common Pitfalls to Avoid

DO:
- Use Service Role Key only on backend
- Verify JWT before trusting user_id
- Enable RLS on all tables
- Test with multiple user accounts
- Keep API credentials in .env files

DON'T:
- Expose Service Role Key in frontend
- Skip JWT validation
- Forget to add user_id filter to queries
- Mix up anon key with service role key
- Hard-code secrets

---

## Testing Checklist

- [ ] User can sign up
- [ ] User can log in
- [ ] Messages appear in Supabase
- [ ] Conversations persist after refresh
- [ ] User A can't see User B's data
- [ ] JWT expires and returns 401
- [ ] Loan offers save to database
- [ ] Photos are analyzed and stored

---

## File Paths (Absolute)

All files relative to:
```
/Users/wkendall/Documents/GitHub/business-partner-demo/
```

Key files:
- Frontend: `./msme-assistant.html`
- Backend: `./backend/server.js`
- Python: `./python-backend/main.py`
- Config: `./backend/.env`

---

## Helpful Links

- Supabase Docs: https://supabase.com/docs
- Supabase JavaScript SDK: https://supabase.com/docs/reference/javascript
- LangGraph: https://langchain-ai.github.io/langgraph/
- Anthropic Claude: https://docs.anthropic.com/
- Langfuse: https://langfuse.com/docs

---

## Quick Command Reference

**Start Backend (Node):**
```bash
cd backend && npm install && npm start
```

**Start Backend (Python):**
```bash
cd python-backend && python main.py
```

**Deploy Backend (Vercel):**
```bash
cd backend && vercel --prod
```

**Install Dependencies:**
```bash
# Node backend
npm install @supabase/supabase-js

# Python backend
pip install supabase
```

---

## API Endpoint Summary

### Current Endpoints
- `GET /health` - Health check
- `POST /api/chat` - Send message, get response

### Endpoints to Add
- `GET /api/conversations` - List user's conversations
- `GET /api/conversations/:id/messages` - Load conversation messages
- `POST /api/business-profile` - Save/update profile (optional)

---

## State Shape (What Gets Passed Around)

```javascript
BusinessPartnerState {
  messages: [...],              // conversation history
  session_id: "...",            // session tracking
  user_id: "...",               // from Supabase auth
  business_name: "...",         // collected from chat
  business_type: "...",         // collected from chat
  monthly_revenue: 50000,       // collected from chat
  photos: ["base64..."],        // user uploads
  photo_insights: [...],        // vision analysis results
  risk_score: 75,               // underwriting results
  loan_offer: {...},            // loan terms
  onboarding_stage: "...",      // progress tracking
  next_agent: "vision|underwriting|coaching|end"
}
```

---

## Remember

This is an **AI lending assistant**, not a kanban board. The "vibe-kanban" name refers to the Vibe project management tool used to track this feature.

Key differences from task management:
- No columns or cards
- No drag-and-drop
- Linear conversation flow
- AI-driven decision making
- Photo analysis capability

---

Generated: November 9, 2025
Repository: business-partner-demo
Branch: vk/05a9-i-want-to-integr

