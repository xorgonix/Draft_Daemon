# Core Architecture Specification

## 1. System Identity
The system is a local-first, agentic writing environment acting as an editorial partner for a senior engineer. It orchestrates research, structures arguments, and drafts technical articles while leaving the human in total control of the final voice.

## 2. Technology Stack
- **Backend & GUI:** Python 3.11+ using `nicegui` for a component-driven, reactive frontend, pocketflow for llm agentic capabilities.
- **Database:** SurrealDB (handles graph relations, raw text storage, and vector embeddings).
- **LLM Orchestration:** Local UMM Server (OpenAI-compatible API endpoints).
- **File System:** The primary interface for reading/writing finished text is the user's Obsidian Vault (strict Markdown with YAML frontmatter).

## 3. Core Directives
- **Zero API Lock-in:** The system must run locally or use explicitly provided local server endpoints (UMM Server).
- **Fine-Tuning Data Capture:** Every AI-generated draft text block that is subsequently edited/dictated by the user MUST be captured as a `{"prompt": "...", "completion": "..."}` pair and stored for Supervised Fine-Tuning (SFT).
- **No Black Box Research:** All scraped data (Brave Search, Firecrawl, Reddit Playwright scrapes) must be logged and saved locally before being distilled by the LLM.
