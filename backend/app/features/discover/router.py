"""Discover router module."""
from typing import Optional
import asyncio
from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.features.searxng import SearxngService
from .schemas import DiscoveryResponse, BlogResult

router = APIRouter(prefix="/discover", tags=["discover"])

async def search_with_params(
    searxng_service: SearxngService,
    website: str,
    topic: str
) -> list[BlogResult]:
    """Helper function to perform a single search."""
    query = f"site:{website} {topic}"
    search_result = await searxng_service.search(
        query=query,
        engines='bing news',
        pageno=1,
        categories='news'
    )
    return [BlogResult(**item.model_dump()) for item in search_result.results]

@router.get("", response_model=DiscoveryResponse)
async def discover(
    mode: str = Query("normal", description="Search mode (normal or preview)"),
    searxng_service: SearxngService = Depends(SearxngService)
) -> DiscoveryResponse:
    """Discover content."""
    # Define websites and topics
    article_websites = [
        'yahoo.com',
        'www.exchangewire.com',
        'businessinsider.com',
    ]
    topics = ['AI', 'tech']

    # Get search results from SearxNG
    if mode == "normal":
        # Create tasks for all combinations
        search_tasks = [
            search_with_params(searxng_service, website, topic)
            for website in article_websites
            for topic in topics
        ]
        
        # Run all searches concurrently
        results_lists = await asyncio.gather(*search_tasks)
        
        # Flatten results and remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        
        for result_list in results_lists:
            for result in result_list:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
                    
        return DiscoveryResponse(blogs=unique_results)
    
    else:  # preview mode
        # Random single search
        from random import choice
        website = choice(article_websites)
        topic = choice(topics)
        results = await search_with_params(searxng_service, website, topic)
        return DiscoveryResponse(blogs=results)