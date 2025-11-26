# Business Partner AI - Python/LangGraph Multi-Agent Backend

A multi-agent implementation of the Business Partner lending assistant using **LangGraph** for orchestration and **Langfuse** for observability.

## Architecture Overview

This version uses a hybrid multi-agent approach where a main conversational agent delegates specific tasks to specialist agents:

```
┌─────────────────────────────────────────┐
│    Main Conversational Agent            │
│  - Natural dialogue                     │
│  - Fetches system prompt from Langfuse  │
│  - Routes to specialists                │
└─────────────────────────────────────────┘
          │
          ├─> 📸 Vision Agent
          │   Analyzes business photos
          │   Returns insights + coaching tips
          │
          ├─> 💰 Underwriting Agent
          │   Calculates risk score
          │   Generates loan offer
          │   (Mocked for demo)
          │
          └─> 🎓 Coaching Agent
              Provides business advice
              Post-loan growth strategies
```

## Key Features

- **LangGraph Orchestration**: Stateful multi-agent workflow with conditional routing
- **Full Langfuse Integration**: Each agent execution traced as separate span
- **Claude Vision**: Photo analysis using Claude's multimodal capabilities
- **Session Management**: Conversation state persisted with checkpointing
- **Production-Ready Structure**: Clear separation for extending to production APIs

## Project Structure

```
python-backend/
├── main.py                    # FastAPI server
├── graph.py                   # LangGraph workflow definition
├── state.py                   # Shared state schema
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
├── agents/
│   ├── conversation_agent.py  # Main orchestrator
│   ├── vision_agent.py        # Photo analysis
│   ├── underwriting_agent.py  # Loan decisions
│   └── coaching_agent.py      # Business advice
└── README.md                  # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd python-backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` (or .env already exists):

```bash
# Already configured with your Langfuse credentials
# Just add your Anthropic API key if not present
```

Required environment variables:
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_BASE_URL` - Langfuse instance URL
- `LANGFUSE_PROMPT_NAME` - Prompt name (default: business-partner-system)

### 4. Run the Server

```bash
python main.py
```

Server starts on **http://localhost:8000**

### 5. Update Frontend (Optional)

To use this Python backend with the existing HTML frontend, update the API URL in `msme-assistant.html`:

```javascript
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8080/api/chat'  // Local development
    : 'https://business-partner-demo-production.up.railway.app/api/chat';  // Production (Railway)
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
run_terminal_cmd

## API Endpoints

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "Business Partner AI (Python/LangGraph) is running",
  "version": "2.0.0"
}
```

### `POST /api/chat`
Main chat endpoint - compatible with existing frontend

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, I own a grocery store"}
  ],
  "session_id": "session-abc123",
  "user_id": "demo-user",
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024
}
```

**Response:**
```json
{
  "content": [{"type": "text", "text": "¡Hola! Welcome..."}],
  "model": "claude-sonnet-4-20250514",
  "id": "msg_session-abc123_1234567890",
  "role": "assistant",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 200
  }
}
```

## Langfuse Observability

### What Gets Tracked

Each conversation turn creates a trace in Langfuse with nested spans for agent executions:

```
Session: session-abc123
└─ Trace: business-partner-conversation (turn 1)
   ├─ Span: conversation-agent-process
   ├─ Span: conversation-agent-respond
   ├─ Span: vision-agent-process (if photos uploaded)
   │  └─ Span: vision-agent-analyze
   ├─ Span: underwriting-agent-process (if ready)
   │  ├─ Span: underwriting-agent-calculate-risk
   │  └─ Span: underwriting-agent-generate-offer
   └─ Span: coaching-agent-process (if loan accepted)
      └─ Span: coaching-agent-generate
```

### Viewing in Langfuse Dashboard

1. Go to https://us.cloud.langfuse.com (or your Langfuse instance)
2. Navigate to **Tracing** → **Sessions**
3. Find your session by ID
4. Expand traces to see agent execution details
5. View input/output for each agent
6. Analyze latency and costs per agent

### Key Metrics Tracked

- **Agent execution time**: How long each agent takes
- **Input/Output**: What data each agent received and returned
- **Routing decisions**: Which agents were called for each turn
- **Model usage**: Token counts per agent
- **Errors**: Any failures in agent execution

## Agent Details

### Conversation Agent (`agents/conversation_agent.py`)

**Purpose**: Main orchestrator and dialogue handler

**Responsibilities**:
- Fetches system prompt from Langfuse (with caching)
- Manages natural conversation flow
- Detects when to invoke specialist agents
- Integrates specialist results into responses
- Tracks onboarding progress

**Langfuse Tracing**: `@observe(name="conversation-agent-process")`

### Vision Agent (`agents/vision_agent.py`)

**Purpose**: Analyzes business photos

