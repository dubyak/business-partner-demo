# LangSmith Integration Setup Guide

This guide explains how to set up and use LangSmith observability for the Business Partner Demo application.

## What is LangSmith?

LangSmith is a platform for debugging, testing, and monitoring LLM applications. It provides:

- **Tracing**: Track all LLM calls with full input/output visibility
- **Monitoring**: Real-time performance metrics and cost tracking
- **Debugging**: Detailed error logging and stack traces
- **Analytics**: Usage patterns and model performance insights
- **Testing**: Compare model outputs and track improvements

## Why Use LangSmith?

This application already includes Langfuse for observability. LangSmith is integrated as an additional tool that provides:

1. **Complementary Features**: Different analytics and debugging capabilities
2. **Team Collaboration**: Built-in sharing and commenting features
3. **LangChain Ecosystem**: Native integration if you're using LangChain
4. **Dual Observability**: Run both tools in parallel for comprehensive monitoring

## Prerequisites

1. A LangSmith account (sign up at [smith.langchain.com](https://smith.langchain.com))
2. Node.js backend running (see [QUICK_START.md](QUICK_START.md))
3. LangSmith SDK installed (already included via `npm install`)

## Step 1: Get Your LangSmith API Key

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign in or create an account
3. Navigate to **Settings** → **API Keys**
4. Click **Create API Key**
5. Copy your API key (starts with `lsv2_...` or `ls__...`)
6. Save it securely - you won't be able to see it again

## Step 2: Create a LangSmith Project

1. In the LangSmith dashboard, click **Projects**
2. Click **New Project**
3. Name it `business-partner-demo` (or choose your own name)
4. Save the project name for configuration

## Step 3: Configure Environment Variables

### Local Development

1. Navigate to the `backend` directory
2. Open or create the `.env` file
3. Add your LangSmith credentials:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=lsv2_your_api_key_here
LANGSMITH_PROJECT=business-partner-demo
# LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # Optional: defaults to LangSmith cloud
```

### Production Deployment

#### Vercel

```bash
vercel env add LANGSMITH_API_KEY
# Paste your API key when prompted

vercel env add LANGSMITH_PROJECT
# Enter: business-partner-demo
```

#### Railway

```bash
railway variables --set LANGSMITH_API_KEY=lsv2_your_api_key_here
railway variables --set LANGSMITH_PROJECT=business-partner-demo
```

Or use the Railway dashboard:
1. Go to your project
2. Click **Variables**
3. Add `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT`

#### Other Platforms

Add the environment variables through your platform's dashboard or CLI:
- `LANGSMITH_API_KEY`: Your LangSmith API key
- `LANGSMITH_PROJECT`: Your project name
- `LANGSMITH_ENDPOINT` (optional): Custom endpoint URL

## Step 4: Start the Server

```bash
cd backend
npm start
```

You should see initialization logs:

```
[LANGSMITH] Initializing with config:
  - API Key: Set (starts with lsv2_...)
  - Project: business-partner-demo
  - Endpoint: https://api.smith.langchain.com
```

If you don't see these logs, LangSmith is not configured (which is fine - it's optional).

## Step 5: Verify Tracing

1. Open the frontend (`msme-assistant.html`) in your browser
2. Send a message to the assistant
3. Go to [smith.langchain.com](https://smith.langchain.com)
4. Navigate to your project (`business-partner-demo`)
5. You should see traces appearing in the dashboard

Each trace includes:
- **Inputs**: User messages and system prompt
- **Outputs**: Assistant responses
- **Metadata**: Model, tokens, latency, session ID, user ID
- **Tags**: `anthropic`, `claude`, `business-partner`

## Features and Capabilities

### 1. Conversation Tracking

Every chat request creates a LangSmith "run" that tracks:
- Full conversation history
- System prompt used
- Model parameters
- Session and user IDs

### 2. Performance Monitoring

LangSmith automatically tracks:
- **Latency**: Response time in milliseconds
- **Token Usage**: Input, output, and total tokens
- **Cost**: Estimated cost per request (if configured)
- **Throughput**: Requests per minute/hour

### 3. Error Tracking

Errors are automatically logged with:
- Error message
- Stack trace
- Request context
- Timestamp

### 4. Metadata and Tags

Each run includes:
- **Tags**: `anthropic`, `claude`, `business-partner`
- **Metadata**: Model version, token counts, session info
- **Custom Fields**: System prompt length, message count

### 5. Search and Filtering

In the LangSmith dashboard, you can:
- Filter by tags, status, or date range
- Search by user ID or session ID
- Sort by latency, cost, or tokens
- View aggregate statistics

## Troubleshooting

### LangSmith Not Logging

**Check 1: API Key**
```bash
# Verify your .env file contains:
LANGSMITH_API_KEY=lsv2_...
```

**Check 2: Server Logs**
Look for initialization message:
```
[LANGSMITH] Initializing with config:
```

If you see:
```
[LANGSMITH] Not initialized - LANGSMITH_API_KEY not set
```

Then the API key is missing or invalid.

**Check 3: Network Connectivity**
Ensure your server can reach `https://api.smith.langchain.com`

**Check 4: API Key Permissions**
Verify your API key has write permissions in the LangSmith dashboard.

### Partial Traces

If traces appear incomplete:
- Check for errors in server logs (look for `[LANGSMITH] Error`)
- Verify the API call completed successfully
- Check LangSmith dashboard for error details

### Duplicate Traces

This app runs both Langfuse and LangSmith in parallel. You'll see:
- Traces in Langfuse dashboard
- Separate traces in LangSmith dashboard

This is intentional and provides dual observability.

## Disabling LangSmith

LangSmith is optional. To disable it:

1. Remove or comment out these environment variables:
   ```bash
   # LANGSMITH_API_KEY=...
   # LANGSMITH_PROJECT=...
   ```

2. Restart the server

The server will log:
```
[LANGSMITH] Not initialized - LANGSMITH_API_KEY not set
```

The application will continue working normally with only Langfuse tracing.

## Best Practices

### 1. Use Separate Projects for Environments

Create different projects for different environments:
- `business-partner-dev` (development)
- `business-partner-staging` (staging)
- `business-partner-prod` (production)

### 2. Tag Your Runs

The integration automatically adds tags. You can extend this in `server.js`:

```javascript
tags: ['anthropic', 'claude', 'business-partner', 'v1', 'your-custom-tag']
```

### 3. Monitor Costs

LangSmith can help track LLM costs:
1. Configure pricing in LangSmith dashboard
2. View cost analytics per session/user
3. Set up alerts for high usage

### 4. Review Traces Regularly

- Check for slow responses (high latency)
- Look for error patterns
- Analyze token usage trends
- Optimize prompts based on data

### 5. Use Sessions for User Tracking

The integration automatically uses session IDs from the frontend. This allows you to:
- Track individual user journeys
- Analyze conversation patterns
- Debug user-specific issues

## Advanced Configuration

### Custom Endpoint (Self-Hosted)

If you're running a self-hosted LangSmith instance:

```bash
LANGSMITH_ENDPOINT=https://your-langsmith-instance.com
```

### Additional Metadata

To add more metadata, edit `server.js`:

```javascript
extra: {
    metadata: {
        // ... existing metadata
        environment: process.env.NODE_ENV,
        version: '1.0.0',
        custom_field: 'value'
    }
}
```

### Run Types

LangSmith supports different run types:
- `chain`: Multi-step operations (default)
- `llm`: Direct LLM calls
- `tool`: Tool/function calls
- `retriever`: RAG/retrieval operations

To change the run type, edit the `createRun` call in `server.js`.

## Comparison: LangSmith vs Langfuse

Both tools are integrated in this application. Here's how they compare:

| Feature | LangSmith | Langfuse |
|---------|-----------|----------|
| **Tracing** | ✅ Excellent | ✅ Excellent |
| **Open Source** | ❌ No | ✅ Yes |
| **Self-Hosting** | ⚠️ Enterprise only | ✅ Free |
| **LangChain Integration** | ✅ Native | ⚠️ Via SDK |
| **Prompt Management** | ✅ Yes | ✅ Yes |
| **Analytics** | ✅ Advanced | ✅ Good |
| **Cost Tracking** | ✅ Built-in | ✅ Built-in |
| **Team Features** | ✅ Excellent | ✅ Good |

**Recommendation**: Use both! They complement each other and provide redundancy.

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Python/JS SDK](https://github.com/langchain-ai/langsmith-sdk)
- [LangChain Documentation](https://python.langchain.com/docs/langsmith/)
- [Example Projects](https://docs.smith.langchain.com/old/cookbook)

## Support

### LangSmith Issues

For LangSmith-specific problems:
- [LangSmith Discord](https://discord.gg/langchain)
- [GitHub Issues](https://github.com/langchain-ai/langsmith-sdk/issues)
- [Documentation](https://docs.smith.langchain.com/)

### Application Issues

For issues with this integration:
- Check the [GitHub repository](https://github.com/dubyak/business-partner-demo)
- Review server logs for `[LANGSMITH]` messages
- Compare with Langfuse behavior (should be similar)

## Next Steps

After setting up LangSmith:

1. **Explore the Dashboard**: Familiarize yourself with traces and analytics
2. **Set Up Alerts**: Configure notifications for errors or high latency
3. **Optimize Prompts**: Use trace data to improve system instructions
4. **Monitor Costs**: Track token usage and optimize for cost
5. **Compare with Langfuse**: See how the two tools complement each other

## Conclusion

LangSmith is now integrated and running in parallel with Langfuse. Both tools provide valuable observability for your AI application. The integration is designed to be non-intrusive - if LangSmith fails or isn't configured, the application continues working normally with Langfuse.

Happy monitoring!
