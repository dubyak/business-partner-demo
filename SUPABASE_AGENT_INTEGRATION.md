# 🤖 Supabase + Agentic Workflow Integration Guide

## Overview: How Tables Map to Your LangGraph State

Your `BusinessPartnerState` flows through 4 agents, and Supabase tables persist this state at key points.

---

## 🔄 State → Database Mapping

### Your LangGraph State
```python
class BusinessPartnerState(TypedDict):
    # Session tracking
    session_id: str
    user_id: str
    
    # Business info (from conversation agent)
    business_name: Optional[str]
    business_type: Optional[str]
    location: Optional[str]
    years_operating: Optional[int]
    monthly_revenue: Optional[float]
    monthly_expenses: Optional[float]
    num_employees: Optional[int]
    loan_purpose: Optional[str]
    
    # Photos & analysis (from vision agent)
    photos: List[str]
    photo_insights: List[PhotoInsight]
    
    # Loan offer (from underwriting agent)
    risk_score: Optional[float]
    loan_offer: Optional[LoanOffer]
    
    # Messages (throughout)
    messages: List[BaseMessage]
    
    # Progress
    onboarding_stage: str
    info_complete: bool
    photos_received: bool
    loan_offered: bool
    loan_accepted: bool
```

### Supabase Tables

```
conversations → Stores session metadata
messages → Stores full conversation history
business_profiles → Stores business info from state
loan_applications → Stores underwriting results
photo_analyses → Stores vision agent results
user_profiles → Stores basic user info
```

---

## 📊 Integration Strategy: What to Persist vs Mock

### ✅ MUST PERSIST (Core Functionality)

#### 1. **Conversations** → `conversations` table
**When**: After first message in new session
**Data from state**:
- `session_id` → `session_id`
- `user_id` → `user_id`
- `started_at` → timestamp
- First message content → `title` (optional preview)

**Why**: Enables conversation history, resume sessions

#### 2. **Messages** → `messages` table
**When**: After EVERY agent response
**Data from state**:
- `messages` → save each message as row
- `role` (user/assistant)
- `content` as JSONB (supports text + images)

**Why**: Complete conversation history, analytics, debugging

#### 3. **Business Profiles** → `business_profiles` table
**When**: After conversation agent collects complete info (`info_complete = True`)
**Data from state**:
```python
{
    'user_id': state['user_id'],
    'business_name': state['business_name'],
    'business_type': state['business_type'],
    'location': state['location'],
    'years_operating': state['years_operating'],
    'monthly_revenue': state['monthly_revenue'],
    'monthly_expenses': state['monthly_expenses'],
    'num_employees': state['num_employees'],
}
```

**Why**: User profile, loan history, future underwriting

#### 4. **Loan Applications** → `loan_applications` table
**When**: After underwriting agent generates offer (`loan_offered = True`)
**Data from state**:
```python
{
    'user_id': state['user_id'],
    'conversation_id': conversation_id,
    'loan_purpose': state['loan_purpose'],
    'risk_score': state['risk_score'],
    'loan_amount': state['loan_offer']['amount'],
    'term_days': state['loan_offer']['term_days'],
    'interest_rate': state['loan_offer']['interest_rate_flat'],
    'status': 'offered',  # or 'accepted' if loan_accepted=True
    'offer_details': state['loan_offer']  # full JSONB
}
```

**Why**: Loan tracking, acceptance rate analytics, compliance

### ⚠️ OPTIONAL (Enhanced Features)

#### 5. **Photo Analyses** → `photo_analyses` table
**When**: After vision agent analyzes photos
**Data from state**:
```python
for insight in state['photo_insights']:
    {
        'user_id': state['user_id'],
        'conversation_id': conversation_id,
        'photo_data': state['photos'][insight['photo_index']],  # base64
        'cleanliness_score': insight['cleanliness_score'],
        'organization_score': insight['organization_score'],
        'stock_level': insight['stock_level'],
        'insights': insight['insights'],  # JSONB array
        'coaching_tips': insight['coaching_tips']  # JSONB array
    }
```

**Why**: Photo quality trends, coaching insights over time

**⚡ Can Mock**: For MVP, just keep in memory. Vision results are already in messages.

#### 6. **User Profiles** → `user_profiles` table
**When**: After first successful conversation
**Data from state**:
```python
{
    'user_id': state['user_id'],
    'business_name': state['business_name'],
    'business_type': state['business_type'],
    'location': state['location']
}
```

**Why**: Quick user lookup, admin dashboard

**⚡ Can Mock**: Business profiles table has this info too.

---

## 🎯 Recommended Implementation Strategy

### Phase 1: MVP (Do This First) ⭐

**Persist These:**
1. ✅ **Conversations** - Enable session tracking
2. ✅ **Messages** - Full conversation history
3. ✅ **Loan Applications** - Track loan offers/acceptances

