# Proposal: Initialize Core Workflow & GUI

## Intent
Build the foundational scaffolding for the Agentic Writing System. We need to transition from a conceptual workflow to a functional local application where the user can initiate a project, chat with the "Spec Interviewer" LLM, and generate the physical Obsidian directory structure.

## Scope
- Scaffold the basic NiceGUI web application.
- Implement the "Editorial Architect" LLM system prompt.
- Build the conversational kickoff UI.
- Implement the File System Writer to generate `01_Spec.md` inside a newly created project directory.
- Build the dual-pane `EditorPane` component that captures the AI draft vs. user edit SFT pairs.

## Out of Scope
- Integration with SurrealDB (to be handled in a subsequent change).
- Active execution of the Brave Search/Reddit scraping pipelines.
