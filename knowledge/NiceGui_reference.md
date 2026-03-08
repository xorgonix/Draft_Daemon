
````
# NiceGUI: Advanced LLM Instruction Guide

## 1. Core Philosophy & Architecture
NiceGUI is an open-source, backend-first Python web framework. It handles web development details automatically, meaning developers focus almost exclusively on Python code. It is built on top of **FastAPI** (for the backend), **Vue.js** (for frontend reactivity), **Quasar** (for UI components), and **Tailwind CSS** (for styling). 

* **Concurrency:** NiceGUI relies heavily on Python's `async/await` event loop. It is resource-efficient and avoids thread-safety issues. All UI updates *must* happen on the main thread.
* **State:** Variables and states live entirely on the server unless explicitly passed to the client. 
* **Deployment:** Calling `ui.run()` spins up the FastAPI server. It can run locally, in a native window, or deployed to handle multiple clients (e.g., using Docker and NGINX).

---

## 2. Declarative Layout & Hierarchy
NiceGUI uses a "declarative UI" structure inside Python using the `with` context manager. This indentation mimics the visual layout of the DOM. 

### Hierarchy Methods
* `ui.row()` / `ui.column()` / `ui.card()`: Standard layout containers.
* `clear()`: Removes all child elements of a container.
* `delete()`: Deletes an element and all its children.
* `move(target)`: Moves an element to a new parent container.
* `descendants()`: Iterates over all children/grandchildren.
* `add_slot(name, template)`: Fills a specific Quasar/Vue slot with elements or raw HTML/Vue templates.

---

## 3. Styling & Customization
Avoid writing raw CSS where possible. Use NiceGUI's built-in methods to tap into Tailwind and Quasar.

| Method | Purpose | Example |
| :--- | :--- | :--- |
| `.classes()` | Applies Tailwind or Quasar CSS classes. | `.classes('w-full bg-blue-500 shadow-lg')` |
| `.props()` | Applies Vue/Quasar properties (attributes). | `.props('outline dense icon="add"')` |
| `.style()` | Applies raw inline CSS definitions. | `.style('color: red; padding: 10px;')` |
| `.tooltip()` | Adds a hover tooltip to the element. | `.tooltip('Click to save')` |

*Note: You can define `.default_classes()`, `.default_props()`, and `.default_style()` on custom element classes to enforce consistent styling across all instances.*

---

## 4. Event Handling
Events link the frontend UI to Python backend logic. 

* **Python Handlers:** Use `.on(event_type, handler)` or specific wrappers like `on_click=...`. The handler receives an `EventArguments` object (e.g., `events.GenericEventArguments` or `events.ValueChangeEventArguments`).
* **Client-side JS Handlers:** Pass a JavaScript function string via `js_handler` inside `.on()` to execute logic directly in the browser without server roundtrips (e.g., `js_handler='(...args) => emit(...args)'`).
* **UI Updates:** Modifying a component's property (like `label.text = 'new'`) automatically triggers a client update. You can manually call `.update()` if a complex layout requires a forced refresh.

---

## 5. State Management & Data Binding
NiceGUI excels at automatically syncing data between the Python backend and the UI.

| Technique | Description | Use Case |
| :--- | :--- | :--- |
| **Direct Binding** | `.bind_value(target, 'prop')`, `.bind_visibility_from()`, `.bind_text_to()` | Linking a specific UI element to a simple Python object or dictionary. |
| **Bindable Dataclass** | `@binding.bindable_dataclass` decorator on a Python class. | Complex data models where updating a class attribute automatically updates all bound UI elements. |
| **Reaktiv Signals** | `Signal()`, `Computed()`, `Effect()` from the `reaktiv` library. | High-performance, granular reactivity for interdependent variables (e.g., updating a total when a price signal changes). |
| **Refreshable** | `@ui.refreshable` decorator on a function. | Entire sections of the UI that need to be re-rendered when underlying list/database data changes. |

---

## 6. App Lifecycle & Storage
Manage user sessions and global app states using `app.storage` and lifecycle hooks. **Note:** Using storage requires setting a `storage_secret` in `ui.run()`.

### Storage Scopes
* `app.storage.user`: Unique per browser (cookie-based tracking, stored on server). Great for auth and user preferences.
* `app.storage.client`: Unique per connected browser tab.
* `app.storage.tab`: Unique per tab, but persists across page reloads.
* `app.storage.general`: Shared across all users/clients (global state).
* `app.storage.browser`: Stored directly in the user's `localStorage` via browser.

### Lifecycle Hooks
* `app.on_startup(func)` / `app.on_shutdown(func)`
* `app.on_connect(func)` / `app.on_disconnect(func)`

