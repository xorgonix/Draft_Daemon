"""
Pocket Flow definition for the Research Engine.

Uses AsyncFlow for NiceGUI compatibility.
"""

from pocketflow import AsyncFlow
from .research import (
    QueryExtractionNode,
    SearchAndScrapeNode,
    DistillationNode,
    ResearchWriterNode
)


def create_research_flow():
    """
    Create and return the Research Engine flow.
    
    Flow structure:
    QueryExtractionNode -> SearchAndScrapeNode -> DistillationNode -> ResearchWriterNode
    """
    # Create node instances
    query_node = QueryExtractionNode()
    search_scrape_node = SearchAndScrapeNode(num_results=3)
    distill_node = DistillationNode()
    write_node = ResearchWriterNode()
    
    # Create flow connections
    query_node - "search" >> search_scrape_node
    search_scrape_node - "distill" >> distill_node
    distill_node - "write" >> write_node
    
    # Create AsyncFlow
    return AsyncFlow(start=query_node)
