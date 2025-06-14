"""Search service module."""
import random
from typing import List

from .schemas import SearchRequest, SearchResponse, SearchResult

class SearchService:
    """Search service class."""
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform search based on request."""
        # Mock search results - replace with actual search implementation
        results: List[SearchResult] = []
        
        # Generate mock results based on mode
        if request.mode == "web":
            domains = ["example.com", "test.org", "demo.net"]
            for i in range(request.limit):
                domain = random.choice(domains)
                results.append(
                    SearchResult(
                        title=f"Result {i+1} for {request.query}",
                        url=f"https://{domain}/result-{i+1}",
                        snippet=f"This is a sample search result for the query '{request.query}'...",
                        source=domain,
                        score=random.uniform(0.5, 1.0)
                    )
                )
        elif request.mode == "academic":
            sources = ["arxiv", "springer", "ieee"]
            for i in range(request.limit):
                source = random.choice(sources)
                results.append(
                    SearchResult(
                        title=f"Academic Paper {i+1}",
                        url=f"https://{source}.org/paper-{i+1}",
                        snippet=f"Academic research related to '{request.query}'...",
                        source=source,
                        score=random.uniform(0.5, 1.0),
                        metadata={
                            "authors": ["Author 1", "Author 2"],
                            "year": random.randint(2010, 2024),
                            "citations": random.randint(0, 1000)
                        }
                    )
                )
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            mode=request.mode
        ) 