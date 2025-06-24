# """Search module."""
# from typing import Dict, Optional, Any
# from enum import Enum

# from .meta_search_agent import MetaSearchAgent
# from app.core.prompts import (
#     WEB_SEARCH_RETRIEVER_PROMPT,
#     WEB_SEARCH_RESPONSE_PROMPT,
#     ACADEMIC_SEARCH_RETRIEVER_PROMPT,
#     ACADEMIC_SEARCH_RESPONSE_PROMPT,
#     WRITING_ASSISTANT_PROMPT,
#     WOLFRAM_ALPHA_SEARCH_RETRIEVER_PROMPT,
#     WOLFRAM_ALPHA_SEARCH_RESPONSE_PROMPT,
#     YOUTUBE_SEARCH_RETRIEVER_PROMPT,
#     YOUTUBE_SEARCH_RESPONSE_PROMPT,
#     REDDIT_SEARCH_RETRIEVER_PROMPT,
#     REDDIT_SEARCH_RESPONSE_PROMPT
# )

# class SearchMode(str, Enum):
#     """Search mode enum."""
#     WEB_SEARCH = "webSearch"
#     ACADEMIC_SEARCH = "academicSearch"
#     WRITING_ASSISTANT = "writingAssistant"
#     WOLFRAM_ALPHA = "wolframAlphaSearch"
#     YOUTUBE = "youtubeSearch"
#     REDDIT = "redditSearch"

# # Search handlers mapping
# SEARCH_HANDLERS: Dict[str, MetaSearchAgent] = {
#     SearchMode.WEB_SEARCH: MetaSearchAgent(
#         active_engines=[],
#         query_generator_prompt=WEB_SEARCH_RETRIEVER_PROMPT,
#         response_prompt=WEB_SEARCH_RESPONSE_PROMPT,
#         rerank=True,
#         rerank_threshold=0.3,
#         search_web=True,
#         summarizer=True
#     ),
#     SearchMode.ACADEMIC_SEARCH: MetaSearchAgent(
#         active_engines=["arxiv", "google scholar", "pubmed"],
#         query_generator_prompt=ACADEMIC_SEARCH_RETRIEVER_PROMPT,
#         response_prompt=ACADEMIC_SEARCH_RESPONSE_PROMPT,
#         rerank=True,
#         rerank_threshold=0,
#         search_web=True,
#         summarizer=False
#     ),
#     SearchMode.WRITING_ASSISTANT: MetaSearchAgent(
#         active_engines=[],
#         query_generator_prompt="",
#         response_prompt=WRITING_ASSISTANT_PROMPT,
#         rerank=True,
#         rerank_threshold=0,
#         search_web=False,
#         summarizer=False
#     ),
#     SearchMode.WOLFRAM_ALPHA: MetaSearchAgent(
#         active_engines=["wolframalpha"],
#         query_generator_prompt=WOLFRAM_ALPHA_SEARCH_RETRIEVER_PROMPT,
#         response_prompt=WOLFRAM_ALPHA_SEARCH_RESPONSE_PROMPT,
#         rerank=False,
#         rerank_threshold=0,
#         search_web=True,
#         summarizer=False
#     ),
#     SearchMode.YOUTUBE: MetaSearchAgent(
#         active_engines=["youtube"],
#         query_generator_prompt=YOUTUBE_SEARCH_RETRIEVER_PROMPT,
#         response_prompt=YOUTUBE_SEARCH_RESPONSE_PROMPT,
#         rerank=True,
#         rerank_threshold=0.3,
#         search_web=True,
#         summarizer=False
#     ),
#     SearchMode.REDDIT: MetaSearchAgent(
#         active_engines=["reddit"],
#         query_generator_prompt=REDDIT_SEARCH_RETRIEVER_PROMPT,
#         response_prompt=REDDIT_SEARCH_RESPONSE_PROMPT,
#         rerank=True,
#         rerank_threshold=0.3,
#         search_web=True,
#         summarizer=False
#     )
# }

# def get_search_handler(mode: str) -> Optional[MetaSearchAgent]:
#     """Get search handler by mode.
    
#     Args:
#         mode: Search mode
        
#     Returns:
#         Search handler if available
#     """
#     return SEARCH_HANDLERS.get(mode) 