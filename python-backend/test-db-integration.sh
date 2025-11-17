#!/bin/bash

# =====================================================
# Database Integration Test Script
# =====================================================
# Tests the MVP Supabase integration
# =====================================================

set -e  # Exit on error

echo "🧪 Testing Supabase Integration"
echo "========================================"
echo ""

API_URL="http://localhost:8000"
USER_ID="test-user-$(date +%s)"
SESSION_ID="test-session-$(date +%s)"

# Check if server is running
echo "📡 Checking if server is running..."
if ! curl -s "$API_URL/health" > /dev/null; then
    echo "❌ Server not running. Start it with: python main.py"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Test 1: Send first message
echo "📨 Test 1: Sending first message..."
RESPONSE1=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"Hello, I need a loan\"}],
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

if echo "$RESPONSE1" | grep -q "content"; then
    echo "✅ First message sent successfully"
    echo "Response preview: $(echo $RESPONSE1 | head -c 100)..."
else
    echo "❌ First message failed"
    echo "Response: $RESPONSE1"
    exit 1
fi
echo ""

# Test 2: Send follow-up message
echo "📨 Test 2: Sending follow-up message..."
RESPONSE2=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"I run a sari-sari store in Manila, been operating for 5 years\"}],
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

if echo "$RESPONSE2" | grep -q "content"; then
    echo "✅ Follow-up message sent successfully"
else
    echo "❌ Follow-up message failed"
    exit 1
fi
echo ""

# Test 3: Provide financial info
echo "📨 Test 3: Providing financial information..."
RESPONSE3=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"messages\": [{\"role\": \"user\", \"content\": \"We make about 50,000 pesos per month and spend about 35,000 pesos on expenses\"}],
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\"
  }")

if echo "$RESPONSE3" | grep -q "content"; then
    echo "✅ Financial info sent successfully"
else
    echo "❌ Financial info failed"
    exit 1
fi
echo ""

echo "========================================"
echo "✅ All API tests passed!"
echo ""
echo "🔍 Now check your Supabase dashboard:"
echo "   https://app.supabase.com/project/svkwsubgcedffcfrgeev/editor"
echo ""
echo "You should see:"
echo "   ✅ 1 conversation in 'conversations' table"
echo "   ✅ 6 messages in 'messages' table (3 user + 3 assistant)"
echo "   ✅ (Possibly) 1 loan in 'loan_applications' table"
echo ""
echo "Session details:"
echo "   User ID: $USER_ID"
echo "   Session ID: $SESSION_ID"
echo ""
echo "🎉 Integration test complete!"

