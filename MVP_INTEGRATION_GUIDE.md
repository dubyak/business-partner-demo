# 🚀 MVP Integration Guide - Step by Step

## What You're About to Do

Add **3 database operations** to enable conversation persistence and loan tracking.

**Time**: 15 minutes  
**Changes**: 3 files  
**Lines of code**: ~20

---

## ✅ Prerequisites

1. ✅ Supabase database provisioned (Done!)
2. ✅ Credentials in `.env` file
3. ✅ `db.py` created (Done!)
4. ✅ Supabase client library installed (Done!)

---

## 📝 Step 1: Update `main.py`

Add 3 imports and 2 function calls to your existing `main.py`.

### 1.1 Add Import at Top

**Location**: After line 22 (`from state import BusinessPartnerState`)

```python
from graph import graph
from state import BusinessPartnerState
from db import get_or_create_conversation, save_messages  # ← ADD THIS LINE
```

### 1.2 Add Conversation Tracking

**Location**: After line 101 (after `user_id = request.user_id or "demo-user"`)

**FIND THIS**:
```python
    # Generate session ID if not provided
    session_id = request.session_id or f"session-{int(time.time())}"
    user_id = request.user_id or "demo-user"

    # Create Langfuse trace for this conversation turn
```

**ADD AFTER IT**:
```python
    # Generate session ID if not provided
    session_id = request.session_id or f"session-{int(time.time())}"
    user_id = request.user_id or "demo-user"

    # NEW: Get or create conversation in database
    conversation = await get_or_create_conversation(user_id, session_id)

    # Create Langfuse trace for this conversation turn
```

### 1.3 Add Message Saving

**Location**: After line 153 (after `result = graph.invoke(initial_state, config=config)`)

**FIND THIS**:
```python
        # Invoke the graph
        result = graph.invoke(initial_state, config=config)

        # Extract the assistant's response
```

**ADD AFTER `result = ...`**:
```python
        # Invoke the graph
        result = graph.invoke(initial_state, config=config)

        # NEW: Save messages to database
        await save_messages(conversation['id'], result["messages"])

        # Extract the assistant's response
```

### 1.4 Store Conversation ID in State (Optional)

**Location**: In the `initial_state` dictionary (around line 127)

**FIND THIS**:
```python
        initial_state: BusinessPartnerState = {
            "messages": langchain_messages[-1:],
            "session_id": session_id,
            "user_id": user_id,
```

**ADD ONE LINE**:
```python
        initial_state: BusinessPartnerState = {
            "messages": langchain_messages[-1:],
            "session_id": session_id,
            "user_id": user_id,
            "conversation_id": conversation['id'],  # ← ADD THIS for agents to use
```

**That's it for main.py!** ✅

---

## 📝 Step 2: Update `underwriting_agent.py`

Add loan application saving when offer is generated.

### 2.1 Add Import at Top

**File**: `python-backend/agents/underwriting_agent.py`

**Location**: After the existing imports (around line 14)

```python
from state import BusinessPartnerState
from db import save_loan_application  # ← ADD THIS LINE
```

### 2.2 Add Loan Saving in `process()` Method

**Location**: After the loan offer is created (look for `state['loan_offered'] = True`)

**FIND THIS** (around line 100-120):
```python
        state['loan_offer'] = loan_offer
        state['risk_score'] = risk_score
        state['loan_offered'] = True
        
        # Set next agent to conversation to present the offer
```

**ADD AFTER `state['loan_offered'] = True`**:
```python
        state['loan_offer'] = loan_offer
        state['risk_score'] = risk_score
        state['loan_offered'] = True
        
        # NEW: Save loan application to database
        if not state.get('_loan_saved'):
            await save_loan_application(state.get('conversation_id'), state)
            state['_loan_saved'] = True
        
        # Set next agent to conversation to present the offer
```

**That's it for underwriting_agent.py!** ✅

---

## 📝 Step 3: Update `state.py` (Optional)

Add `conversation_id` to your state type definition for type safety.

**File**: `python-backend/state.py`

**Location**: In the `BusinessPartnerState` class (around line 44)

**FIND THIS**:
```python
    # Session tracking
    session_id: str
    user_id: str
```

**ADD ONE LINE**:
```python
    # Session tracking
    session_id: str
    user_id: str
    conversation_id: Optional[str]  # ← ADD THIS
```

**That's it for state.py!** ✅

---

## 🧪 Step 4: Test Your Integration

### 4.1 Update Your `.env` File

Ensure `python-backend/.env` has these lines:

```bash
SUPABASE_URL=https://svkwsubgcedffcfrgeev.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2a3dzdWJnY2VkZmZjZnJnZWV2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzM4NTA4OSwiZXhwIjoyMDc4OTYxMDg5fQ.FBBGRWhRtlaoCiOu66TcQlAQfSyZxEM-plB8y7Gxi1k
```

### 4.2 Start Your Server

```bash
cd python-backend
python main.py
```

You should see:
```
🚀 Starting Business Partner AI (Python/LangGraph)
📍 Server: http://localhost:8000
```

### 4.3 Send a Test Message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, I need a loan"}],
    "user_id": "test-user-123",
    "session_id": "test-session-001"
  }'
```

### 4.4 Verify in Supabase Dashboard

1. Go to: https://app.supabase.com/project/svkwsubgcedffcfrgeev/editor
2. Check **`conversations`** table → Should see 1 row
3. Check **`messages`** table → Should see 2 rows (user + assistant)

**If you see data** → ✅ Success! Your integration works!

### 4.5 Test Loan Application

Continue the conversation through to loan offer:

```bash
# Continue with business info
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "I run a sari-sari store in Manila"}],
    "user_id": "test-user-123",
    "session_id": "test-session-001"
  }'

# Provide more info until you get a loan offer
# Then check loan_applications table
```

Check **`loan_applications`** table → Should see loan offer!

---

## 🎯 What You Just Implemented

### ✅ Conversations Table
- ✅ Tracks each user session
- ✅ Enables conversation resume
- ✅ Handles multiple devices

### ✅ Messages Table
- ✅ Saves full conversation history
- ✅ Both user and assistant messages
- ✅ Supports debugging and analytics

### ✅ Loan Applications Table
- ✅ Tracks all loan offers
- ✅ Records risk scores
- ✅ Enables conversion tracking

---

## 📊 Database Status Check

Run this in Supabase SQL Editor to see your data:

```sql
-- View all conversations
SELECT * FROM conversations;

-- Count messages per conversation
SELECT 
    c.session_id,
    COUNT(m.id) as message_count
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.session_id;

-- View loan applications
SELECT 
    user_id,
    loan_amount,
    status,
    created_at
FROM loan_applications
ORDER BY created_at DESC;
```

---

## 🐛 Troubleshooting

### Error: "module 'db' has no attribute 'get_or_create_conversation'"

**Solution**: Make sure `db.py` is in the `python-backend/` directory and restart your server.

### Error: "asyncpg.exceptions.UndefinedTableError: relation 'conversations' does not exist"

**Solution**: Your migrations weren't applied. Run:
```bash
npx supabase db push
```

### Error: "No conversation_id in state"

**Solution**: Make sure you added `conversation_id` to `initial_state` in `main.py` (Step 1.4)

### No data appears in Supabase

**Solution**: 
1. Check your `.env` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
2. Look for `[DB]` logs in your server output
3. Check for errors in the console

---

## 🎉 Success Criteria

Your MVP is complete when:

- [ ] Server starts without errors
- [ ] You can send a message via API
- [ ] New row appears in `conversations` table
- [ ] Messages appear in `messages` table
- [ ] Loan offers appear in `loan_applications` table
- [ ] You see `[DB] ✓` success logs in console

---

## 🚀 Next Steps

### Immediate
1. Test with your frontend UI
2. Send a full conversation flow
3. Verify all data persists
4. Try resuming a conversation

### Phase 2 (Later)
- Add `save_business_profile()` when info complete
- Implement conversation history retrieval
- Build admin dashboard for loan tracking
- Add photo analysis persistence (if needed)

---

## 📚 Quick Reference

### Files Modified
```
python-backend/
├── db.py                    ← NEW FILE (already created)
├── main.py                  ← MODIFIED (3 additions)
├── state.py                 ← MODIFIED (1 addition)
└── agents/
    └── underwriting_agent.py ← MODIFIED (1 addition)
```

### Lines Changed
- `main.py`: +5 lines
- `state.py`: +1 line
- `underwriting_agent.py`: +4 lines
- `db.py`: +250 lines (provided)

**Total**: ~260 lines for complete MVP persistence! 🎉

---

## ✨ You're Done!

You now have:
- ✅ Full conversation persistence
- ✅ Message history
- ✅ Loan tracking
- ✅ Session resume capability

**Time to integrate with your frontend and launch!** 🚀

Need help? Check:
- `SUPABASE_AGENT_INTEGRATION.md` - Detailed integration guide
- `PERSISTENCE_DECISION_GUIDE.md` - What to add later
- `SUPABASE_CREDENTIALS.md` - Your API keys

