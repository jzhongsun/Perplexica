from typing import List, Optional
import json

from app.core.config import get_settings
from app.features.prompts.service import PromptService
from .schemas import SuggestionRequest, SuggestionResponse, Suggestion, SuggestionInfo

class SuggestionService:
    """Service for generating search suggestions."""

    def __init__(self):
        self.settings = get_settings()
        self.prompt_service = PromptService()
        self.llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model="gpt-4-turbo-preview"
        )

    async def generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Generate search suggestions using LLM."""
        # Generate suggestions using LLM
        prompt_response = self.prompt_service.generate_prompt({
            "template_name": "suggestion_generator",
            "variables": {
                "query": request.query,
                "context": request.context or "No additional context provided"
            }
        })
        
        # Use the LLM to analyze the prompt and generate suggestions
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_response.prompt),
            ("user", """Generate suggestions in the following JSON format:
{
    "suggestions": [
        {
            "text": "suggested search query",
            "info": {
                "category": "category name",
                "relevance_score": 0.95,
                "source": "source of suggestion",
                "context": "additional context"
            }
        }
    ]
}""")
        ])
        
        response = await self.llm.apredict_messages(chat_prompt)
        
        try:
            # Parse the JSON response
            suggestions_data = json.loads(response)
            suggestions = []
            
            for item in suggestions_data["suggestions"][:request.max_suggestions]:
                info = SuggestionInfo(
                    category=item["info"].get("category"),
                    relevance_score=item["info"].get("relevance_score"),
                    source=item["info"].get("source"),
                    context=item["info"].get("context")
                )
                
                suggestion = Suggestion(
                    text=item["text"],
                    info=info
                )
                
                # Apply filters if specified
                if request.min_relevance and info.relevance_score:
                    if info.relevance_score < request.min_relevance:
                        continue
                        
                if request.categories and info.category:
                    if info.category not in request.categories:
                        continue
                        
                suggestions.append(suggestion)
            
            return SuggestionResponse(
                suggestions=suggestions,
                original_query=request.query,
                total_suggestions=len(suggestions)
            )
            
        except Exception as e:
            # If JSON parsing fails, generate simple suggestions
            suggestions = []
            lines = response.split("\n")
            
            for line in lines[:request.max_suggestions]:
                if line.strip():
                    suggestion = Suggestion(
                        text=line.strip(),
                        info=SuggestionInfo(
                            source="fallback_generator"
                        )
                    )
                    suggestions.append(suggestion)
            
            return SuggestionResponse(
                suggestions=suggestions,
                original_query=request.query,
                total_suggestions=len(suggestions)
            ) 