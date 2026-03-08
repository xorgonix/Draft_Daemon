# Draft Daemon - Development Notes & Lessons Learned

## Quick Start Commands

```bash
# Activate virtual environment
source .venv/Scripts/activate  # Git Bash
.\.venv\Scripts\activate       # PowerShell

# Run the application
python main.py

# Run tests
python tests\test_app.py

# Test Ollama directly
curl -X POST http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\": \"gemma3-12b-32k:latest\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}"
```

---

## Architecture Overview

### Tech Stack
- **Frontend**: NiceGUI (FastAPI + Vue.js + Quasar + Tailwind)
- **LLM Framework**: Pocket Flow (AsyncNode, AsyncFlow)
- **LLM Backend**: Ollama (gemma3-12b-32k:latest)
- **Python**: 3.12+

### Key Files
```
openspec/
├── main.py                      # NiceGUI app + routes
├── workflows/
│   ├── nodes.py                 # AsyncNode classes
│   └── flow.py                  # AsyncFlow orchestration
├── utils/
│   ├── llm_client.py            # Ollama API wrapper
│   ├── parser.py                # Markdown extraction
│   └── file_system_writer.py    # Spec file writer
├── components/
│   ├── kickoff_chat.py          # (optional) Chat component
│   └── editor_pane.py           # Editor with SFT logging
└── tests/
    └── test_app.py              # Unit tests
```

---

## Critical Patterns & Gotchas

### 1. NiceGUI Event Handling

**WRONG** - Don't use decorator syntax:
```python
@input_field.on('change')  # ❌ Returns None, causes TypeError
def _on_change(e):
    ...
```

**CORRECT** - Use function call syntax:
```python
def on_change(e):
    ...

input_field.on('keydown.enter', send)  # ✅
input_field.on('change', on_change)    # ✅
```

### 2. NiceGUI Props for Enable/Disable

```python
# Disable a button
button.props('disable')

# Re-enable a button
button.props('remove-disable')

# Don't use button.disabled = True/False (doesn't work reliably)
```

### 3. Pocket Flow Node Lifecycle

Every Node must implement:
```python
async def prep_async(self, shared):
    # Read from shared, return data for exec
    return data

async def exec_async(self, prep_res):
    # Do the work (LLM call, file I/O, etc.)
    return result

async def post_async(self, shared, prep_res, exec_res):
    # Write to shared, return next action string
    shared["result"] = exec_res
    return "next_action"  # or None to end
```

**CRITICAL**: `shared` is passed automatically by the Flow. Don't reference it as a global - it comes through the method parameters!

### 4. AsyncNode vs Node

**For NiceGUI, ALWAYS use AsyncNode:**
```python
from pocketflow import AsyncNode, AsyncFlow

class MyNode(AsyncNode):  # ✅
    async def prep_async(self, shared): ...
    async def exec_async(self, prep_res): ...
    async def post_async(self, shared, prep_res, exec_res): ...

# Flow must be AsyncFlow
flow = AsyncFlow(start=my_node)  # ✅

# Run with await
await flow.run_async(shared)  # ✅
```

**Don't use synchronous Node** - it blocks the NiceGUI event loop!

### 5. LLM Client for NiceGUI

```python
# In AsyncNode exec_async:
response = await self._llm_client.chat_async(messages)  # ✅

# LLM client must use OpenAI async:
from openai import AsyncOpenAI

class LLMClient:
    def __init__(self):
        self._client = AsyncOpenAI(base_url=..., api_key=...)
    
    async def chat_async(self, messages):
        response = await self._client.chat.completions.create(...)
        return response.choices[0].message.content
```

### 6. Shared Store Structure

```python
shared = {
    # For LLM context
    "system_prompt": "...",
    "chat_history": [{"role": "user", "content": "..."}],
    
    # For UI rendering
    "messages": [{"role": "user", "content": "..."}],
    
    # Current input
    "user_input": "...",
    
    # Results
    "llm_response": "...",
    "spec_complete": False,
    "final_spec": "...",
    "project_name": "...",
    "spec_file_path": "...",
}
```

### 7. Flow Connections

```python
# Create nodes
node_a = NodeA()
node_b = NodeB()
node_c = NodeC()

# Connect with named actions
node_a - "action1" >> node_b
node_b - "action2" >> node_a  # Loop back
node_b - "action3" >> node_c  # Branch

# Create flow
flow = AsyncFlow(start=node_a)
```

### 8. NiceGUI Chat Message Pattern

```python
# Following the reference demo exactly:
message_container = ui.column().classes('w-full max-w-3xl mx-auto')

with message_container:
    ui.chat_message(text="Hello!", name='Bot', sent=False)
    ui.chat_message(text="Hi!", name='You', sent=True)

# Input with Enter key:
text = ui.input(placeholder='Type...') \
    .props('rounded outlined input-class=mx-3') \
    .classes('w-full self-center') \
    .on('keydown.enter', send)

ui.button(icon='send', on_click=send).props('round')
```

---

## Common Errors & Fixes

