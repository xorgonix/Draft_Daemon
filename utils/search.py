"""
Web search utility with Tavily API support (default) and fallbacks.

Priority:
1. Tavily API (default) - provides search + content extraction
2. Brave Search API - search only
3. Mock fallback - for testing without API keys

Usage:
    results = web_search("your query")
    
Environment Variables:
    TAVILY_API_KEY: Your Tavily API key (default search engine)
    BRAVE_API_KEY: Your Brave Search API key (fallback)
"""

import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, title: str, url: str, snippet: str, content: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.content = content  # Full page content (Tavily provides this)
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "content": self.content
        }


def web_search(query: str, num_results: int = 5, include_content: bool = True) -> List[SearchResult]:
    """
    Search the web using Tavily API (default) with fallbacks.
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 5)
        include_content: Whether to fetch full page content (Tavily only)
    
    Returns:
        List of SearchResult objects
    """
    # Try Tavily first (default)
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if tavily_api_key:
        print(f"[SEARCH] Using Tavily API for: '{query}'")
        return _tavily_search(query, num_results, include_content)
    
    # Fallback to Brave
    brave_api_key = os.getenv("BRAVE_API_KEY")
    
    if brave_api_key:
        print(f"[SEARCH] No TAVILY_API_KEY, using Brave Search API for: '{query}'")
        return _brave_search(query, num_results)
    
    # Last resort: mock fallback
    print(f"[SEARCH] No API keys set, using mock fallback for: '{query}'")
    return _mock_search(query, num_results)


def _tavily_search(query: str, num_results: int, include_content: bool) -> List[SearchResult]:
    """
    Perform search using Tavily API.
    
    Tavily provides both search results AND full page content in one call,
    which is perfect for our research engine.
    
    Args:
        query: Search query
        num_results: Number of results
        include_content: Fetch full page content
    
    Returns:
        List of SearchResult objects
    """
    endpoint = "https://api.tavily.com/search"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "api_key": os.getenv("TAVILY_API_KEY"),
        "query": query,
        "search_depth": "basic",  # or "advanced" for deeper search
        "include_answer": False,
        "include_raw_content": include_content,
        "max_results": min(num_results, 10),  # Tavily max is 10
        "include_domains": [],  # Can restrict to specific domains if needed
        "exclude_domains": []
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(endpoint, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
        
        results = []
        search_results = data.get("results", [])
        
        for result in search_results[:num_results]:
            results.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("content", ""),
                content=result.get("raw_content", "")  # Full page content!
            ))
        
        print(f"[SEARCH] Tavily returned {len(results)} results for: '{query}'")
        return results
        
    except httpx.HTTPError as e:
        print(f"[SEARCH] Tavily API error: {e}, falling back to Brave")
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if brave_api_key:
            return _brave_search(query, num_results)
        return _mock_search(query, num_results)
    except Exception as e:
        print(f"[SEARCH] Tavily unexpected error: {e}, falling back to Brave")
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if brave_api_key:
            return _brave_search(query, num_results)
        return _mock_search(query, num_results)


def _brave_search(query: str, num_results: int) -> List[SearchResult]:
    """
    Perform search using Brave Search API (fallback).
    
    Note: Brave only provides search results, not full content.
    You'll need to use scraper.py to fetch content.
    
    Args:
        query: Search query
        num_results: Number of results
    
    Returns:
        List of SearchResult objects
    """
    base_url = os.getenv("BRAVE_BASE_URL", "https://api.search.brave.com/res/v1")
    endpoint = f"{base_url}/web/search"
    
    brave_api_key = os.getenv("BRAVE_API_KEY")
    
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": brave_api_key
    }
    
    params = {
        "q": query,
        "count": min(num_results, 20),  # Brave max is 20 per request
        "safesearch": "off"
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(endpoint, headers=headers, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        results = []
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results[:num_results]:
            results.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("description", ""),
                content=""  # Brave doesn't provide full content
            ))
        
        print(f"[SEARCH] Brave API returned {len(results)} results for: '{query}'")
        return results
        
    except httpx.HTTPError as e:
        print(f"[SEARCH] Brave API error: {e}, falling back to mock")
        return _mock_search(query, num_results)
    except Exception as e:
        print(f"[SEARCH] Brave unexpected error: {e}, falling back to mock")
        return _mock_search(query, num_results)


def _mock_search(query: str, num_results: int) -> List[SearchResult]:
    """
    Mock search results for testing without API keys.
    
    Args:
        query: Search query
        num_results: Number of results
    
    Returns:
        List of mock SearchResult objects
    """
    # Generate realistic mock URLs based on query
    query_slug = query.lower().replace(" ", "-").replace(".", "")[:50]
    
    mock_results = [
        SearchResult(
            title=f"Understanding {query.title()} - Complete Guide",
            url=f"https://example.com/guides/{query_slug}-guide",
            snippet=f"A comprehensive guide to {query}. Learn everything you need to know about this topic with practical examples and expert insights.",
            content=f"This is mock content for {query}. In production, this would be the full page content from Tavily API."
        ),
        SearchResult(
            title=f"{query.title()}: Best Practices and Tips",
            url=f"https://devblog.io/posts/{query_slug}-best-practices",
            snippet=f"Discover best practices for {query}. This article covers common pitfalls, optimization techniques, and real-world applications.",
            content=f"Mock content about {query} best practices. Tavily would return actual page content here."
        ),
        SearchResult(
            title=f"Introduction to {query.title()} | Tech Docs",
            url=f"https://docs.example.org/intro/{query_slug}",
            snippet=f"Getting started with {query}. Step-by-step tutorials and documentation for beginners and advanced users.",
            content=f"Mock tutorial content for {query}."
        ),
        SearchResult(
            title=f"{query.title()} - Community Discussion",
            url=f"https://reddit.com/r/technology/comments/{query_slug}",
            snippet=f"Community discussion about {query}. Read experiences, tips, and recommendations from practitioners in the field.",
            content=f"Mock community discussion about {query}."
        ),
        SearchResult(
            title=f"Advanced {query.title()} Techniques",
            url=f"https://medium.com/@expert/{query_slug}-advanced",
            snippet=f"Deep dive into advanced {query} techniques. Learn from industry experts and take your skills to the next level.",
            content=f"Mock advanced content for {query}."
        ),
    ]
    
    return mock_results[:num_results]


# Test function
def _test_search():
    """Test the search function."""
    print("="*60)
    print("Testing web_search() with Tavily")
    print("="*60)
    
    test_queries = [
        "Python async programming",
        "Machine learning best practices",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("="*60)
        results = web_search(query, num_results=3, include_content=True)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Snippet: {result.snippet[:100]}...")
            print(f"   Content length: {len(result.content)} chars")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    _test_search()
