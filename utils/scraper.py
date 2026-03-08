"""
Web scraper utility with Tavily API support (default), Firecrawl, and BeautifulSoup fallback.

Priority:
1. Use Tavily content directly (if already fetched via search.py)
2. Firecrawl API - for dedicated scraping
3. BeautifulSoup + httpx - basic fallback

Usage:
    content = scrape_url("https://example.com")
    
Note: If you're using Tavily for search, the content is already included
in the SearchResult objects from search.py - no need to scrape again!

Environment Variables:
    TAVILY_API_KEY: Your Tavily API key
    FIRECRAWL_API_KEY: Your Firecrawl API key
"""

import os
import httpx
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class ScrapedContent:
    """Represents scraped content from a URL."""
    
    def __init__(self, url: str, title: str, content: str, success: bool = True, source: str = "scraped"):
        self.url = url
        self.title = title
        self.content = content
        self.success = success
        self.source = source  # "tavily", "firecrawl", or "beautifulsoup"
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "success": self.success,
            "source": self.source
        }


def scrape_url(url: str, timeout: float = 10.0, use_tavily_cache: bool = True) -> ScrapedContent:
    """
    Scrape content from a URL.
    
    Priority:
    1. If Tavily API key exists and use_tavily_cache=True, use Tavily's extract endpoint
    2. Firecrawl API
    3. BeautifulSoup fallback
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        use_tavily_cache: Try Tavily first if API key available
    
    Returns:
        ScrapedContent object with title and content
    """
    # Try Tavily first (if enabled)
    if use_tavily_cache:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            print(f"[SCRAPER] Using Tavily extract for: {url}")
            result = _tavily_extract(url, timeout)
            if result.success:
                return result
    
    # Try Firecrawl
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_api_key:
        print(f"[SCRAPER] No Tavily, using Firecrawl for: {url}")
        result = _firecrawl_scrape(url, timeout)
        if result.success:
            return result
    
    # Fallback to BeautifulSoup
    print(f"[SCRAPER] No API keys, using BeautifulSoup fallback for: {url}")
    return _beautifulsoup_scrape(url, timeout)


def _tavily_extract(url: str, timeout: float) -> ScrapedContent:
    """
    Extract content from URL using Tavily's extract endpoint.
    
    Args:
        url: URL to extract from
        timeout: Request timeout
    
    Returns:
        ScrapedContent object
    """
    endpoint = "https://api.tavily.com/extract"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "api_key": os.getenv("TAVILY_API_KEY"),
        "urls": [url],
        "include_raw_content": True
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        if results:
            result = results[0]
            return ScrapedContent(
                url=url,
                title=result.get("title", url),
                content=result.get("raw_content", result.get("content", "")),
                success=True,
                source="tavily"
            )
        else:
            return ScrapedContent(
                url=url,
                title=url,
                content="Error: Tavily returned no results",
                success=False,
                source="tavily"
            )
            
    except Exception as e:
        print(f"[SCRAPER] Tavily extract error: {e}")
        return ScrapedContent(
            url=url,
            title=url,
            content=f"Error: {str(e)}",
            success=False,
            source="tavily"
        )


def _firecrawl_scrape(url: str, timeout: float) -> ScrapedContent:
    """
    Scrape using Firecrawl API (returns markdown).
    
    Args:
        url: URL to scrape
        timeout: Request timeout
    
    Returns:
        ScrapedContent object
    """
    base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")
    endpoint = f"{base_url}/v1/scrape"
    
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "waitFor": 0
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(endpoint, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
        
        if data.get("success"):
            markdown_content = data.get("data", {}).get("markdown", "")
            title = data.get("data", {}).get("metadata", {}).get("title", "")
            
            print(f"[SCRAPER] Firecrawl returned {len(markdown_content)} chars for: {url}")
            return ScrapedContent(
                url=url,
                title=title or url,
                content=markdown_content,
                success=True,
                source="firecrawl"
            )
        else:
            error_msg = data.get("error", "Unknown error")
            print(f"[SCRAPER] Firecrawl error: {error_msg}")
            return ScrapedContent(
                url=url,
                title=url,
                content=f"Error: {error_msg}",
                success=False,
                source="firecrawl"
            )
            
    except Exception as e:
        print(f"[SCRAPER] Firecrawl error: {e}")
        return ScrapedContent(
            url=url,
            title=url,
            content=f"Error: {str(e)}",
            success=False,
            source="firecrawl"
        )


def _beautifulsoup_scrape(url: str, timeout: float) -> ScrapedContent:
    """
    Scrape using httpx + BeautifulSoup (returns plain text).
    
    Args:
        url: URL to scrape
        timeout: Request timeout
    
    Returns:
        ScrapedContent object
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        # Extract title
        title = soup.title.string if soup.title else url
        
        # Extract main content
        main_content = None
        for tag_name in ['article', 'main', 'content', 'post', 'entry']:
            main_content = soup.find(tag_name)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        # Extract and clean text
        text_content = main_content.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        cleaned_content = '\n'.join(lines)
        
        print(f"[SCRAPER] BeautifulSoup returned {len(cleaned_content)} chars for: {url}")
        return ScrapedContent(
            url=url,
            title=title.strip() if title else url,
            content=cleaned_content,
            success=True,
            source="beautifulsoup"
        )
        
    except Exception as e:
        print(f"[SCRAPER] Error scraping {url}: {e}")
        return ScrapedContent(
            url=url,
            title=url,
            content=f"Error: {str(e)}",
            success=False,
            source="beautifulsoup"
        )


# Test function
def _test_scraper():
    """Test the scraper function."""
    print("="*60)
    print("Testing scrape_url()")
    print("="*60)
    
    test_urls = [
        "https://example.com",
    ]
    
    for url in test_urls:
        print(f"\nScraping: {url}")
        result = scrape_url(url)
        
        print(f"Title: {result.title}")
        print(f"Success: {result.success}")
        print(f"Source: {result.source}")
        print(f"Content length: {len(result.content)} chars")
        print(f"Preview: {result.content[:200]}...")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    _test_scraper()