**Mock/Skip:**
- ❌ Photo analyses (already in messages)
- ❌ User profiles (use business_profiles instead)
- ❌ Business profiles (unless you need reporting)

**Why**: Minimal work, maximum value. Users can resume conversations and you can track loan conversion.

### Phase 2: Full Persistence (Do Later)

**Add:**
4. ✅ **Business Profiles** - Enable better underwriting over time
5. ✅ **Photo Analyses** - Track photo quality trends
6. ✅ **User Profiles** - Quick lookups for admin

---

## 🔧 Implementation Points in Your Code

### 1. After Conversation Start (First Message)

**File**: `python-backend/main.py`
**Location**: After graph execution starts

```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Get or create conversation
    conversation = await get_or_create_conversation(
        user_id=request.userId,
        session_id=request.sessionId
    )
    
    # Continue with graph execution...
    result = await graph.ainvoke(state, config)
```

### 2. After Each Agent Response

**File**: `python-backend/main.py`
**Location**: After graph execution completes

```python
    # Graph execution
    result = await graph.ainvoke(state, config)
    
    # Save messages
    await save_messages(
        conversation_id=conversation.id,
        messages=result['messages']
    )
    
    return {"response": result}
```

### 3. After Info Gathering Complete

**File**: `python-backend/agents/conversation_agent.py`
**Location**: In `process()` method when `info_complete` becomes `True`

```python
def process(self, state: BusinessPartnerState) -> BusinessPartnerState:
    # ... existing logic ...
    
    # Check if info just became complete
    if state.get('info_complete') and not state.get('_business_profile_saved'):
        await save_business_profile(state)
        state['_business_profile_saved'] = True
    
    return state
```

### 4. After Loan Offer Generated

**File**: `python-backend/agents/underwriting_agent.py`
**Location**: After loan offer is calculated

```python
def process(self, state: BusinessPartnerState) -> BusinessPartnerState:
    # ... calculate loan offer ...
    
    state['loan_offer'] = loan_offer
    state['risk_score'] = risk_score
    state['loan_offered'] = True
    
    # Save loan application
    await save_loan_application(state)
    
    return state
```

### 5. After Loan Acceptance

**File**: `python-backend/agents/conversation_agent.py`
**Location**: When user accepts loan

```python
def process(self, state: BusinessPartnerState) -> BusinessPartnerState:
    # ... detect loan acceptance ...
    
    if user_accepted_loan:
        state['loan_accepted'] = True
        
        # Update loan application status
        await update_loan_status(
            conversation_id=state['conversation_id'],
            status='accepted'
        )
    
    return state
```

---

## 💾 Database Helper Functions

### Create These in a New File: `python-backend/db.py`

```python
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

async def get_or_create_conversation(user_id: str, session_id: str):
    """Get existing conversation or create new one."""
    # Try to find existing
    response = supabase.table("conversations").select("*").eq(
        "user_id", user_id
    ).eq("session_id", session_id).execute()
    
    if response.data:
        return response.data[0]
    
    # Create new
    response = supabase.table("conversations").insert({
        "user_id": user_id,
        "session_id": session_id,
        "title": "New Loan Inquiry"
    }).execute()
    
    return response.data[0]

async def save_messages(conversation_id: str, messages: list):
    """Save messages to database."""
    # Only save new messages (compare with existing count)
    existing_count = supabase.table("messages").select(
        "id", count="exact"
    ).eq("conversation_id", conversation_id).execute()
    
    new_messages = messages[existing_count.count:]
    
    for msg in new_messages:
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": {"text": msg.content}  # JSONB
        }).execute()

async def save_business_profile(state: dict):
    """Save business profile when info gathering complete."""
    supabase.table("business_profiles").insert({
        "user_id": state['user_id'],
        "business_name": state.get('business_name'),
        "business_type": state.get('business_type'),
        "location": state.get('location'),
        "years_operating": state.get('years_operating'),
        "monthly_revenue": state.get('monthly_revenue'),
        "monthly_expenses": state.get('monthly_expenses'),
        "num_employees": state.get('num_employees')
    }).execute()

async def save_loan_application(state: dict):
    """Save loan application after underwriting."""
    conversation = await get_or_create_conversation(
        state['user_id'], 
        state['session_id']
    )
    
    supabase.table("loan_applications").insert({
        "user_id": state['user_id'],
        "conversation_id": conversation['id'],
        "loan_purpose": state.get('loan_purpose'),
        "risk_score": state.get('risk_score'),
        "loan_amount": state['loan_offer']['amount'],
        "term_days": state['loan_offer']['term_days'],
        "interest_rate": state['loan_offer']['interest_rate_flat'],
        "status": "offered",
        "offer_details": state['loan_offer']  # full JSONB
    }).execute()

async def update_loan_status(conversation_id: str, status: str):
    """Update loan application status (e.g. accepted)."""
    supabase.table("loan_applications").update({
        "status": status
    }).eq("conversation_id", conversation_id).execute()

async def save_photo_analysis(state: dict):
    """Save photo analysis results (optional)."""
    conversation = await get_or_create_conversation(
        state['user_id'],
        state['session_id']
    )
    
    for i, insight in enumerate(state.get('photo_insights', [])):
        supabase.table("photo_analyses").insert({
            "user_id": state['user_id'],
            "conversation_id": conversation['id'],
            "photo_data": state['photos'][i] if i < len(state['photos']) else None,
            "cleanliness_score": insight['cleanliness_score'],
            "organization_score": insight['organization_score'],
            "stock_level": insight['stock_level'],
            "insights": insight['insights'],
            "coaching_tips": insight['coaching_tips']
        }).execute()
```

