"""Discover router module."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.features.searxng import SearxngService
from .schemas import DiscoveryResponse, BlogResult

router = APIRouter(prefix="/discover", tags=["discover"])

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
        # Get all combinations
        results = []
        for website in article_websites:
            for topic in topics:
                query = f"site:{website} {topic}"
                search_result = await searxng_service.search(
                    query=query,
                    engines='bing news',
                    pageno=1,
                    categories='news'
                )
                results.extend([
                    BlogResult(
                        **item.model_dump()
                    )
                    for item in search_result.results
                ])
    else:  # preview mode
        # Random single search
        from random import choice
        website = choice(article_websites)
        topic = choice(topics)
        query = f"site:{website} {topic}"
        
        search_result = await searxng_service.search(
            query=query,
            engines='bing news',
            pageno=1,
            categories='news'
        )
        results = [
            BlogResult(
                **item.model_dump()
            )
            for item in search_result.results
        ]

    return DiscoveryResponse(blogs=results)