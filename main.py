#!/usr/bin/env python3
"""
Draft Daemon - Spec Interviewer Chat with Pocket Flow
Polished UI with consistent navigation and modern design.
"""

from nicegui import ui
from workflows.flow import create_spec_interviewer_flow
from workflows.nodes import LLMEvaluateNode
from utils.llm_client import LLMClient
from components.editor_pane import EditorPane


EDITORIAL_ARCHITECT_SYSTEM_PROMPT = """
**Role:**
You are an Editorial Architect assisting a senior engineer in designing a technical article. Your goal is to guide the user from a loose idea to a concrete, strictly formatted article specification.

**Context:**
The user writes highly technical, practical articles for other engineers. The tone is analytical, systems-focused, and grounded in real-world operational experience.

**Instructions:**
1. Ask clarifying questions to understand the project scope, goals, and requirements
2. Help the user think through edge cases, constraints, and success criteria  
3. Guide them toward a clear, actionable specification
4. When you have enough information, output the complete specification in markdown format enclosed in ```markdown code blocks

Always be supportive, ask one question at a time, and ensure the user feels heard.
"""


app_state = {
    "current_spec": None,
    "current_project": None,
    "current_spec_path": None,
}


def add_header(current_page: str = '/'):
    """Add consistent header with navigation to all pages."""
    
    with ui.header().classes('w-full bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg'):
        with ui.row().classes('w-full max-w-6xl mx-auto items-center justify-between px-4 py-2'):
            # Logo/Title
            with ui.row().classes('items-center gap-3'):
                ui.icon('psychology', size='32px').classes('text-blue-200')
                ui.label('Draft Daemon').classes('text-xl font-bold')
                ui.label('OpenSpec').classes('text-sm text-blue-200 mt-1')
            
            # Navigation tabs
            with ui.row().classes('items-center gap-0'):
                nav_items = [
                    ('/', 'home', 'Home'),
                    ('/kickoff', 'chat', 'Spec Interviewer'),
                    ('/editor', 'edit', 'Editor'),
                ]
                
                for path, icon, label in nav_items:
                    is_active = current_page == path
                    with ui.button(icon=icon, on_click=lambda p=path: ui.navigate.to(p)) \
                        .props('flat dense').classes(
                            'text-white bg-white/20' if is_active else 'text-white hover:bg-white/10'
                        ).tooltip(label):
                        ui.label(label).classes('ml-2 text-sm')


def add_footer():
    """Add consistent footer."""
    with ui.footer().classes('bg-gray-50 border-t border-gray-200'):
        with ui.row().classes('w-full justify-center py-3'):
            ui.markdown('Built with [NiceGUI](https://nicegui.io) • Powered by Ollama') \
                .classes('text-xs text-gray-500')


@ui.page('/')
def index():
    """Dashboard with feature overview."""
    add_header('/')
    
    with ui.column().classes('w-full max-w-4xl mx-auto gap-8 px-4 py-12'):
        # Hero section
        with ui.column().classes('w-full items-center text-center gap-4'):
            ui.icon('psychology', size='80px').classes('text-blue-600')
            ui.label('Draft Daemon').classes('text-5xl font-bold text-gray-800')
            ui.label('Your AI-powered writing assistant for technical specifications').classes('text-xl text-gray-600')
        
        ui.separator()
        
        # Feature cards
        with ui.row().classes('w-full gap-6 justify-center'):
            # Spec Interviewer Card
            with ui.card().classes('w-80 hover:shadow-xl transition-shadow cursor-pointer') \
                .on('click', lambda: ui.navigate.to('/kickoff')):
                with ui.card_section().classes('bg-blue-50'):
                    ui.icon('chat', size='48px').classes('text-blue-600')
                with ui.card_section():
                    ui.label('Spec Interviewer').classes('text-lg font-bold text-gray-800')
                    ui.label('Chat with the Editorial Architect to define your project specifications through guided conversation.').classes('text-sm text-gray-600 mt-2')
                    ui.button('Start Chatting', icon='arrow_forward') \
                        .props('color=primary').classes('mt-4')
            
            # Editor Card
            with ui.card().classes('w-80 hover:shadow-xl transition-shadow cursor-pointer') \
                .on('click', lambda: ui.navigate.to('/editor')):
                with ui.card_section().classes('bg-green-50'):
                    ui.icon('edit', size='48px').classes('text-green-600')
                with ui.card_section():
                    ui.label('Editor').classes('text-lg font-bold text-gray-800')
                    ui.label('Review and refine AI-generated specs. Edit side-by-side with SFT logging for continuous improvement.').classes('text-sm text-gray-600 mt-2')
                    ui.button('Open Editor', icon='arrow_forward') \
                        .props('color=positive').classes('mt-4')
        
        ui.separator()
        
        # How it works
        with ui.column().classes('w-full gap-4'):
            ui.label('How It Works').classes('text-2xl font-bold text-gray-800')
            
            steps = [
                ('1', 'chat', 'Chat with AI', 'Answer questions about your project idea'),
                ('2', 'auto_awesome', 'Generate Spec', 'AI creates a structured specification'),
                ('3', 'edit', 'Refine', 'Edit and improve the generated spec'),
                ('4', 'save', 'Save & Learn', 'Changes logged for continuous improvement'),
            ]
            
            with ui.row().classes('w-full gap-4 justify-center'):
                for num, icon, title, desc in steps:
                    with ui.column().classes('items-center gap-2 w-48'):
                        with ui.element('div').classes('w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center text-xl font-bold'):
                            ui.label(num)
                        ui.icon(icon, size='32px').classes('text-blue-600')
                        ui.label(title).classes('font-bold text-gray-800')
                        ui.label(desc).classes('text-xs text-gray-600 text-center')
    
    add_footer()


