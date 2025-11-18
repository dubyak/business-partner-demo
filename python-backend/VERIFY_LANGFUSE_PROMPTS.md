# ✅ Verify Langfuse Prompt Integration

After manually adding prompts in the Langfuse portal, verify everything is configured correctly.

## 📋 Prompt Names to Verify

Make sure these prompt names **exactly** match in Langfuse:

| Agent | Required Prompt Name | Optional Env Var |
|-------|---------------------|------------------|
| **Vision** | `vision-agent-system` | `LANGFUSE_VISION_PROMPT_NAME` |
| **Coaching** | `coaching-agent-system` | `LANGFUSE_COACHING_PROMPT_NAME` |
| **Conversation** | `business-partner-system` | `LANGFUSE_PROMPT_NAME` |

## ✅ Checklist

### 1. Prompt Names Match
- [ ] `vision-agent-system` exists in Langfuse
- [ ] `coaching-agent-system` exists in Langfuse
- [ ] `business-partner-system` exists in Langfuse (if using Conversation Agent)

### 2. Prompts Are Published
**Critical**: Drafts won't be fetched! Each prompt must be **Published**.

- [ ] `vision-agent-system` is **Published** (not Draft)
- [ ] `coaching-agent-system` is **Published** (not Draft)
- [ ] `business-partner-system` is **Published** (not Draft)

### 3. Railway Environment Variables (Optional)
If you're using custom prompt names, set these in Railway:

- [ ] `LANGFUSE_VISION_PROMPT_NAME` (if different from default)
- [ ] `LANGFUSE_COACHING_PROMPT_NAME` (if different from default)
- [ ] `LANGFUSE_PROMPT_NAME` (if different from default)

### 4. Required Langfuse Credentials
Make sure these are set in Railway:

- [ ] `LANGFUSE_SECRET_KEY`
- [ ] `LANGFUSE_PUBLIC_KEY`
- [ ] `LANGFUSE_BASE_URL` (optional, defaults to https://cloud.langfuse.com)

## 🧪 Testing After Deployment

After deploying, check Railway logs for:

### Success Messages:
```
[LANGFUSE-VISION] ✓ Prompt fetched successfully (v1)
[LANGFUSE-COACHING] ✓ Prompt fetched successfully (v1)
```

### Error Messages (if prompts not found):
```
[LANGFUSE-VISION] ✗ Error fetching prompt: ...
[LANGFUSE-VISION] → Using fallback prompt
```

## 🔍 Quick Verification Steps

1. **Check Langfuse Dashboard**:
   - Go to https://cloud.langfuse.com → Prompts
   - Verify all 3 prompts exist and show "Published" status

2. **Check Railway Logs**:
   - Deploy code
   - Look for `✓ Prompt fetched successfully` messages
   - If you see fallback messages, check prompt names and publish status

3. **Test Agents**:
   - Upload a photo (triggers Vision Agent)
   - Ask for coaching advice (triggers Coaching Agent)
   - Check Langfuse traces to see which prompts were used

## 🚨 Common Issues

### Prompts Not Being Fetched
**Problem**: Logs show "Using fallback prompt"

**Solutions**:
1. Verify prompt is **Published** (not Draft)
2. Check prompt name matches exactly (case-sensitive)
3. Verify Langfuse credentials are set correctly in Railway
4. Check you're in the correct Langfuse project

### Wrong Prompt Version
**Problem**: Changes to prompts not appearing

**Solutions**:
1. Prompts are cached for 60 seconds - wait 1 minute
2. Create new version and **Publish** it
3. Or redeploy to clear cache

## ✅ Success Indicators

When everything works:
- ✅ Railway logs show successful prompt fetches
- ✅ Langfuse traces show prompts being used
- ✅ Agents use updated prompts without code changes
- ✅ You can update prompts in Langfuse UI and see changes within 1 minute

---

**If all prompts are created and published, you're all set!** 🎉

Just deploy your code and the agents will automatically fetch prompts from Langfuse.

