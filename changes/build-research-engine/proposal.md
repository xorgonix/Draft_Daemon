# Proposal: Build Research & Distillation Engine

## Intent
Now that the project specification is successfully generated, the system must execute the required research. We need to build a pipeline that takes search queries, queries the web, scrapes the raw markdown from the resulting URLs, and uses the LLM to distill the raw text into highly cited nuggets and useful soundbites.

## Scope
- Create utility functions for Web Search (e.g., Brave Search API or a mocked fallback for testing) and Web Scraping (e.g., Firecrawl API or a BeautifulSoup/Playwright fallback).
- Build a new Pocket Flow called `ResearchFlow` utilizing parallel/batch nodes.
- Process the scraped data through the local UMM Server to extract "Distilled Nuggets" and "Color/Vignettes".
- Write the final output to `Writing_System_Dev/Projects/<project_name>/Research/3_Distilled.md`.