---

## 7. Routing & Authentication
Use decorators to create multi-page applications.

* **Standard Routing:** `@ui.page('/path')`.
* **Authentication:** * *Option A (Middleware):* Apply a `BaseHTTPMiddleware` to `app` that checks `app.storage.user.get('authenticated')` and returns a `RedirectResponse` to a login page if false.
    * *Option B (Sub-pages):* Inherit from `ui.sub_pages` and override `_render_page()` to check authentication dynamically, rendering a login form or a custom 404 page if unauthorized or missing.

---

## 8. Concurrency & Heavy Processing
Never block the async event loop with heavy computation or synchronous IO (like requests, OpenCV frame reading, or ML model generation).

| Method | Purpose |
| :--- | :--- |
| `run.io_bound(func)` | Runs synchronous IO tasks (like database calls or network requests) in a separate thread. |
| `run.cpu_bound(func)` | Runs heavy computations (like image processing or data crunching) in a separate process to avoid blocking the GIL. |
| `background_tasks.create()` | Fires and forgets an async function in the background. |
| `ui.timer(interval, func)` | Executes a function periodically or once after a delay (use `once=True`). |

---

## 9. Advanced Integrations & Custom Components
NiceGUI allows seamless integration of frontend libraries and custom Python extensions.

* **Custom Vue Components:** Create a subclass of `ui.element` and specify `component='my_file.vue'`. Use `self.on('custom_event', handler)` to listen to Vue `$emit` calls, and `self.run_method('js_method')` to trigger JS functions from Python.
* **Running JS:** `ui.run_javascript('console.log("hello")')` executes code on the client.
* **HTML/SVG/PDF Generation:** Use `ui.html(sanitize=True)` for rendering raw HTML.
* **FastAPI Integration:** You can add standard FastAPI endpoints using `@app.get('/path')`. For example, this is used to stream video frames (OpenCV) or return file downloads via `StreamingResponse`.

---

## 10. Common Patterns & LLM Pitfalls

When writing NiceGUI code, avoid defaulting to standard React, Vue, or vanilla web patterns. Stick strictly to the following NiceGUI-specific APIs:

### 10.1 Quasar Props Translation
Do not write raw Vue or Quasar HTML tags (like `<q-btn color="primary">`). NiceGUI elements map directly to Quasar components (e.g., `ui.button` maps to `q-btn`). 
* **Applying Props:** Pass Quasar properties as a string to the `.props()` method.
    * *Correct:* `ui.button('Save').props('color="primary" outline')`
    * *Incorrect:* `ui.button('Save', color="primary", outline=True)` *(unless explicitly supported by the NiceGUI constructor)*.
* **Boolean Props:** For boolean attributes in Quasar, simply list the word in the string (e.g., `.props('disable flat')`).

### 10.2 Navigation & Dialogs
Do not invent routing functions or use standard JS `window.location`.
* **Navigation:** Always use `ui.navigate.to('/path')` to move between pages and `ui.navigate.back()` to return.
* **Dialogs:** Use `ui.dialog()`. You can await a dialog to get a result if you subclass it and use `self.submit(value)`.
```python
with ui.dialog() as dialog, ui.card():
    ui.label('Are you sure?')
    ui.button('Yes', on_click=lambda: dialog.submit(True))
    ui.button('No', on_click=lambda: dialog.submit(False))

# Usage inside an async function:
result = await dialog


### 10.3 Data Grids & Tables

For tabular data, use `ui.table()` for basic needs and `ui.aggrid()` for advanced, high-performance data grids.

- **AG Grid:** Pass the standard AG Grid configuration dictionary directly to the component.
    

Python

```
grid = ui.aggrid({
    'columnDefs': [{'field': 'name'}, {'field': 'age'}],
    'rowData': [{'name': 'Alice', 'age': 18}, {'name': 'Bob', 'age': 21}],
    'rowSelection': 'multiple',
})
# To get selected rows asynchronously:
selected = await grid.get_selected_rows()
```

### 10.4 Fast UI Testing

NiceGUI provides a blazing-fast simulated testing framework. Do not use standard Selenium/Playwright unless testing browser-specific quirks. Use the `User` fixture.

- **Syntax:**
    

Python

```
from nicegui.testing import User

async def test_my_app(user: User):
    await user.open('/')
    user.find('Username').type('admin')
    user.find('Login').click()
    await user.should_see('Welcome, admin!')
