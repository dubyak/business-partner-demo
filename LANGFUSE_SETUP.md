# Langfuse Setup Guide

This guide will help you set up Langfuse for observability and tracking of your Business Partner AI demo.

## What is Langfuse?

Langfuse is an open-source LLM engineering platform that provides:
- 📊 **Trace Logging**: See every conversation, message, and API call
- 💰 **Cost Tracking**: Monitor token usage and API costs
- 📈 **Analytics**: Analyze user behavior, conversion rates, and drop-offs
- 🔄 **Prompt Management**: Version and test different prompts
- ⚡ **Performance Monitoring**: Track latency and response times

## Quick Start

### 1. Get Your Langfuse Credentials

1. Go to [Langfuse Cloud](https://cloud.langfuse.com) (or your self-hosted instance)
2. Create an account or log in
3. Create a new project (e.g., "Business Partner Demo")
4. Navigate to **Settings** → **API Keys**
5. Copy your:
   - `Public Key`
   - `Secret Key`

### 2. Add Environment Variables

Add these to your `.env` file in the `/backend` directory:

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Langfuse Configuration
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**For Vercel Deployment:**
1. Go to your Vercel project settings
2. Navigate to **Environment Variables**
3. Add the same three Langfuse variables
4. Redeploy

### 3. Install Dependencies

```bash
cd backend
npm install
```

### 4. Test Locally

```bash
npm run dev
```

You should see:
```
✓ System instructions loaded from file
Server running on port 3000
```

### 5. Use the Application

Open `msme-assistant.html` in your browser and start chatting. Every conversation will automatically be logged to Langfuse!

## What Gets Tracked?

### Traces
Each conversation creates a **trace** with:
- **Session ID**: Unique per user session (persists in localStorage)
- **User ID**: Currently set to "demo-user"
- **Metadata**: Model name, timestamp

### Generations
Each API call logs:
- **Input**: The full conversation history + images
- **Output**: The assistant's response
- **Usage**: Input/output token counts
- **Metadata**: Latency, stop reason, message count
- **Cost**: Automatically calculated based on model pricing

### System Prompts
The system prompt is tracked via:
- Loaded from `system-instructions.md`
- Length logged in metadata
- Can version and compare different prompts

## Using the Langfuse Dashboard

### View Traces
1. Go to **Traces** in Langfuse
2. You'll see all conversation sessions
3. Click any trace to see the full conversation flow

### Analyze Conversations
- **Sessions**: Group traces by session ID to see full user journeys
- **Timeline**: See conversation flow and timing
- **Tokens**: Monitor usage and costs per conversation

### Key Metrics to Watch

**Onboarding Analysis:**
- How many messages until loan offer?
- Where do users drop off?
- Which photos generate best engagement?

**Cost Management:**
- Average cost per conversation
- Token usage trends
- Model performance vs. cost

**Performance:**
- Average response latency
- API error rates
- Success rate

## Advanced Features

### Prompt Versioning

Instead of using the local `system-instructions.md`, you can manage prompts in Langfuse:

```javascript
// In server.js, replace file loading with:
const prompt = await langfuse.getPrompt('business-partner-v1');
const systemPrompt = prompt.prompt;
```

Benefits:
- A/B test different prompts
- Roll back to previous versions
- Track which prompt version each conversation used

### Custom Metadata

Add business-specific tracking:

```javascript
trace.update({
    metadata: {
        loanOffered: true,
        loanAmount: 5000,
        loanAccepted: false,
        businessType: 'retail'
    }
});
```

### User Feedback

Capture thumbs up/down:

```javascript
trace.score({
    name: 'user-satisfaction',
    value: 1, // 1 for positive, 0 for negative
    comment: 'Helpful advice!'
});
```

## Debugging

### No Traces Appearing?

1. **Check API keys**: Verify they're correct in `.env` or Vercel
2. **Check console**: Look for Langfuse errors in backend logs
3. **Flush timing**: Traces are flushed asynchronously; wait a few seconds
4. **Network issues**: Ensure backend can reach Langfuse Cloud

### Test Langfuse Connection

Add this endpoint to `server.js` for testing:

```javascript
app.get('/test-langfuse', async (req, res) => {
    try {
        const trace = langfuse.trace({
            name: 'test-trace',
            metadata: { test: true }
        });
        await langfuse.flushAsync();
        res.json({ success: true, message: 'Langfuse connected!' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

## Production Best Practices

### 1. Environment-Specific Projects
Create separate Langfuse projects for:
- **Development**: Testing and iteration
- **Production**: Real user data

### 2. User Privacy
- Don't log PII in metadata
- Use hashed/anonymized user IDs
- Consider compliance requirements (GDPR, etc.)

### 3. Cost Management
- Set up alerts for high token usage
- Monitor daily/weekly spend
- Optimize prompts based on cost data

### 4. Sampling (Optional)
For high-volume production, sample traces:

```javascript
// Only log 10% of conversations
if (Math.random() < 0.1) {
    trace = langfuse.trace({ ... });
}
```

## Support & Resources

- **Langfuse Docs**: https://langfuse.com/docs
- **API Reference**: https://langfuse.com/docs/sdk/typescript
- **Discord**: Join the Langfuse community
- **GitHub**: https://github.com/langfuse/langfuse

## Next Steps

Now that Langfuse is set up:

1. ✅ Run a few test conversations
2. ✅ Explore the Langfuse dashboard
3. ✅ Identify key metrics for your use case
4. ✅ Experiment with prompt variations
5. ✅ Use insights to improve the agent

**Happy tracking!** 🚀

