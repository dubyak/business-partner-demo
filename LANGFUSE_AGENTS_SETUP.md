# Langfuse System Prompts Setup Guide

This guide helps you set up all system prompts for the 4 specialist agents in Langfuse.

## 📋 Agent Overview

| Agent | Prompt Name | Environment Variable | Purpose |
|-------|-------------|---------------------|---------|
| **Onboarding** | `onboarding-agent-system` | `LANGFUSE_ONBOARDING_PROMPT_NAME` | Handles conversation, info gathering, and photo analysis |
| **Underwriting** | `underwriting-agent-system` | `LANGFUSE_UNDERWRITING_PROMPT_NAME` | Generates loan offers based on risk assessment |
| **Servicing** | `servicing-agent-system` | `LANGFUSE_SERVICING_PROMPT_NAME` | Handles disbursement, repayments, and recovery |
| **Coaching** | `coaching-agent-system` | `LANGFUSE_COACHING_PROMPT_NAME` | Provides business advice |

## 🚀 Quick Setup (Automated)

### Option 1: Run Setup Script (Recommended)

The easiest way is to use the automated setup script:

```bash
cd python-backend
python3 setup-langfuse-prompts.py
```

This will:
- ✅ Create all 4 prompts in Langfuse
- ✅ Use default prompt names (or environment variables if set)
- ✅ Publish prompts automatically
- ✅ Verify all prompts are ready

**Prerequisites:**
- Set `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` in your environment
- Or create a `.env` file in `python-backend/` with these values

### Option 2: Manual Setup via Langfuse UI

If you prefer to set up prompts manually:

1. Go to https://cloud.langfuse.com
2. Click **"Prompts"** in the left sidebar
3. For each agent, click **"+ New Prompt"** and create:

#### Onboarding Agent Prompt
- **Name**: `onboarding-agent-system`
- **Type**: Text
- **Content**: See prompt content below

#### Underwriting Agent Prompt
- **Name**: `underwriting-agent-system`
- **Type**: Text
- **Content**: See prompt content below

#### Servicing Agent Prompt
- **Name**: `servicing-agent-system`
- **Type**: Text
- **Content**: See prompt content below

#### Coaching Agent Prompt
- **Name**: `coaching-agent-system`
- **Type**: Text
- **Content**: See prompt content below

4. **Important**: Click **"Publish"** for each prompt (drafts won't be fetched)

## 📝 Prompt Contents

### Onboarding Agent Prompt

```
You are a friendly business partner agent for a lending platform. Help customers with loan onboarding.

FLOW:
1. Greet and welcome (acknowledge if they've completed previous loan cycles)
2. Gather business info: type, location, years operating, number of employees
3. Request photos of their business (storefront, inventory, workspace) for analysis
4. Collect financial info: monthly revenue, monthly expenses, loan purpose
5. Once all info is collected, route to underwriting for loan offer

Keep responses SHORT (2-3 paragraphs max). Ask 1-2 questions at a time. Be conversational and encouraging.

When analyzing photos, provide:
- Cleanliness score (0-10)
- Organization score (0-10)
- Stock level (low/medium/high)
- 2-3 specific observations
- 1-2 actionable coaching tips
```

### Underwriting Agent Prompt

```
You are a loan underwriting specialist for a lending platform.

Your responsibilities:
- Evaluate business information and photo insights
- Calculate risk scores based on business profile
- Generate appropriate loan offers with terms

Risk factors to consider:
- Years operating (more experience = lower risk)
- Monthly revenue (higher revenue = lower risk)
- Photo insights (cleanliness and organization scores)
- Loan purpose (some purposes are lower risk)

For this demo, generate standard offers:
- Amount: 5,000 pesos
- Term: 45 days
- Installments: 3
- Interest rate: 11% flat

In production, you would adjust terms based on risk score and integrate with credit models.
```

### Servicing Agent Prompt

```
You are a helpful loan servicing agent for a lending platform. You assist customers with:
- Disbursement after loan acceptance
- Making repayments (via bank account or in-person)
- Understanding payment schedules
- Managing recovery conversations and payment plans

Be:
- Clear and empathetic
- Helpful in explaining processes
- Supportive during difficult financial situations
- Professional and solution-oriented

Keep responses concise (2-3 paragraphs max).

For disbursement: Help customer complete disbursement process. Confirm bank account details and explain timeline.

For repayments: Help customer make a repayment. Explain payment options (existing bank, new account, in-person).

For recovery: Help customer navigate financial difficulties. Work towards solutions like promise to pay, payment plans, or restructuring. Be compassionate but clear about obligations.
```

### Coaching Agent Prompt

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

## ✅ Verification

After setting up prompts, verify they're working:

1. **Check Langfuse UI**: Go to Prompts → See all 4 prompts listed
2. **Check Logs**: When agents run, you should see:
   ```
   [LANGFUSE-ONBOARDING] ✓ Prompt fetched successfully (v1)
   [LANGFUSE-UNDERWRITING] ✓ Prompt fetched successfully (v1)
   [LANGFUSE-SERVICING] ✓ Prompt fetched successfully (v1)
   [LANGFUSE-COACHING] ✓ Prompt fetched successfully (v1)
   ```

3. **Test Fallback**: If Langfuse is unavailable, agents will use fallback prompts (you'll see "→ Using fallback prompt" in logs)

## 🔧 Customization

### Using Custom Prompt Names

If you want to use different prompt names, set environment variables:

```bash
export LANGFUSE_ONBOARDING_PROMPT_NAME=my-onboarding-prompt
export LANGFUSE_UNDERWRITING_PROMPT_NAME=my-underwriting-prompt
export LANGFUSE_SERVICING_PROMPT_NAME=my-servicing-prompt
export LANGFUSE_COACHING_PROMPT_NAME=my-coaching-prompt
```

### Updating Prompts

1. Go to Langfuse → Prompts
2. Click on the prompt you want to update
3. Click "Edit" or create a new version
4. Make your changes
5. Click "Publish" to activate

Changes take effect within 60 seconds (prompt cache TTL).

## 📊 Prompt Caching

All agents cache prompts for **60 seconds** to reduce API calls:
- Updates in Langfuse take effect within 1 minute
- If Langfuse is unavailable, agents use fallback prompts
- Cache TTL can be adjusted in each agent's `__init__` method

## 🎯 Best Practices

1. **Version Control**: Langfuse automatically versions prompts - use this to track changes
2. **A/B Testing**: Create multiple versions and test which performs better
3. **Rollback**: If a prompt change causes issues, instantly revert to previous version
4. **Collaboration**: Non-technical team members can edit prompts without code changes

## 🆘 Troubleshooting

### Prompts Not Found
- **Check**: Prompt name matches exactly (case-sensitive)
- **Check**: Prompt is published (not draft)
- **Check**: Environment variables are set correctly

### Fallback Prompts Being Used
- **Check**: Langfuse credentials are correct
- **Check**: Network connectivity to Langfuse
- **Check**: Langfuse base URL is correct

### Changes Not Taking Effect
- **Wait**: Up to 60 seconds for cache to expire
- **Check**: Prompt is published (not draft)
- **Check**: Correct prompt name is being used

## 📚 Related Documentation

- `python-backend/setup-langfuse-prompts.py` - Automated setup script
- `python-backend/agents/onboarding_agent.py` - Onboarding agent implementation
- `python-backend/agents/underwriting_agent.py` - Underwriting agent implementation
- `python-backend/agents/servicing_agent.py` - Servicing agent implementation
- `python-backend/agents/coaching_agent.py` - Coaching agent implementation

