@echo off
REM Test script for Ollama LLM using OpenAI-compatible endpoint
REM This is the same endpoint the app uses

echo ============================================================
echo Testing Ollama LLM (OpenAI-compatible endpoint)
echo ============================================================
echo.

echo Sending request to Ollama...
echo Endpoint: http://localhost:11434/v1/chat/completions
echo Model: gemma3-12b-32k:latest
echo.

curl -X POST http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer ollama" -d "{\"model\": \"gemma3-12b-32k:latest\", \"messages\": [{\"role\": \"system\", \"content\": \"You are a helpful assistant.\"}, {\"role\": \"user\", \"content\": \"Say hello in 5 words or less\"}]}"

echo.
echo.
echo ============================================================
echo Test complete
echo ============================================================
