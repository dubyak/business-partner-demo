# Langfuse Tracing Improvements

This document summarizes the comprehensive improvements made to Langfuse tracing throughout the application.

## Overview

The tracing system has been upgraded to provide:
- **Production-ready configuration** with sampling, environment detection, and graceful shutdown
- **Comprehensive coverage** of all user journeys, agent handoffs, LLM calls, and database operations
- **Automatic LLM tracing** via LangChain callbacks
- **Structured metadata** for filtering and analytics in Langfuse UI

## Key Changes

### 1. Centralized Langfuse Client (`langfuse_config.py`)

**New Features:**
- Singleton pattern for Langfuse client (prevents multiple instances)
- Environment-based configuration (development/production)
- Sampling support via `LANGFUSE_SAMPLE_RATE` environment variable
- Non-blocking auth check in background thread
- Automatic shutdown/flush on application termination
- Helper functions for standardized trace metadata

**Usage:**
```python
from langfuse_config import get_langfuse_client, get_trace_metadata, should_sample

# Get client (singleton)
langfuse = get_langfuse_client()

# Check if request should be sampled
if should_sample():
    # Create trace...

# Get standardized metadata
metadata = get_trace_metadata(
    user_id="user123",
    session_id="session456",
    flow_name="customer-journey"
)
```

### 2. Root Trace Wrapping (`main.py`)

**Changes:**
- Main chat endpoint wrapped with `@observe` decorator
- Root trace created for each customer journey
- Comprehensive metadata including:
  - User ID, session ID
  - Flow name, environment, version
  - Model information
  - State information

**Example:**
```python
@app.post("/api/chat")
@observe(name="business-partner-chat-request")
async def chat(request: ChatRequest):
    # Root trace automatically created
    # All nested operations will be children of this trace
```

### 3. Graph Node Tracing (`graph.py`)

**Changes:**
- All graph nodes wrapped with `@observe` decorators
- Routing function traced for agent handoff decisions
- Input/output metadata for each node:
  - Business state information
  - Phase transitions
  - Agent routing decisions

**Traced Nodes:**
- `business_partner_node` - Onboarding agent
- `underwriting_node` - Underwriting agent
- `servicing_node` - Servicing agent
- `coaching_node` - Coaching agent
- `route_after_business_partner` - Routing logic

### 4. Agent Updates

**All agents updated to:**
- Use centralized Langfuse client (no duplicate instances)
- Include Langfuse callbacks for automatic LLM tracing
- Add `@observe` decorators to key methods
- Attach input/output metadata to spans

**Agents Updated:**
- `OnboardingAgent` - Main conversation agent
- `UnderwritingAgent` - Loan offer generation
- `ServicingAgent` - Disbursement and repayments
- `CoachingAgent` - Business advice

**Example LLM Integration:**
```python
from langfuse_callbacks import LangfuseCallbackHandler

callbacks = []
if self.langfuse:
    callbacks.append(LangfuseCallbackHandler(trace_name="onboarding-llm-call"))

self.llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    callbacks=callbacks if callbacks else None,
)
```

### 5. Database Operation Tracing (`db.py`)

**Changes:**
- `@observe` decorators on all database functions
- Input/output metadata for:
  - Conversation creation/retrieval
  - Message saving
  - Loan application operations

**Traced Functions:**
- `get_or_create_conversation`
- `save_messages`
- (Other DB functions can be added as needed)

### 6. Automatic LLM Tracing (`langfuse_callbacks.py`)

**New Module:**
- `LangfuseCallbackHandler` - LangChain callback handler
- Automatically captures:
  - LLM prompts and responses
  - Token usage
  - Latency
  - Errors

**Integration:**
- Works seamlessly with `@observe` decorators
- Creates nested spans for LLM calls
- No manual tracing code needed in agent methods

### 7. Shutdown and Flush Logic

**Implementation:**
- `shutdown_langfuse()` function registered with `atexit`
- FastAPI shutdown event handler
- Manual flush available via `flush_langfuse()`

**Benefits:**
- Ensures all traces are sent before application termination
- Prevents data loss on server restarts
- Graceful handling of buffered spans

## Environment Variables

### Required
```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # Optional, defaults to cloud
```

### Optional
```bash
# Sampling (0.0 to 1.0, default: 1.0 = 100%)
LANGFUSE_SAMPLE_RATE=0.2  # Sample 20% of traces

# Environment detection
ENVIRONMENT=production  # or development, staging, etc.

# Enable/disable tracing
LANGFUSE_ENABLED=true  # Set to false to disable tracing
```

## Trace Hierarchy

The trace hierarchy follows the user journey:

```
business-partner-chat-request (root trace)
├── get-or-create-conversation
├── load-existing-state
├── invoke-graph
│   ├── graph-node-business-partner
│   │   ├── onboarding-get-system-prompt
│   │   ├── onboarding-llm-call (automatic)
│   │   └── business-partner-agent-generate-response
│   ├── graph-routing
│   ├── graph-node-underwriting (if routed)
│   │   └── underwriting-agent-calculate-risk
│   ├── graph-node-servicing (if routed)
│   │   └── servicing-agent-process-disbursement
│   └── graph-node-coaching (if routed)
│       └── coaching-agent-generate
└── save-messages
```

## Metadata and Tags

### Standard Metadata
- `environment` - Development/production/staging
- `version` - Application version
- `user_id` - User identifier
- `session_id` - Session identifier
- `flow_name` - Customer journey name
- `model` - LLM model used
- `architecture` - System architecture (langgraph-multi-agent)

### Tags
- `customer-journey` - Root trace tag
- `langgraph` - LangGraph workflow tag
- `multi-agent` - Multi-agent system tag

## Benefits

1. **Complete Visibility**: Every step of the customer journey is traced
2. **Performance Monitoring**: Latency tracking at every level
3. **Error Tracking**: Comprehensive error logging with context
4. **Cost Analysis**: Token usage automatically captured
5. **Debugging**: Rich metadata for troubleshooting
6. **Analytics**: Filterable traces for business insights
7. **Production Ready**: Sampling and graceful shutdown prevent issues

## Migration Notes

### Breaking Changes
- None - all changes are backward compatible

### Required Updates
1. Update `requirements.txt` to use `langfuse>=3.0.0`
2. Ensure environment variables are set
3. No code changes needed in existing agent logic

### Optional Enhancements
- Add more database operations to tracing
- Add custom metadata for specific business metrics
- Implement trace filtering based on user tier or request source

## Testing

To verify tracing is working:

1. **Check Logs**: Look for `[LANGFUSE]` log messages
2. **Langfuse UI**: Verify traces appear in your Langfuse project
3. **Trace Structure**: Confirm nested spans are created correctly
4. **Metadata**: Verify all expected metadata is present

## References

- [Langfuse Python SDK Setup](https://langfuse.com/docs/sdk/python/setup)
- [Langfuse Decorators](https://langfuse.com/docs/observability/sdk/python/decorators)
- [Langfuse Advanced Usage](https://langfuse.com/docs/observability/sdk/python/advanced-usage)
- [LangGraph Integration](https://langfuse.com/guides/cookbook/integration_langgraph)

