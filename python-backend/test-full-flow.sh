#!/bin/bash

# Test the full multi-agent conversation flow
SESSION_ID="test-flow-$(date +%s)"
BASE_URL="http://localhost:8000/api/chat"

echo "🧪 Testing Multi-Agent Flow with Session: $SESSION_ID"
echo "================================================"

# Step 1: Initial greeting
echo -e "\n📝 Step 1: Initial greeting..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"Hi! I want to apply for a business loan.\"
    }],
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test-user\"
  }" | python3 -m json.tool | grep -A2 '"text"'

sleep 2

# Step 2: Provide business info
echo -e "\n📝 Step 2: Providing business information..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"I run a small grocery store called Maria's Shop in Nairobi. I've been operating for 3 years.\"
    }],
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test-user\"
  }" | python3 -m json.tool | grep -A2 '"text"'

sleep 2

# Step 3: Provide financial info
echo -e "\n📝 Step 3: Providing financial information..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"My monthly revenue is about 45,000 pesos and expenses are around 25,000 pesos. I want to use the loan to buy more inventory.\"
    }],
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"test-user\"
  }" | python3 -m json.tool | grep -A2 '"text"'

echo -e "\n\n✅ Test complete! Check Langfuse for traces: https://us.cloud.langfuse.com"
echo "Session ID: $SESSION_ID"