```



#!/usr/bin/env python3
from html_sanitizer import Sanitizer
from langchain_openai import ChatOpenAI

from nicegui import ui

OPENAI_API_KEY = 'not-set'  # TODO: set your OpenAI API key here


def root():
    llm = ChatOpenAI(model_name='gpt-4o-mini', streaming=True, openai_api_key=OPENAI_API_KEY)

    async def send() -> None:
        question = text.value
        text.value = ''

        with message_container:
            ui.chat_message(text=question, name='You', sent=True)
            response_message = ui.chat_message(name='Bot', sent=False)
            spinner = ui.spinner(type='dots')

        response = ''
        async for chunk in llm.astream(question):
            response += chunk.content
            with response_message.clear():
                ui.html(response, sanitize=Sanitizer().sanitize)
            ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        message_container.remove(spinner)

    message_container = ui.column().classes('w-full max-w-2xl mx-auto flex-grow items-stretch')

    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            placeholder = 'message' if OPENAI_API_KEY != 'not-set' else \
                'Please provide your OPENAI key in the Python script first!'
            text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', send)
        ui.markdown('simple chat app built with [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary') \
            .classes('[&_a]:text-inherit [&_a]:no-underline [&_a]:font-medium')


ui.run(root, title='Chat with GPT-4o-mini')



#!/usr/bin/env python3
from audio_recorder import AudioRecorder

from nicegui import ui

with ui.row().classes('w-full justify-center'):
    audio_recorder = AudioRecorder(on_audio_ready=lambda data: ui.notify(f'Recorded {len(data)} bytes'))

with ui.row().classes('w-full justify-center'):
    ui.button('Play', on_click=audio_recorder.play_recorded_audio) \
        .bind_enabled_from(audio_recorder, 'recording')
    ui.button('Download', on_click=lambda: ui.download(audio_recorder.recording, 'audio.ogx')) \
        .bind_enabled_from(audio_recorder, 'recording')

ui.run()


import base64
from collections.abc import Callable

from nicegui import events, ui


class AudioRecorder(ui.element, component='audio_recorder.vue'):

    def __init__(self, *, on_audio_ready: Callable | None = None) -> None:
        super().__init__()
        self.recording = b''

        def handle_audio(e: events.GenericEventArguments) -> None:
            self.recording = base64.b64decode(e.args['audioBlobBase64'].encode())
            if on_audio_ready:
                on_audio_ready(self.recording)
        self.on('audio_ready', handle_audio)

    def start_recording(self) -> None:
        self.run_method('startRecording')

    def stop_recording(self) -> None:
        self.run_method('stopRecording')

    def play_recorded_audio(self) -> None:
        self.run_method('playRecordedAudio')
        
        
        
        
        
<template>
  <div>
    <button class="record-button" @mousedown="startRecording" @mouseup="stopRecording">Hold to Record</button>
    <audio ref="audioPlayer"></audio>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isRecording: false,
      audioChunks: [],
      mediaRecorder: null,
      stream: null,
      audioURL: null,
      audioBlob: null,
    };
  },
  mounted() {
    this.requestMicrophonePermission();
  },
  watch: {
    audioBlob(newBlob, oldBlob) {
      if (newBlob && newBlob !== oldBlob) {
        this.emitBlob(); // Emit the blob when it's non-null and changes
      }
    },
  },
  methods: {
    async requestMicrophonePermission() {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (error) {
        console.error("Error accessing microphone:", error);
      }
    },
    async startRecording() {
      try {
        if (!this.stream) {
          await this.requestMicrophonePermission();
        }
        this.audioChunks = [];
        this.mediaRecorder = new MediaRecorder(this.stream);
        this.mediaRecorder.addEventListener("dataavailable", (event) => {
          if (event.data.size > 0) {
            this.audioChunks.push(event.data);
          }
        });
        this.mediaRecorder.start();
        this.isRecording = true;
      } catch (error) {
        console.error("Error accessing microphone:", error);
      }
    },
    stopRecording() {
      if (this.isRecording) {
        this.mediaRecorder.addEventListener("stop", () => {
          this.isRecording = false;
          this.saveBlob();
          // this.playRecordedAudio();
        });
        this.mediaRecorder.stop();
      }
    },
    async playRecordedAudio() {
      this.audioURL = window.URL.createObjectURL(this.audioBlob);
      this.$refs.audioPlayer.src = this.audioURL;
      this.$refs.audioPlayer.play();
    },
    saveBlob() {
      this.audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
    },
    emitBlob() {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result.split(",")[1]; // Extracting base64 data from the result
        this.$emit("audio_ready", { audioBlobBase64: base64Data });
      };
      reader.readAsDataURL(this.audioBlob);
    },
  },
};
</script>

<style scoped>
.record-button {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background-color: red;
  color: white;
  border: 2px solid white;
  font-size: 16px;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.record-button:active {
  transform: translateY(2px);
  box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
}
</style>