@ui.page('/kickoff')
def kickoff_page():
    """Spec Interviewer with Pocket Flow (Async)."""
    add_header('/kickoff')
    
    # Shared store for Pocket Flow
    shared = {
        "system_prompt": EDITORIAL_ARCHITECT_SYSTEM_PROMPT,
        "chat_history": [],
        "messages": [],
        "user_input": None,
        "llm_response": None,
        "spec_complete": False,
        "final_spec": None,
        "project_name": None,
        "spec_file_path": None,
    }
    
    flow_running = False
    
    # Create LLM client once
    llm_client = LLMClient(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="gemma3-12b-32k:latest"
    )
    
    async def send():
        nonlocal flow_running
        if flow_running:
            return
        
        question = text.value
        if not question:
            return
        
        text.value = ''
        
        # Add user message to UI
        with message_container:
            ui.chat_message(text=question, name='You', sent=True)
            response_message = ui.chat_message(name='Bot', sent=False)
            spinner = ui.spinner(type='dots')
        
        flow_running = True
        
        try:
            # Set user input for Pocket Flow
            shared["user_input"] = question
            
            # Create flow and inject LLM client
            flow = create_spec_interviewer_flow()
            
            # Inject LLM client into LLMEvaluateNode
            chat_node = flow.start_node
            llm_node = chat_node.successors.get("evaluate")
            if isinstance(llm_node, LLMEvaluateNode):
                llm_node.set_llm_client(llm_client)
            
            # Run async flow
            await flow.run_async(shared)
            
            # Get response from shared store
            response = shared.get("llm_response", "No response")
            
            # Update UI
            with response_message.clear():
                ui.label(response)
            
            message_container.remove(spinner)
            
            # Handle spec completion
            if shared.get("spec_complete"):
                spec_content = shared.get("final_spec", "")
                project_name = shared.get("project_name", "")
                spec_path = shared.get("spec_file_path", "")
                
                app_state["current_spec"] = spec_content
                app_state["current_project"] = project_name
                app_state["current_spec_path"] = spec_path
                
                ui.notify(f'Spec complete: {project_name}', type='positive',
                         caption=f'Saved to: {spec_path}')
                
                # Show completion dialog
                with ui.dialog() as dialog, ui.card().classes('w-96'):
                    ui.label('✓ Specification Complete!').classes('text-h6 text-green-600')
                    ui.label(f'Project: {project_name}').classes('text-body1')
                    if spec_path:
                        ui.label(f'Saved to: {spec_path}').classes('text-sm text-gray-500')
                    with ui.row().classes('gap-2 mt-4'):
                        ui.button('Open in Editor', 
                                 on_click=lambda: [ui.navigate.to('/editor'), dialog.close()]
                                 ).props('color=primary')
                        ui.button('Continue', on_click=dialog.close).props('flat')
                dialog.open()
            
        except Exception as e:
            ui.notify(f'Error: {str(e)}', type='negative')
            with response_message.clear():
                ui.label(f'Error: {str(e)}')
            message_container.remove(spinner)
        finally:
            flow_running = False
    
    # Main content area
    with ui.column().classes('w-full max-w-4xl mx-auto gap-4 px-4 py-6 flex-grow'):
        # Header card
        with ui.card().classes('w-full bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('psychology', size='32px').classes('text-blue-600')
                with ui.column():
                    ui.label('Spec Interviewer').classes('text-lg font-bold text-gray-800')
                    ui.label('Chat with the Editorial Architect to define your project spec').classes('text-sm text-gray-600')
        
        # Chat messages area
        message_container = ui.column().classes('w-full h-[500px] overflow-y-auto border rounded-lg p-4 bg-gray-50')
        
        # Initial greeting
        with message_container:
            ui.chat_message(
                text="Hello! I'm the Editorial Architect. Tell me about your project idea.",
                name='Bot',
                sent=False
            )
        
        # Input area
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center gap-2'):
                text = ui.input(placeholder='Describe your project idea...') \
                    .props('rounded outlined dense') \
                    .classes('flex-grow') \
                    .on('keydown.enter', send)
                
                ui.button(icon='send', on_click=send) \
                    .props('round color=primary')
    
    add_footer()


@ui.page('/editor')
def editor_page():
    """Editor pane page with Research Engine integration."""
    add_header('/editor')
    
    # Research state
    research_running = False
    
    with ui.column().classes('w-full max-w-6xl mx-auto gap-4 px-4 py-6 flex-grow'):
        # Header card with Research button
        with ui.card().classes('w-full bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('edit', size='32px').classes('text-green-600')
                    with ui.column():
                        ui.label('Editor').classes('text-lg font-bold text-gray-800')
                        ui.label('Review and refine your AI-generated specification').classes('text-sm text-gray-600')
                
                # Research button
                research_button = ui.button(
                    'Run Research',
                    icon='search',
                    on_click=lambda: run_research()
                ).props('color=primary outline')
                research_button.tooltip('Research this topic using web search and AI distillation')
        
        # Research status
        research_status = ui.label('').classes('text-sm text-blue-600 italic')
        
        # Editor component
        editor = EditorPane()
        editor.classes('w-full')
        
        # Load existing spec if available
        if app_state.get("current_spec"):
            editor.set_ai_content(app_state.get("current_spec", ""))
        
        async def run_research():
            """Run the Research Engine flow."""
            nonlocal research_running
            
            if research_running:
                ui.notify('Research is already running!', type='warning')
                return
            
            spec_content = app_state.get("current_spec", "")
            if not spec_content:
                ui.notify('No spec loaded. Please generate a spec first.', type='warning')
                return
            
            research_running = True
            research_button.props('disable')
            research_status.text = '🔍 Starting research engine...'
            
            try:
                # Import research flow
                from workflows.research_flow import create_research_flow
                from workflows.research import QueryExtractionNode, SearchAndScrapeNode, DistillationNode
                from utils.llm_client import LLMClient
                
                # Initialize shared store for research
                research_shared = {
                    "spec_content": spec_content,
                    "project_name": app_state.get("current_project", "Research"),
                    "spec_file_path": app_state.get("current_spec_path", ""),
                    "search_queries": [],
                    "scraped_content": [],
                    "distilled_content": "",
                    "research_file_path": "",
                }
                
                # Create flow
                flow = create_research_flow()
                
                # Inject LLM client into nodes
                llm_client = LLMClient(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama",
                    model="gemma3-12b-32k:latest"
                )
                
                chat_node = flow.start_node
                if isinstance(chat_node, QueryExtractionNode):
                    chat_node.set_llm_client(llm_client)
                    research_status.text = '📝 Extracting search queries from spec...'
                
                llm_node = chat_node.successors.get("search")
                if isinstance(llm_node, SearchAndScrapeNode):
                    research_status.text = '🔍 Searching web and scraping content (parallel)...'
                
                distill_node = llm_node.successors.get("distill")
                if isinstance(distill_node, DistillationNode):
                    distill_node.set_llm_client(llm_client)
                
                # Run the flow
                await flow.run_async(research_shared)
                
                research_status.text = '✓ Research complete!'
                research_path = research_shared.get("research_file_path", "")
                
                ui.notify(
                    'Research engine complete!',
                    type='positive',
                    caption=f'Saved to: {research_path}'
                )
                
                # Show results dialog
                with ui.dialog() as dialog, ui.card().classes('w-[600px]'):
                    ui.label('✓ Research Complete!').classes('text-h6 text-green-600')
                    
                    with ui.scroll_area().classes('h-64 mt-4'):
                        ui.markdown(research_shared.get("distilled_content", "No content"))
                    
                    with ui.row().classes('gap-2 mt-4'):
                        ui.button('Close', on_click=dialog.close).props('color=primary')
                
                dialog.open()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                ui.notify(f'Research error: {str(e)}', type='negative', timeout=10000)
                research_status.text = f'✗ Error: {str(e)}'
            finally:
                research_running = False
                research_button.props('remove-disable')

    add_footer()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='Draft Daemon',
        host='localhost',
        port=8080,
        storage_secret='draft-daemon-secret-key',
        dark=False,
    )