---

## 🎬 Agent Flow with Database Saves

```
User sends message
    ↓
conversation_agent (checks session)
    ↓ [IF NEW SESSION]
    ↓ → get_or_create_conversation() → conversations table ✅
    ↓
    ↓ [IF info_complete = True]
    ↓ → save_business_profile() → business_profiles table ✅
    ↓
    ↓ [IF photos received & next_agent = "vision"]
    ↓
vision_agent analyzes photos
    ↓ → (optional) save_photo_analysis() → photo_analyses table
    ↓
conversation_agent integrates results
    ↓
    ↓ [IF next_agent = "underwriting"]
    ↓
underwriting_agent calculates offer
    ↓ → save_loan_application() → loan_applications table ✅
    ↓
conversation_agent presents offer
    ↓
    ↓ [IF user accepts]
    ↓ → update_loan_status("accepted") → loan_applications table ✅
    ↓
    ↓ [IF next_agent = "coaching"]
    ↓
coaching_agent provides advice
    ↓
conversation_agent wraps up
    ↓
    ↓ [ALWAYS]
    ↓ → save_messages() → messages table ✅
    ↓
Return response to user
```

---

## 📊 What Gets Saved When

| Event | Table | Data Saved | Required? |
|-------|-------|------------|-----------|
| First message in session | `conversations` | session_id, user_id | ✅ YES |
| Every agent response | `messages` | role, content | ✅ YES |
| Info gathering complete | `business_profiles` | business details | ⚠️ LATER |
| Photos analyzed | `photo_analyses` | scores, insights | ❌ OPTIONAL |
| Loan offer generated | `loan_applications` | offer details, risk_score | ✅ YES |
| Loan accepted/rejected | `loan_applications` | status update | ✅ YES |

---

## 🎯 MVP Implementation Checklist

For minimum viable persistence:

### Phase 1: Core Persistence (Do Now)
- [ ] Create `db.py` with Supabase helper functions
- [ ] Add `get_or_create_conversation()` to main.py
- [ ] Add `save_messages()` after graph execution
- [ ] Add `save_loan_application()` in underwriting_agent
- [ ] Add `update_loan_status()` when loan accepted
- [ ] Test: Create user, send messages, verify in Supabase dashboard

### Phase 2: Enhanced Features (Do Later)
- [ ] Add `save_business_profile()` when info_complete
- [ ] Add `save_photo_analysis()` after vision agent (optional)
- [ ] Add conversation history retrieval for returning users
- [ ] Add admin dashboard queries

---

## 🔍 What to Mock vs Persist

### ✅ PERSIST (High Value)
1. **Conversations** - Resume sessions, user history
2. **Messages** - Debugging, analytics, compliance
3. **Loan Applications** - Conversion tracking, compliance

### ⚠️ PERSIST LATER (Medium Value)
4. **Business Profiles** - Better underwriting over time
5. **User Profiles** - Admin lookups

### ❌ MOCK FOR NOW (Low Value)
6. **Photo Analyses** - Already in messages, can extract later

---

## 🚀 Quick Start: Minimal Integration

**Add just 3 database calls for MVP:**

```python
# 1. At conversation start
conversation = await get_or_create_conversation(user_id, session_id)

# 2. After each turn
await save_messages(conversation.id, result['messages'])

# 3. After loan offer
await save_loan_application(state)
```

**That's it!** You now have:
- ✅ Conversation persistence
- ✅ Full message history
- ✅ Loan tracking

Everything else can be added incrementally.

---

## 📚 Next Steps

1. **Create `db.py`** with helper functions (see above)
2. **Update `main.py`** to call database functions
3. **Test** with a full conversation flow
4. **Verify** data in Supabase dashboard
5. **Add** business profile persistence when ready
6. **Build** admin dashboard for loan tracking

Your agentic workflow continues to work exactly as before - we're just persisting key state at strategic points! 🎉