### Error: `'NoneType' object is not subscriptable`
**Cause**: LLM returned `None` or flow didn't execute properly.
**Fix**: Add null checks in `post_async()`:
```python
if exec_res is None:
    exec_res = "Error: No response"
```

### Error: `No input callback registered for ChatInputNode`
**Cause**: Forgot to call `set_input_callback()` on the node.
**Fix**:
```python
if isinstance(chat_node, ChatInputNode):
    async def get_input():
        return shared.get("user_input", "")
    chat_node.set_input_callback(get_input)
```

### Error: `TypeError: 'Input' object is not callable`
**Cause**: Used `@input_field.on('change')` decorator syntax.
**Fix**: Use `input_field.on('change', callback)` function syntax.

### Error: Button shows 🚫 (disabled cursor)
**Cause**: Button has `.disable()` or `.props('disable')`.
**Fix**: Use `.props('remove-disable')` to re-enable.

### Error: UnicodeEncodeError with emojis
**Cause**: Windows console can't encode certain Unicode characters.
**Fix**: Avoid emojis in print statements, or set console encoding:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

---

## Development Workflow

### 1. Before Running
- [ ] Ollama running: `ollama serve`
- [ ] Model loaded: `ollama pull gemma3-12b-32k:latest`
- [ ] Virtual env activated

### 2. Testing Changes
1. Make code change
2. Hard refresh browser: `Ctrl + Shift + R`
3. Watch console for debug output
4. Check `http://localhost:8080` responds

### 3. Debug Pattern
Add print statements in node lifecycle:
```python
async def prep_async(self, shared):
    print(f"[Node] prep: {shared.keys()}")
    return ...

async def exec_async(self, prep_res):
    print(f"[Node] exec: {prep_res}")
    return ...

async def post_async(self, shared, prep_res, exec_res):
    print(f"[Node] post: {exec_res}")
    return "next"
```

### 4. Testing LLM Directly
```python
from utils.llm_client import LLMClient
import asyncio

async def test():
    client = LLMClient()
    messages = [{"role": "user", "content": "Hello"}]
    response = await client.chat_async(messages)
    print(response)

asyncio.run(test())
```

---

## NiceGUI Reference Patterns

### Input with Send Button
```python
async def send():
    question = text.value
    text.value = ''
    # Process...

text = ui.input(placeholder='...') \
    .on('keydown.enter', send)

ui.button(icon='send', on_click=send).props('round')
```

### Spinner During Async Operation
```python
with container:
    response_message = ui.chat_message(name='Bot', sent=False)
    spinner = ui.spinner(type='dots')

# After async operation:
with response_message.clear():
    ui.label(response_text)
container.remove(spinner)
```

### Toast Notifications
```python
ui.notify('Success!', type='positive')
ui.notify('Error occurred', type='negative')
ui.notify('Warning', type='warning')
```

### Dialog with Actions
```python
with ui.dialog() as dialog, ui.card():
    ui.label('Complete!')
    with ui.row():
        ui.button('OK', on_click=dialog.close)
        ui.button('Cancel', on_click=dialog.close)
dialog.open()
```

---

## Project Conventions

### Naming
- Nodes: `*Node` (e.g., `ChatInputNode`, `LLMEvaluateNode`)
- Flows: `create_*_flow()` function
- Components: PascalCase (e.g., `EditorPane`, `KickoffChat`)
- Utils: snake_case files (e.g., `llm_client.py`, `parser.py`)

### Shared Store Keys
- `messages` - For UI rendering (includes system messages)
- `chat_history` - For LLM context (user/assistant only)
- `*_complete` - Boolean completion flags
- `final_*` - Final results

### File Structure
```
New feature? Create:
1. workflows/nodes.py - Add Node class
2. workflows/flow.py - Add to flow
3. main.py - Add UI integration
4. tests/test_app.py - Add test
```

---

## Performance Tips

1. **Don't block the event loop** - Use `await` for all I/O
2. **Use `run.io_bound()`** for synchronous operations in NiceGUI
3. **Clear containers** before re-rendering: `container.clear()`
4. **Remove spinners** after async ops: `container.remove(spinner)`
5. **Reuse LLM client** - Create once, inject into nodes

---

## Checklist for New Features

- [ ] Node class with `prep_async`, `exec_async`, `post_async`
- [ ] Add node to flow with named connections
- [ ] Use `AsyncFlow` for NiceGUI
- [ ] Inject dependencies (LLM client, etc.)
- [ ] Update shared store structure
- [ ] Add UI component with proper event handlers
- [ ] Add tests
- [ ] Test with hard refresh (`Ctrl + Shift + R`)

---

## Resources

- **NiceGUI Docs**: https://nicegui.io/documentation
- **Pocket Flow**: https://github.com/the-pocket/PocketFlow
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **Quasar Components**: https://quasar.dev/vue-components/ (for `.props()`)
- **Tailwind CSS**: https://tailwindcss.com/docs (for `.classes()`)

---

## Contact & Support

When stuck:
1. Check console for debug prints
2. Test LLM directly with curl
3. Verify flow structure with `print(flow.start_node.successors)`
4. Hard refresh browser
5. Check Ollama is running: `netstat -ano | findstr :11434`
