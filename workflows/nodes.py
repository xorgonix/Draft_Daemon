"""
Pocket Flow Node definitions for the Spec Interviewer chat loop.
Using AsyncNode for NiceGUI compatibility.
"""

from pocketflow import AsyncNode
from utils.parser import extract_markdown_spec, extract_project_name, is_spec_complete


class ChatInputNode(AsyncNode):
    """
    Gets user input from the shared store (set by NiceGUI UI).
    """
    
    async def prep_async(self, shared):
        # Initialize messages if first run
        if "messages" not in shared:
            shared["messages"] = []
        if "chat_history" not in shared:
            shared["chat_history"] = []
        
        # Get user input from shared (set by UI)
        user_input = shared.get("user_input", "")
        return user_input
    
    async def exec_async(self, user_input):
        # Just pass through - user_input came from prep
        return user_input
    
    async def post_async(self, shared, prep_res, exec_res):
        user_input = exec_res
        
        if not user_input:
            return None  # End if no input
        
        # Store user input
        shared["messages"].append({"role": "user", "content": user_input})
        shared["chat_history"].append({"role": "user", "content": user_input})
        
        # Move to LLM evaluation
        return "evaluate"


class LLMEvaluateNode(AsyncNode):
    """
    Calls the LLM to evaluate the conversation and generate response.
    """
    
    def __init__(self, llm_client=None):
        super().__init__()
        self._llm_client = llm_client
    
    def set_llm_client(self, client):
        self._llm_client = client
    
    async def prep_async(self, shared):
        # Get chat history for LLM
        chat_history = shared.get("chat_history", [])
        system_prompt = shared.get("system_prompt", "")
        
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        return messages
    
    async def exec_async(self, messages):
        # Call LLM with the conversation history
        if self._llm_client is None:
            from utils.llm_client import LLMClient
            self._llm_client = LLMClient(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="gemma3-12b-32k:latest"
            )
        
        # Async call - won't block NiceGUI
        response = await self._llm_client.chat_async(messages)
        return response
    
    async def post_async(self, shared, prep_res, exec_res):
        llm_response = exec_res

        if not llm_response:
            llm_response = "Error: LLM did not return a response."

        # Store response
        shared["llm_response"] = llm_response
        shared["messages"].append({"role": "assistant", "content": llm_response})
        shared["chat_history"].append({"role": "assistant", "content": llm_response})

        # Check if spec is complete
        spec_complete = is_spec_complete(llm_response)
        shared["spec_complete"] = spec_complete

        if spec_complete:
            return "generate"  # Proceed to GenerateSpecNode
        else:
            return "wait"  # Terminate flow gracefully, yield to NiceGUI


class GenerateSpecNode(AsyncNode):
    """
    Extracts and saves the final specification.
    """
    
    async def prep_async(self, shared):
        llm_response = shared.get("llm_response", "")
        return llm_response
    
    async def exec_async(self, llm_response):
        # Parse the spec
        spec_content = extract_markdown_spec(llm_response)
        project_name = extract_project_name(spec_content)
        return (spec_content, project_name)
    
    async def post_async(self, shared, prep_res, exec_res):
        spec_content, project_name = exec_res
        
        # Write to file system
        from utils.file_system_writer import FileSystemWriter
        writer = FileSystemWriter()
        project_dir, spec_path = writer.write_spec(spec_content, project_name)
        
        # Store results
        shared["final_spec"] = spec_content
        shared["project_name"] = project_name
        shared["spec_file_path"] = str(spec_path)
        
        print(f"\n[GenerateSpec] Spec saved to: {spec_path}")
        
        return "done"
