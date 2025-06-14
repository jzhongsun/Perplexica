from typing import Optional, List
from googleapiclient.discovery import build
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.features.prompts.service import PromptService
from .schemas import ImageSearchRequest, ImageSearchResponse, ImageResult, ImageInfo

class ImageSearchService:
    """Service for searching and analyzing images."""

    def __init__(self):
        self.settings = get_settings()
        self.custom_search = build(
            "customsearch",
            "v1",
            developerKey=self.settings.GOOGLE_CUSTOM_SEARCH_API_KEY
        )
        self.prompt_service = PromptService()
        self.llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model="gpt-4-turbo-preview"
        )

    async def search_images(self, request: ImageSearchRequest) -> ImageSearchResponse:
        """Search for images using enhanced query and metadata."""
        # Generate enhanced search query using LLM
        prompt_response = self.prompt_service.generate_prompt({
            "template_name": "image_search",
            "variables": {
                "query": request.query,
                "purpose": "search",
                "style": request.image_type or "any"
            }
        })
        
        # Use the LLM to analyze the prompt and generate search terms
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_response.prompt),
            ("user", "Generate a concise, optimized search query based on the analysis above.")
        ])
        
        enhanced_query = await self.llm.apredict_messages(chat_prompt)
        
        # Build search parameters
        search_params = {
            "q": enhanced_query,
            "cx": self.settings.GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
            "searchType": "image",
            "num": request.max_results,
            "safe": "high" if request.safe_search else "off"
        }
        
        if request.image_type:
            search_params["imgType"] = request.image_type
        if request.color_type:
            search_params["imgColorType"] = request.color_type
        if request.size:
            search_params["imgSize"] = request.size
        if request.license_type:
            search_params["rights"] = request.license_type
            
        # Perform image search
        search_response = self.custom_search.cse().list(**search_params).execute()
        
        # Process results
        results = []
        for item in search_response.get("items", []):
            info = ImageInfo(
                title=item.get("title"),
                description=item.get("snippet"),
                source=item.get("displayLink"),
                dimensions=f"{item.get('image', {}).get('width', 0)}x{item.get('image', {}).get('height', 0)}",
                file_type=item.get("fileFormat"),
                file_size=item.get("image", {}).get("byteSize")
            )
            
            result = ImageResult(
                url=item["link"],
                thumbnail_url=item.get("image", {}).get("thumbnailLink"),
                page_url=item.get("image", {}).get("contextLink"),
                info=info,
                relevance_score=None  # Could be implemented with image similarity
            )
            results.append(result)
            
        return ImageSearchResponse(
            results=results,
            total_results=int(search_response.get("searchInformation", {}).get("totalResults", 0)),
            next_page_token=search_response.get("nextPage")
        )

    async def get_image_details(self, image_url: str) -> Optional[ImageResult]:
        """Get detailed information about a specific image."""
        try:
            # Search for the exact image URL
            search_response = self.custom_search.cse().list(
                q=image_url,
                cx=self.settings.GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
                searchType="image",
                num=1
            ).execute()
            
            if not search_response.get("items"):
                return None
                
            item = search_response["items"][0]
            
            info = ImageInfo(
                title=item.get("title"),
                description=item.get("snippet"),
                source=item.get("displayLink"),
                dimensions=f"{item.get('image', {}).get('width', 0)}x{item.get('image', {}).get('height', 0)}",
                file_type=item.get("fileFormat"),
                file_size=item.get("image", {}).get("byteSize")
            )
            
            return ImageResult(
                url=item["link"],
                thumbnail_url=item.get("image", {}).get("thumbnailLink"),
                page_url=item.get("image", {}).get("contextLink"),
                info=info
            )
        except Exception:
            return None 