**Capabilities**:
- Processes images using Claude's vision API
- Extracts cleanliness and organization scores
- Assesses stock levels
- Generates specific observations
- Provides actionable coaching tips

**Input**: Base64 encoded images + business context
**Output**: Structured `PhotoInsight` objects

**Langfuse Tracing**: `@observe(name="vision-agent-analyze")`

### Underwriting Agent (`agents/underwriting_agent.py`)

**Purpose**: Generates loan offers

**Current Implementation** (Demo):
- Simple rule-based risk scoring
- Fixed loan terms for consistency
- Mocked decision logic

**Production TODO**:
```python
# Replace with API calls to your credit models
response = requests.post(
    "https://your-platform.com/api/credit/assess",
    json={"business_data": {...}, "photo_insights": {...}}
)
```

**Langfuse Tracing**: `@observe(name="underwriting-agent-process")`

### Coaching Agent (`agents/coaching_agent.py`)

**Purpose**: Provides personalized business advice

**Approach**:
- Analyzes business profile
- Incorporates photo insights
- Generates 3-4 specific, actionable tips
- Tailored to business type and goals

**Langfuse Tracing**: `@observe(name="coaching-agent-generate")`

## LangGraph Workflow

The workflow is defined in `graph.py`:

1. **Entry**: Conversation agent processes user message
2. **Routing**: Conditional edges based on `next_agent` field
   - `vision` → Analyze photos
   - `underwriting` → Generate loan offer
   - `coaching` → Provide advice
   - `end` → Return response
3. **Integration**: Specialist agents return to conversation agent
4. **Checkpointing**: State persisted for multi-turn conversations

### Visualization

You can visualize the graph structure:

```python
from graph import graph
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))
```

## Extending to Production

### 1. Underwriting Integration

Replace mocked logic in `agents/underwriting_agent.py`:

```python
@observe(name="underwriting-agent-process")
def process(self, state: BusinessPartnerState) -> Dict:
    # Call your credit model API
    risk_assessment = requests.post(
        f"{CREDIT_API_URL}/assess",
        json={
            "customer_id": state["user_id"],
            "business_data": {...},
            "photo_insights": state["photo_insights"]
        },
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()

    # Call lending platform for offer
    loan_offer = requests.post(
        f"{LENDING_API_URL}/generate-offer",
        json={
            "customer_id": state["user_id"],
            "risk_score": risk_assessment["score"]
        }
    ).json()

    return {"loan_offer": loan_offer, ...}
```

### 2. Additional Agents

Add new specialist agents by:

1. Creating agent file in `agents/`
2. Adding node to `graph.py`
3. Updating routing logic in conversation agent

Example: Document verification agent
```python
# agents/document_agent.py
class DocumentAgent:
    @observe(name="document-agent-verify")
    def process(self, state):
        # Extract data from bank statements, etc.
        pass
```

### 3. Deployment

**Option A: Traditional Hosting**
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Option B: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**Option C: Serverless**
Note: LangGraph with stateful checkpointing works best with traditional hosting.

## Comparison: Single-Agent vs Multi-Agent

| Aspect | Single-Agent (Node.js) | Multi-Agent (Python/LangGraph) |
|--------|------------------------|-------------------------------|
| **Complexity** | Simple, one LLM call | Multiple agents, orchestrated |
| **Latency** | Lower (~1-2s) | Higher (~3-5s for complex flows) |
| **Observability** | Basic trace | Detailed per-agent traces |
| **Modularity** | Monolithic prompt | Specialist agents |
| **Extensibility** | Modify prompt | Add/swap agents easily |
| **Production Path** | Embed API calls in prompt | Replace agent implementations |
| **Best For** | Demos, simple flows | Complex workflows, production systems |

## Troubleshooting

### Issue: "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Langfuse traces not appearing
- Check environment variables are set correctly
- Ensure `langfuse.flush_async()` is called
- Verify network access to Langfuse URL

### Issue: Vision agent not analyzing photos
- Confirm photos are base64 encoded
- Check image format is supported (jpeg, png, webp)
- Verify `data:image/...;base64,` prefix is handled

### Issue: Graph routing not working
- Add debug logging in `route_after_conversation()`
- Check `next_agent` field is being set correctly
- Verify state updates are returning from agents

## Development Tips

1. **Test individual agents**:
   ```python
   from agents.vision_agent import vision_agent
   result = vision_agent.analyze_photo(photo_b64, 0, {"business_type": "grocery"})
   ```

2. **Inspect graph state**:
   ```python
   config = {"configurable": {"thread_id": "test-session"}}
   result = graph.invoke(initial_state, config=config)
   print(result)  # See full state after execution
   ```

3. **Monitor Langfuse in real-time**:
   Keep Langfuse dashboard open while testing to see traces appear

4. **Use debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## License

Same as parent project

## Support

For questions about this implementation, refer to:
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Langfuse docs: https://langfuse.com/docs
- Parent project README
