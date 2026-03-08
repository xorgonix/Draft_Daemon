#!/bin/bash
# Test script for Ollama LLM
# Run this to verify Ollama is responding correctly

echo "============================================================"
echo "Testing Ollama LLM Connection"
echo "============================================================"
echo ""

echo "Sending request to Ollama..."
echo "Model: gemma3-12b-32k:latest"
echo ""

curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3-12b-32k:latest",
    "messages": [
      {"role": "user", "content": "Say hello in 5 words or less"}
    ],
    "stream": false
  }'

echo ""
echo ""
echo "============================================================"
echo "Test complete"
echo "============================================================"
