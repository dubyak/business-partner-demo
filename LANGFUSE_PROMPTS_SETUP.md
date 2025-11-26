# Langfuse Prompts Setup Guide

All three agents now fetch their system prompts from Langfuse! This allows you to update prompts without redeploying code.

## 📋 Prompt Names

| Agent | Prompt Name (Default) | Environment Variable |
|-------|----------------------|---------------------|
| **Conversation** | `business-partner-system` | `LANGFUSE_PROMPT_NAME` |
| **Vision** | `vision-agent-system` | `LANGFUSE_VISION_PROMPT_NAME` |
| **Coaching** | `coaching-agent-system` | `LANGFUSE_COACHING_PROMPT_NAME` |

## 🚀 Setup Steps

### 1. Create Vision Agent Prompt

1. Go to https://cloud.langfuse.com
2. Click **"Prompts"** in left sidebar
3. Click **"+ New Prompt"**
4. Fill in:
   - **Name**: `vision-agent-system`
   - **Type**: Text
   - **Content**: Copy from below or use your custom version
5. Click **"Create"**
6. Click **"Publish"** (important - drafts won't be fetched)

**Default Content**:
```
You are a business consultant analyzing photos of small businesses.

Your task: Analyze the photo and provide:
1. Cleanliness score (0-10): How clean and well-maintained is the space?
2. Organization score (0-10): How organized is the inventory/workspace?
3. Stock level: "low", "medium", or "high" - how well-stocked does it appear?
4. 2-3 specific observations about what you see
5. 1-2 actionable coaching tips to improve the business

Be specific, practical, and encouraging. Focus on visual signals that indicate business health.
```

### 2. Create Coaching Agent Prompt

1. Same steps as above
2. **Name**: `coaching-agent-system`
3. Click **"Publish"**

**Default Content**:
```
You are an experienced business coach helping small business owners grow.

Your task: Provide 3-4 specific, actionable coaching tips based on:
- Business type and operations
- Visual insights from their photos
- Their stated goals for the loan

Be:
- Specific and actionable (not generic advice)
- Encouraging and supportive
- Focused on practical next steps
- Relevant to their specific business type

Format your response as a friendly paragraph with 3-4 concrete suggestions.
```

### 3. Verify Conversation Prompt

1. Check if `business-partner-system` already exists
2. If not, create it with content from `system-instructions.md`
3. Ensure it's **Published** (not Draft)

## ✅ Verification

After deployment, check Railway logs for:

```
[LANGFUSE-VISION] ✓ Prompt fetched successfully (v1)
[LANGFUSE-COACHING] ✓ Prompt fetched successfully (v1)
[LANGFUSE] ✓ Prompt fetched successfully (v1)  # Conversation agent
```

Or if using fallback:
```
[LANGFUSE-VISION] → Using fallback prompt
[LANGFUSE-COACHING] → Using fallback prompt
```

## 🔄 How It Works

1. **First Request**: Agent fetches prompt from Langfuse
2. **Cached**: Prompt cached for 60 seconds
3. **Updates**: Changes in Langfuse take effect within 1 minute
4. **Fallback**: If Langfuse unavailable, uses hardcoded fallback

## 📝 Editing Prompts

### Update Any Prompt
1. Go to Langfuse → Prompts
2. Click on prompt name
3. Click **"Create new version"**
4. Edit content
5. Click **"Publish"**
6. Changes live within 1 minute!

### Version Management
- View all versions with timestamps
- Compare versions side-by-side
- Rollback by promoting old version to production
- A/B test different prompt versions

## 🔧 Custom Prompt Names

If you want custom names, set these in Railway Variables:

```bash
LANGFUSE_PROMPT_NAME=your-conversation-prompt-name
LANGFUSE_VISION_PROMPT_NAME=your-vision-prompt-name
LANGFUSE_COACHING_PROMPT_NAME=your-coaching-prompt-name
```

## 🎯 Benefits

✅ **No Redeployment**: Update prompts without code changes  
✅ **Version Control**: Track all prompt changes  
✅ **A/B Testing**: Test different versions  
✅ **Fast Updates**: Changes live within 1 minute  
✅ **Safe Fallback**: Works even if Langfuse is down  

## 🆘 Troubleshooting

### Prompt Not Found
- Verify prompt name matches exactly
- Ensure prompt is **Published** (not Draft)
- Check API keys have correct permissions

### Changes Not Appearing
- Wait 60 seconds for cache to expire
- Or restart Railway deployment

### Using Fallback
- Check Railway logs for error messages
- Verify Langfuse credentials are set
- Test Langfuse connection manually

---

**All agents now use Langfuse for prompt management!** 🎉


