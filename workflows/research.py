"""
Pocket Flow nodes for the Research Engine.

Following Pocket Flow architecture with AsyncNode for NiceGUI compatibility.
"""

from pocketflow import AsyncNode, AsyncParallelBatchNode
from utils.search import web_search, SearchResult
from utils.scraper import scrape_url, ScrapedContent
from utils.llm_client import LLMClient


# =============================================================================
# QueryExtractionNode
# =============================================================================

class QueryExtractionNode(AsyncNode):
    """
    Reads the project spec and extracts search queries for research.
    
    Shared Store:
    - Reads: 'spec_content' - The project specification text
    - Writes: 'search_queries' - List of search query strings
    """
    
    def __init__(self, llm_client=None):
        super().__init__()
        self._llm_client = llm_client
    
    def set_llm_client(self, client):
        """Inject LLM client."""
        self._llm_client = client
    
    async def prep_async(self, shared):
        """Read spec content from shared store."""
        spec_content = shared.get("spec_content", "")
        
        if not spec_content:
            print("[QueryExtraction] No spec content found in shared store")
            return ""
        
        return spec_content
    
    async def exec_async(self, spec_content):
        """
        Extract search queries from the spec using LLM.
        
        Uses a simple prompt to generate 3-5 targeted search queries.
        """
        if not spec_content:
            return []
        
        if self._llm_client is None:
            self._llm_client = LLMClient(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="gemma3-12b-32k:latest"
            )
        
        # Simple extraction prompt - optimize later
        prompt = f"""Read the following project specification and extract 3-5 specific search queries that would help research this topic.

Focus on:
- Key technologies mentioned
- Best practices and patterns
- Common challenges and solutions

Format your response as a JSON array of strings, like this:
["query 1", "query 2", "query 3"]

Project Specification:
{spec_content[:2000]}  # Limit to avoid token limits

Search queries:"""
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self._llm_client.chat_async(messages)
            
            # Parse JSON array from response
            import json
            import re
            
            # Try to extract JSON array
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group(0))
                print(f"[QueryExtraction] Extracted {len(queries)} queries from spec")
                return queries
            else:
                # Fallback: split by lines
                queries = [q.strip().strip('"\'-') for q in response.split('\n') if q.strip()]
                queries = [q for q in queries if len(q) > 5]  # Filter short queries
                print(f"[QueryExtraction] Extracted {len(queries)} queries (fallback parsing)")
                return queries[:5]  # Limit to 5
                
        except Exception as e:
            print(f"[QueryExtraction] Error extracting queries: {e}")
            # Return default queries based on spec title
            title = spec_content.split('\n')[0].replace('#', '').strip() if spec_content else "Research"
            return [
                f"{title} best practices",
                f"{title} tutorial",
                f"{title} examples"
            ]
    
    async def post_async(self, shared, prep_res, exec_res):
        """Store queries in shared store and proceed to search/scrape."""
        queries = exec_res
        
        shared["search_queries"] = queries
        
        print(f"[QueryExtraction] Queries: {queries}")
        
        return "search"


# =============================================================================
# SearchAndScrapeNode (AsyncParallelBatchNode)
# =============================================================================

class SearchAndScrapeNode(AsyncParallelBatchNode):
    """
    Executes web searches and scrapes URLs in parallel.
    
    Shared Store:
    - Reads: 'search_queries' - List of search queries
    - Writes: 'scraped_content' - List of ScrapedContent dicts
    """
    
    def __init__(self, num_results: int = 3):
        super().__init__()
        self.num_results = num_results
    
    async def prep_async(self, shared):
        """
        Prepare list of search queries to process in parallel.
        Each query will be processed concurrently.
        """
        queries = shared.get("search_queries", [])
        print(f"[SearchAndScrape] Preparing to search {len(queries)} queries")
        return queries
    
    async def exec_async(self, query):
        """
        Execute search for a single query.
        With Tavily, content is already included - no separate scraping needed!
        This runs in parallel for all queries.
        """
        print(f"[SearchAndScrape] Searching: {query}")
        
        # Search (Tavily returns content included)
        search_results = web_search(query, num_results=self.num_results, include_content=True)
        
        # Convert to scraped format
        scraped = []
        for result in search_results:
            scraped.append({
                "query": query,
                "url": result.url,
                "title": result.title,
                "content": result.content,  # Tavily provides this!
                "success": bool(result.content),
                "source": "tavily"
            })
        
        print(f"[SearchAndScrape] Got {len(scraped)} results with content for: {query}")
        return scraped
    
    async def post_async(self, shared, prep_res, exec_res_list):
        """
        Combine all scraped content and store in shared.
        exec_res_list contains results from all parallel query executions.
        """
        # Flatten all scraped content
        all_scraped = []
        for query_results in exec_res_list:
            all_scraped.extend(query_results)
        
        successful = sum(1 for item in all_scraped if item.get("success", False))
        print(f"[SearchAndScrape] Collected {successful}/{len(all_scraped)} successful scrapes")
        
        shared["scraped_content"] = all_scraped
        
        return "distill"


