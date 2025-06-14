from typing import Optional
from googleapiclient.discovery import build
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.features.prompts.service import PromptService
from .schemas import VideoSearchRequest, VideoSearchResponse, VideoResult, VideoInfo

class VideoSearchService:
    """Service for searching and analyzing videos."""

    def __init__(self):
        self.settings = get_settings()
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=self.settings.YOUTUBE_API_KEY
        )
        self.prompt_service = PromptService()
        self.llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model="gpt-4-turbo-preview"
        )

    async def search_videos(self, request: VideoSearchRequest) -> VideoSearchResponse:
        """Search for videos using enhanced query and metadata."""
        # Generate enhanced search query using LLM
        prompt_response = self.prompt_service.generate_prompt({
            "template_name": "youtube_search",
            "variables": {"query": request.query}
        })
        
        # Use the LLM to analyze the prompt and generate search terms
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_response.prompt),
            ("user", "Generate a concise, optimized search query based on the analysis above.")
        ])
        
        enhanced_query = await self.llm.apredict_messages(chat_prompt)
        
        # Perform YouTube search
        search_response = self.youtube.search().list(
            q=enhanced_query,
            part="snippet",
            maxResults=request.max_results,
            type="video",
            regionCode=request.region_code,
            relevanceLanguage=request.language,
            order=request.order
        ).execute()

        # Get video details
        video_ids = [item["id"]["videoId"] for item in search_response["items"]]
        video_details = self.youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()

        # Process results
        results = []
        for item, details in zip(search_response["items"], video_details["items"]):
            snippet = details["snippet"]
            statistics = details["statistics"]
            
            info = VideoInfo(
                title=snippet["title"],
                description=snippet["description"],
                channel_name=snippet["channelTitle"],
                duration=details["contentDetails"]["duration"],
                view_count=int(statistics.get("viewCount", 0)),
                published_at=snippet["publishedAt"]
            )
            
            result = VideoResult(
                video_id=item["id"]["videoId"],
                url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                thumbnail_url=snippet["thumbnails"]["high"]["url"],
                info=info,
                relevance_score=None  # Could be implemented with embedding similarity
            )
            results.append(result)

        return VideoSearchResponse(
            results=results,
            total_results=search_response["pageInfo"]["totalResults"],
            next_page_token=search_response.get("nextPageToken")
        )

    async def get_video_details(self, video_id: str) -> Optional[VideoResult]:
        """Get detailed information about a specific video."""
        try:
            response = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            ).execute()

            if not response["items"]:
                return None

            video = response["items"][0]
            snippet = video["snippet"]
            statistics = video["statistics"]

            info = VideoInfo(
                title=snippet["title"],
                description=snippet["description"],
                channel_name=snippet["channelTitle"],
                duration=video["contentDetails"]["duration"],
                view_count=int(statistics.get("viewCount", 0)),
                published_at=snippet["publishedAt"]
            )

            return VideoResult(
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                thumbnail_url=snippet["thumbnails"]["high"]["url"],
                info=info
            )
        except Exception:
            return None 