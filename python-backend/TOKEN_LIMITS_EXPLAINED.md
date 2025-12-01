# Token Limits Explained

## Important Distinction

### `max_tokens` (Output Limit)
- **What it is**: Maximum length of the agent's **response** (output)
- **Current setting**: 4096 tokens
- **What it controls**: How long the agent can make its reply
- **NOT related to**: Conversation history length

### Context Window (Input Limit)
- **What it is**: Maximum total tokens the model can **process** (input)
- **Claude Sonnet 4**: ~200,000 tokens
- **What it includes**:
  - System prompt
  - Full conversation history
  - Current user message
  - Any context additions

## Current Configuration

### Business Partner Agent
- **Output limit (`max_tokens`)**: 4096 tokens
  - Allows responses up to ~3000 words
  - Should be sufficient for detailed explanations
  
- **Input limit (context window)**: 200,000 tokens
  - Can handle very long conversations
  - Current truncation: Last 500 messages (~50K-100K tokens)
  - Leaves plenty of room for system prompt and response

### Other Agents
- **Underwriting**: 1024 tokens output (sufficient for structured offers)
- **Servicing**: 1024 tokens output (sufficient for status updates)
- **Coaching**: 800 tokens output (sufficient for advice)

## Why We Truncate

Even though Claude has a 200K token context window, we truncate to:
1. **Performance**: Shorter contexts = faster responses
2. **Cost**: Fewer tokens = lower API costs
3. **Relevance**: Recent messages are usually more relevant
4. **Safety margin**: Leave room for system prompt, context additions, and response

## Current Truncation Strategy

- **Keep**: Last 500 messages
- **Estimated tokens**: ~50K-100K tokens (well within 200K limit)
- **Rationale**: Recent context is most relevant, older messages less so

## If You Need More History

If you find the agent forgetting important early information:

1. **Increase `max_messages`** in `onboarding_agent.py` (currently 500)
2. **Implement summarization**: Summarize older messages instead of truncating
3. **Store key facts in state**: Important info is already in state fields (business_type, location, etc.)

## Monitoring

Check logs for:
- `[BUSINESS-PARTNER] ⚠️ Conversation has X messages` - indicates truncation occurred
- Token usage in Langfuse traces
- Whether agent remembers early information

