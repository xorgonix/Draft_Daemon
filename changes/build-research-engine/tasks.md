# Tasks: Build Research Engine

- [ ] 1. Install required packages: `httpx`, `beautifulsoup4`, `python-dotenv`.
- [ ] 2. Create `utils/search.py` and implement a web search function (support Brave Search API via env vars, with a mock fallback).
- [ ] 3. Create `utils/scraper.py` and implement a URL markdown extraction function (support Firecrawl API via env vars, with a BeautifulSoup fallback).
- [ ] 4. Create `workflows/research.py` and define the `QueryExtractionNode`.
- [ ] 5. Define the `SearchAndScrapeNode` as an `AsyncParallelBatchNode` to handle multiple URLs concurrently.
- [ ] 6. Define the `DistillationNode` with a strict system prompt targeting "Distilled Nuggets" and "Vignettes/Soundbites".
- [ ] 7. Define the `ResearchWriterNode` to output the final formatted Markdown to the `Research/` subdirectory of the active project.
- [ ] 8. Connect the nodes into an `AsyncFlow`.
- [ ] 9. Update the NiceGUI `EditorPane` (or create a new component) with a button to trigger the Research Flow for the currently active project.
