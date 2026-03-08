"""
KickoffChat NiceGUI component for the Spec Interviewer.

This component provides the chat interface for the project initialization phase,
where the "Editorial Architect" LLM interviews the user to gather spec requirements.
"""

import asyncio
from nicegui import ui
from workflows.flow import create_spec_interviewer_flow
from workflows.nodes import ChatInputNode


class KickoffChat(ui.element):
    """
    A chat interface component for the Spec Interviewer flow.
    
    Integrates with Pocket Flow to orchestrate the conversation between
    the user and the "Editorial Architect" LLM.
    """
    
    def __init__(self, llm_client=None, system_prompt=None):
        super().__init__()
        
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Pocket Flow shared store
        self.shared = {
            "system_prompt": self.system_prompt,
            "chat_history": [],
            "user_input": None,
            "llm_response": None,
            "spec_complete": False,
            "final_spec": None,
            "project_name": None
        }
        
        # Flow state
        self._flow = None
        self._user_input_queue = asyncio.Queue()
        self._flow_running = False
        self._current_response = None
        
        self._build_ui()
    
    def _default_system_prompt(self) -> str:
        """Return the default 'Editorial Architect' system prompt."""
        return """You are the Editorial Architect, an expert in software specification and requirements gathering.

Your role is to interview users about their project ideas and help them create a well-structured OpenSpec specification document.

Guidelines:
1. Ask clarifying questions to understand the project scope, goals, and requirements
2. Help the user think through edge cases, constraints, and success criteria
3. Guide them toward a clear, actionable specification
4. When you have enough information, output the complete specification in markdown format

Always be supportive, ask one question at a time, and ensure the user feels heard."""
    
    def _build_ui(self):
        """Build the chat interface UI."""
        with self:
            # Chat container
            with ui.column().classes('w-full max-w-3xl mx-auto gap-4'):
                # Header
                ui.label('Spec Interviewer').classes('text-h5 text-primary')
                ui.label('Chat with the Editorial Architect to define your project spec').classes('text-subtitle2 text-gray-600')
                
                # Chat messages area (scrollable)
                self._messages_container = ui.column().classes('w-full h-96 overflow-y-auto border rounded-lg p-4 bg-gray-50')
                
                # Input area
                with ui.row().classes('w-full gap-2'):
                    self._input_field = ui.input(
                        placeholder='Describe your project idea...',
                        on_change=lambda e: self._enable_send()
                    ).classes('flex-grow')
                    
                    self._send_button = ui.button(
                        'Send',
                        on_click=self._handle_send,
                        icon='send'
                    ).props('round dense').disable()
                
                # Status indicator
                self._status_label = ui.label('').classes('text-sm text-gray-500')
    
    def _enable_send(self):
        """Enable send button when input has content."""
        if self._input_field.value and self._input_field.value.strip():
            self._send_button.disable(False)
        else:
            self._send_button.disable()
    
    def _add_message(self, content: str, role: str):
        """Add a message bubble to the chat."""
        with self._messages_container:
            is_user = role == "user"
            alignment = "items-end" if is_user else "items-start"
            bg_color = "bg-blue-600 text-white" if is_user else "bg-white text-gray-800 border"
            
            with ui.row().classes(f'w-full {alignment}'):
                with ui.element('div').classes(f'max-w-[80%] p-3 rounded-lg {bg_color}'):
                    ui.label(content).classes('text-sm whitespace-pre-wrap')
    
    async def _handle_send(self):
        """Handle user sending a message."""
        user_message = self._input_field.value.strip()
        if not user_message:
            return
        
        # Clear input and disable
        self._input_field.value = ''
        self._send_button.disable()
        self._input_field.disable()
        
        # Add user message to chat
        self._add_message(user_message, "user")
        
        # Put message in queue for the flow to consume
        await self._user_input_queue.put(user_message)
        
        # Show status
        self._status_label.text = 'Editorial Architect is thinking...'
        
        # Start flow if not running
        if not self._flow_running:
            asyncio.create_task(self._run_flow_iteration())
    
    def _get_user_input(self):
        """
        Callback for ChatInputNode to get user input.
        This is a blocking call that waits for the next user message.
        """
        # For synchronous flow, we need to handle this differently
        # Return the current response if available
        if self._current_response:
            return self._current_response
        return None
    
    async def _run_flow_iteration(self):
        """Run one iteration of the Pocket Flow."""
        self._flow_running = True
        
        try:
            # Create fresh flow instance
            self._flow = create_spec_interviewer_flow()
            
            # Get the chat input node and set up callback
            # We need to inject our async input retrieval
            
            # For now, let's run the flow with the current shared state
            # The flow will need to be adapted for async operation
            
            # Run flow in a thread to avoid blocking UI
            await ui.run_io(lambda: self._run_flow_sync())
            
        except Exception as e:
            self._status_label.text = f'Error: {str(e)}'
            self._input_field.disable(False)
            self._flow_running = False
        finally:
            self._flow_running = False
    
    def _run_flow_sync(self):
        """Run the flow synchronously (called from IO thread)."""
        # Inject dependencies into nodes
        from workflows.nodes import ChatInputNode, LLMEvaluateNode, GenerateSpecNode
        
        # Find and configure nodes in the flow
        # This is a simplified approach - in production we'd use proper dependency injection
        
        # For now, just process the shared store through the flow
        # We'll need to refactor the nodes to work with the UI callback pattern
        
        pass
    
    def start_conversation(self):
        """Start a new conversation session."""
        self.shared = {
            "system_prompt": self.system_prompt,
            "chat_history": [],
            "user_input": None,
            "llm_response": None,
            "spec_complete": False,
            "final_spec": None,
            "project_name": None
        }
        with self._messages_container:
            self._messages_container.clear()
        self._add_message("Hello! I'm the Editorial Architect. Tell me about your project idea and I'll help you create a detailed specification.", "assistant")
        self._status_label.text = ''
