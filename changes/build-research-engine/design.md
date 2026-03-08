# Design: Research Engine

## 1. Tooling & Utilities (`utils/search.py`, `utils/scraper.py`)
- We need a `web_search(query)` function. (Use Brave Search API if a key is provided in `.env`, otherwise return mock URLs for testing).
- We need a `scrape_url(url)` function. (Use Firecrawl API if available, otherwise implement a basic `httpx` + `BeautifulSoup` text extractor).

## 2. Agent Workflow (Pocket Flow Integration)
- The Research pipeline MUST use Pocket Flow's `BatchNode` or `AsyncParallelBatchNode` capabilities to handle multiple queries/URLs efficiently.
- **Expected Nodes in `workflows/research.py`:**
  - `QueryExtractionNode`: Reads the `01_Spec.md` and outputs a list of search queries.
  - `SearchAndScrapeNode (AsyncParallelBatchNode)`: Takes the queries, executes the web search, scrapes the top 3 URLs per query, and returns the raw text.
  - `DistillationNode`: Passes the combined raw text to the local LLM with a strict prompt to extract cited facts and anecdotes.
  - `ResearchWriterNode`: Saves the output to the local file system.

## 3. UI Hookup
- Add a "Run Research" button on the Editor page (or Dashboard) that triggers this specific flow for the active project.
