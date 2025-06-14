"""Suggestions service module."""
import random
from typing import List

from .schemas import SuggestionsRequest, SuggestionsResponse, Suggestion

class SuggestionsService:
    """Suggestions service class."""
    
    async def get_suggestions(self, request: SuggestionsRequest) -> SuggestionsResponse:
        """Get suggestions based on query."""
        # Mock suggestions - replace with actual suggestions implementation
        suggestions: List[Suggestion] = []
        
        # Define suggestion types if not provided
        types = request.types or ["search", "command", "topic"]
        
        # Generate mock suggestions
        for i in range(request.limit):
            suggestion_type = random.choice(types)
            
            if suggestion_type == "search":
                suggestions.append(
                    Suggestion(
                        text=f"{request.query} in {random.choice(['Python', 'JavaScript', 'Rust'])}",
                        type="search",
                        score=random.uniform(0.5, 1.0)
                    )
                )
            elif suggestion_type == "command":
                suggestions.append(
                    Suggestion(
                        text=f"/{random.choice(['help', 'search', 'explain'])} {request.query}",
                        type="command",
                        score=random.uniform(0.5, 1.0)
                    )
                )
            elif suggestion_type == "topic":
                suggestions.append(
                    Suggestion(
                        text=f"Learn about {request.query} {random.choice(['basics', 'advanced', 'examples'])}",
                        type="topic",
                        score=random.uniform(0.5, 1.0)
                    )
                )
        
        return SuggestionsResponse(
            suggestions=suggestions,
            query=request.query
        ) 