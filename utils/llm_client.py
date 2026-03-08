"""
LLMClient for communicating with Ollama server.

This client wraps the OpenAI API to communicate with Ollama.
Ollama provides an OpenAI-compatible API endpoint.
"""

import os
from openai import AsyncOpenAI


class LLMClient:
    """
    Async LLM client for Ollama server.
    
    Usage:
        client = LLMClient()
        response = await client.chat_async([{"role": "user", "content": "Hello"}])
    """
    
    def __init__(self, base_url=None, api_key=None, model=None):
        """
        Initialize the LLM client.
        
        Args:
            base_url: Ollama base URL (default: http://localhost:11434/v1)
            api_key: API key (default: 'ollama' - Ollama doesn't require auth)
            model: Model name (default: gemma3-12b-32k:latest)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "ollama")
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3-12b-32k:latest")
        
        # Initialize async OpenAI client configured for Ollama
        self._client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    async def chat_async(self, messages):
        """
        Send a chat completion request to Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            str: The assistant's response text
        """
        # DEBUG: Log incoming request
        print("\n" + "="*60)
        print("[LLMClient] Sending request to Ollama:")
        print(f"  Base URL: {self.base_url}")
        print(f"  Model: {self.model}")
        print(f"  API Key: {self.api_key}")
        print(f"  Messages count: {len(messages)}")
        for i, msg in enumerate(messages):
            preview = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            print(f"    [{i}] {msg.get('role')}: {preview}")
        print("="*60)
        
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            response_text = response.choices[0].message.content
            
            # DEBUG: Log outgoing response
            print("\n" + "="*60)
            print("[LLMClient] Received response from Ollama:")
            preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
            print(f"  Response preview: {preview}")
            print(f"  Response length: {len(response_text)} chars")
            print("="*60 + "\n")
            
            return response_text
            
        except Exception as e:
            print("\n" + "="*60)
            print(f"[LLMClient] ERROR: {type(e).__name__}: {str(e)}")
            print("="*60 + "\n")
            raise
    
    def chat(self, messages):
        """
        Synchronous wrapper for chat_async.
        Uses run_io_bound for NiceGUI compatibility.
        """
        import asyncio
        from nicegui import run
        
        # Use NiceGUI's IO-bound runner for async LLM calls
        return run.io_bound(lambda: asyncio.run(self.chat_async(messages)))


# Test function
async def _test_client():
    """Test the LLM client with a simple prompt."""
    client = LLMClient()
    
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    try:
        response = await client.chat_async(test_messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_test_client())
