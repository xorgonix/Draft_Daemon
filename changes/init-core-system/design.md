openspec/changes/init-core-system/design.md
# Design: Initialize Core Workflow

## 1. NiceGUI Interface Layout
- **Main View:** A dashboard showing active project directories found in the Obsidian path.
- **Kickoff Modal/Page:** A chat interface specifically for the project initialization phase.
- **Editor View:** A layout containing two text areas (Top: Read-only AI Draft, Bottom: User Edit/Dictation area) and a "Save & Log SFT" button.

## 2. Agent Workflow (Pocket Flow Integration)
- The "Spec Interviewer" must not be a massive, monolithic while-loop. It must be implemented as a `pocketflow` Flow.
- **Expected Nodes:**
  - `ChatInputNode`: Waits for and retrieves the user's message from the NiceGUI interface.
  - `LLMEvaluateNode`: Prompts the local UMM Server to decide if the spec is complete or if more questions are needed.
  - `GenerateSpecNode`: Triggered only when the LLM resolves the conversation. Formats the OpenSpec markdown.
- **State Management:** The chat history and the current template rules must be maintained inside the Pocket Flow `Shared Store` dictionary so all nodes have access to the context.

## 3. The Resolver Logic
- When the user types a resolution command, the LLM must output the specification in strict Markdown enclosed in code blocks.
- A parsing function will extract this block, create a new timestamped folder under `Writing_System_Dev/Projects/`, and write the file as `01_Spec.md`.
