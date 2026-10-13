# Tasks: Initialize Core Workflow

- [x] 1. Set up the Python virtual environment and install `nicegui`, `openai`, and `watchdog`.
- [x] 2. Create `main.py` and initialize a basic NiceGUI app running on `localhost`.
- [x] 3. Create a `workflows/` directory and define the Pocket Flow `Node` classes for the Spec Interviewer chat loop.
- [x] 4. Connect the defined nodes into a `Flow` and link the flow's input/output to the `KickoffChat` NiceGUI component.
- [x] 5. Implement the `LLMClient` class to communicate with a local LLM server via an OpenAI-compatible endpoint.
- [x] 6. Build the `KickoffChat` NiceGUI component, injecting the "Editorial Architect" system prompt.
- [x] 7. Implement the state logic to hold the conversation history.
- [x] 8. Write the parsing function to extract the strict OpenSpec markdown format from the LLM's final response.
- [x] 9. Build the `FileSystemWriter` to create `Writing_System_Dev/Projects/<project_name>/01_Spec.md`.
- [x] 10. Build the `EditorPane` component with the split top (AI) / bottom (User) text areas.
- [x] 11. Implement the SFT data logger: on save, append the top and bottom pane texts as a JSON object to `sft_pairs.jsonl`.