# =============================================================================
# DistillationNode
# =============================================================================

class DistillationNode(AsyncNode):
    """
    Distills scraped content into key insights and soundbites.
    
    Shared Store:
    - Reads: 'scraped_content' - List of scraped content
    - Writes: 'distilled_nuggets', 'vignettes' - Extracted insights
    """
    
    def __init__(self, llm_client=None):
        super().__init__()
        self._llm_client = llm_client
    
    def set_llm_client(self, client):
        """Inject LLM client."""
        self._llm_client = client
    
    async def prep_async(self, shared):
        """Prepare scraped content for distillation."""
        scraped_content = shared.get("scraped_content", [])
        
        # Combine all content
        combined = []
        for item in scraped_content:
            if item.get("success"):
                combined.append(f"Source: {item.get('url', 'Unknown')}\n{item.get('content', '')}")
        
        full_text = "\n\n---\n\n".join(combined)
        print(f"[Distillation] Processing {len(combined)} sources ({len(full_text)} chars)")
        
        return full_text
    
    async def exec_async(self, scraped_text):
        """
        Extract distilled nuggets and vignettes from scraped content.
        
        Basic extraction prompt - will be optimized later.
        """
        if not scraped_text:
            return {"nuggets": [], "vignettes": []}
        
        if self._llm_client is None:
            self._llm_client = LLMClient(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model="gemma3-12b-32k:latest"
            )
        
        # Simple distillation prompt
        prompt = f"""Extract key insights from the following research content.

Return TWO sections:

## Distilled Nuggets
- Bullet points of key facts, best practices, and actionable insights
- Each point should be concise and cited with [Source URL]

## Vignettes / Soundbites  
- Short anecdotes, examples, or illustrative quotes
- Include the source for each

Format as markdown.

Research Content:
{scraped_text[:3000]}  # Limit to avoid token limits

Extraction:"""
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self._llm_client.chat_async(messages)
            print(f"[Distillation] Generated {len(response)} chars of insights")
            return response
        except Exception as e:
            print(f"[Distillation] Error: {e}")
            return "Error distilling content. Please try again."
    
    async def post_async(self, shared, prep_res, exec_res):
        """Store distilled content in shared."""
        shared["distilled_content"] = exec_res
        
        return "write"


# =============================================================================
# ResearchWriterNode
# =============================================================================

class ResearchWriterNode(AsyncNode):
    """
    Writes the final research report to the file system.
    
    Shared Store:
    - Reads: 'distilled_content', 'project_name'
    - Writes: 'research_file_path'
    """
    
    async def prep_async(self, shared):
        """Get content and project info from shared."""
        return {
            "distilled_content": shared.get("distilled_content", ""),
            "project_name": shared.get("project_name", "Research"),
            "spec_file_path": shared.get("spec_file_path", "")
        }
    
    async def exec_async(self, prep_res):
        """Write research report to file system."""
        from pathlib import Path
        from datetime import datetime
        
        distilled = prep_res["distilled_content"]
        project_name = prep_res["project_name"]
        spec_path = prep_res["spec_file_path"]
        
        # Determine output directory
        if spec_path:
            # Write to same directory as spec
            output_dir = Path(spec_path).parent
        else:
            # Fallback to Research subdirectory
            output_dir = Path.cwd() / "Writing_System_Dev" / "Projects" / project_name / "Research"
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"02_Research_{timestamp}.md"
        output_path = output_dir / filename
        
        # Write content
        output_path.write_text(distilled, encoding='utf-8')
        
        print(f"[ResearchWriter] Saved research to: {output_path}")
        
        return str(output_path)
    
    async def post_async(self, shared, prep_res, exec_res):
        """Store file path and complete."""
        shared["research_file_path"] = exec_res
        
        return "done"
