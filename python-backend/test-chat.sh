#!/bin/bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hi! I am interested in getting a loan for my small business."
      }
    ],
    "session_id": "test-session-1",
    "user_id": "test-user"
  }'
