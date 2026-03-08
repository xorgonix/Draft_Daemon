openspec/changes/init-core-system/specs/core/spec.md
### ADDED Requirement: GUI Kickoff Flow
- The system SHALL provide a conversational chat interface to define the article's structure before creating any local files.
- The system SHALL output the agreed-upon structure into a strict Markdown file (`01_Spec.md`) inside a newly generated project directory.

### ADDED Requirement: SFT Capture UI
- The system SHALL display AI-generated drafts and user edits side-by-side or stacked.
- The system SHALL log these pairings to a local file upon saving to build a fine-tuning dataset.
