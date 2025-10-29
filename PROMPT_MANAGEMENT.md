# Langfuse Prompt Management Guide

Now that tracing is working, you can use Langfuse to manage your system prompts without redeploying code!

## ✨ Benefits

- **No Redeployment**: Update prompts in Langfuse UI, changes take effect within 1 minute
- **Version Control**: Track all prompt changes with automatic versioning
- **A/B Testing**: Test different prompt versions and compare results
- **Rollback**: Instantly revert to previous prompt versions
- **Collaboration**: Non-technical team members can edit prompts

## 🚀 Setup (One-Time)

### 1. Create Your Prompt in Langfuse

1. Go to https://us.cloud.langfuse.com
2. Click **"Prompts"** in the left sidebar
3. Click **"+ New Prompt"**
4. Fill in the details:
   - **Name**: `business-partner-system` (or custom name)
   - **Type**: Select **"Text"**
   - **Content**: Copy/paste from `system-instructions.md`
5. Click **"Create"**
6. Click **"Publish"** to activate it (drafts won't be fetched)

### 2. Configure Vercel (Optional)

If you used a custom prompt name (not `business-partner-system`), add this to Vercel:

- Go to: https://vercel.com/dubyak/business-partner-demo/settings/environment-variables
- Add new variable:
  - **Key**: `LANGFUSE_PROMPT_NAME`
  - **Value**: `your-custom-prompt-name`
- Redeploy

### 3. Deploy

The code is already pushed. Just wait for Vercel deployment to complete!

## 📝 How It Works

### Automatic Fallback
The system will:
1. **First**: Try to fetch prompt from Langfuse (cached for 1 minute)
2. **Fallback**: Use `system-instructions.md` if Langfuse is unavailable
3. **Track**: Log which source was used in trace metadata

### Caching
- Prompts are cached for **60 seconds** to reduce API calls
- Updates in Langfuse take effect within 1 minute
- Adjust cache TTL in `server.js` if needed:
  ```javascript
  ttl: 60000 // Change to 30000 for 30 seconds, etc.
  ```

## 🎯 Using Prompt Management

### View Current Prompt
1. Go to Langfuse → **Prompts**
2. Click on your prompt name
3. See current version and content

### Update the Prompt
1. Click **"Create new version"**
2. Edit the content
3. Save and **"Publish"**
4. Within 1 minute, all new conversations use the new version!

### Version Comparison
1. In Langfuse Prompts, click on your prompt
2. See all versions with timestamps
3. Click any version to see the diff
4. Click **"Promote to production"** to switch versions instantly

### A/B Testing
1. Create two versions of your prompt
2. Publish both
3. Use Langfuse analytics to compare:
   - Response quality
   - Token usage
   - User satisfaction
   - Conversation length

### Rollback
If a new prompt version isn't working well:
1. Go to Langfuse → Prompts → Your prompt
2. Click on a previous version
3. Click **"Promote to production"**
4. Done! Old version is now active

## 🔍 Verify It's Working

### Check Logs
After deployment, check Vercel logs for:
```
✓ System prompt fetched from Langfuse: business-partner-system (v1)
```

Or if using fallback:
```
ℹ Using fallback prompt (Langfuse prompt not found or error)
✓ System instructions fallback loaded from file
```

### Check Traces
In Langfuse traces, look at the metadata:
- `promptSource: "langfuse"` = Using Langfuse
- `promptSource: "file"` = Using fallback file

## 🛠️ Troubleshooting

### Prompt Not Found Error
**Symptom**: Logs show "Using fallback prompt"

**Fixes**:
1. Verify prompt name matches (default: `business-partner-system`)
2. Ensure prompt is **Published** (not Draft)
3. Check API keys have correct permissions
4. Verify you're in the right Langfuse project

### Changes Not Appearing
**Symptom**: Updated prompt but app still uses old version

**Reasons**:
- Cache hasn't expired yet (wait 1 minute)
- Frontend has old SYSTEM_PROMPT hardcoded (check `msme-assistant.html`)

**Fix**:
- Wait 60 seconds for cache to expire
- Or restart the server to clear cache immediately

### Using File Instead of Langfuse
If you want to temporarily use the file:
1. Comment out or delete the prompt in Langfuse
2. The system will auto-fallback to `system-instructions.md`

## 📊 Best Practices

### Development Workflow
1. **Draft** → Edit and test in Langfuse UI
2. **Preview** → Publish a draft and test with specific session IDs
3. **Production** → Promote to production version
4. **Monitor** → Watch traces for quality/performance

### Prompt Versioning Strategy
- **v1.0**: Initial launch version
- **v1.1**: Minor tweaks (tone, formatting)
- **v2.0**: Major changes (new features, restructure)

### Testing New Prompts
1. Create new version in Langfuse
2. Test with a few conversations
3. Check traces for quality
4. Compare metrics vs. previous version
5. Promote or rollback based on results

### Collaboration Tips
- Use **descriptive commit messages** when creating versions
- Add **labels** to prompts for easy filtering
- Create **separate prompts** for different use cases:
  - `business-partner-onboarding`
  - `business-partner-coaching`
  - `business-partner-support`

## 🔗 Resources

- **Langfuse Prompt Docs**: https://langfuse.com/docs/prompts
- **Your Prompts**: https://us.cloud.langfuse.com/prompts
- **Your Traces**: https://us.cloud.langfuse.com/traces

## 💡 Next Steps

Once this is working, you can:
1. **Experiment** with different prompt styles
2. **A/B test** multiple versions
3. **Create specialized prompts** for different conversation stages
4. **Use prompt variables** for dynamic content (advanced)

---

**Ready to try it?** Create your first prompt in Langfuse and watch it work! 🚀

