import asyncio
import io
import json
import logging
import os
from typing import (
    override,
    Callable,
    Awaitable,
    AsyncIterable,
    Any,
    Annotated,
    TypedDict,
    Optional,
)
from urllib.parse import urljoin
from openai import AsyncOpenAI
from semantic_kernel.kernel import Kernel, KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.functions import KernelPlugin
from semantic_kernel.contents import (
    ChatMessageContent,
    StreamingChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.agents import (
    Agent,
    AgentThread,
    AgentResponseItem,
    ChatCompletionAgent,
    ChatHistoryAgentThread,
    register_agent_type,
    DeclarativeSpecMixin,
)
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from pydantic import BaseModel, Field
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions import kernel_function
from markitdown._stream_info import StreamInfo
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents import AuthorRole
from semantic_kernel.data import TextSearchResult
from agents.utils import parse_json_response

logger: logging.Logger = logging.getLogger(__name__)

class DocumentSearchResult(TypedDict):
    content: str
    metadata: dict[str, str]

class DocumentSearchResults(TypedDict):
    query: str
    docs: list[DocumentSearchResult]

class MetaSearchAgentConfig(KernelBaseSettings):
    search_web: bool = Field(default=True)
    rerank: bool = Field(default=True)
    summarizer: bool = Field(default=True)
    rerank_threshold: float = Field(default=0.5)
    query_generator_prompt: str = Field(default="")
    response_prompt: str = Field(default="")
    active_engines: list[str] = Field(default_factory=list)


class MetaSearchDoc(TypedDict):
    content: str
    metadata: dict[str, str]


class MetaSearchResult(TypedDict):
    query: str
    docs: list[MetaSearchDoc]


class MetaSearchPlugin:
    async def fetch_content_of_url(self, url: str, query: str | None = None, title: str | None = None) -> dict[str, str | bool | None]:
        from playwright.async_api import async_playwright
        from markitdown import MarkItDown
        from markitdown.converters import HtmlConverter

        async with async_playwright() as ps:
            browser = None
            try:
                logger.info(f"Fetching content from URL: {url}")
                browser = await ps.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Set reasonable timeout and wait conditions
                page.set_default_timeout(30000)
                response = await page.goto(
                    url,
                    # wait_until="domcontentloaded",
                    # timeout=30000
                )
                
                if not response:
                    return f"Failed to load URL: {url}"
                    
                if response.status >= 400:
                    return f"HTTP error {response.status} for URL: {url}"

                # Wait for content to load
                await page.wait_for_load_state("networkidle", timeout=30000)
                if title is None:
                    title = await page.title()
                    
                # Get the main content
                html_content = await page.evaluate("document.body.innerHTML;")
                
                chat_completion_service = OpenAIChatCompletion(
                    ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                    async_client=AsyncOpenAI(
                        api_key=os.getenv("OPENAI_API_KEY"),
                        base_url=os.getenv("OPENAI_BASE_URL"),
                    ),
                )
                system_message = "You are a helpful assistant that converts HTML to markdown."
                if query is not None:
                    system_message += f"\n\nPlease extract the main content from the HTML that is relevant to this query: {query}"
                if title is not None:
                    system_message += f"\n\nOr extract content related to the page title: {title}"
                
                class MarkdownContextResult(BaseModel):
                    success: bool = Field(description="Whether the markdown content is successfully extracted")
                    failed_reason: Optional[str] = Field(description="The reason why the markdown content is not successfully extracted")
                    markdown_content: Optional[str] = Field(description="The markdown content of the page")
                    
                    
                system_message += f"\n\n ### Output Format \n\n Must return the content in json format. The json schema is: {json.dumps(MarkdownContextResult.model_json_schema(), indent=2)}"
                    
                markdown_content = await chat_completion_service.get_chat_message_content(
                    chat_history=ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content=html_content)]),
                    system_message=system_message,
                    settings=chat_completion_service.instantiate_prompt_execution_settings(temperature=0.0, response_format="json_object"),
                )
                logger.info(f"converted markdown: {markdown_content}")
                json_dict = parse_json_response(markdown_content.content)
                if json_dict is not None:
                    markdown_content_result = MarkdownContextResult.model_validate(json_dict)
                    if markdown_content_result:
                        return markdown_content_result.model_dump()
                return {"success": False, "content": None, "failed_reason": "Failed to extract markdown content"}

                # Convert to markdown with proper options
                markdown_converter = HtmlConverter()
                markdown_result = markdown_converter.convert_string(html_content, url=url)
                logger.info(f"converted markdown: {markdown_result.text_content}")
                return markdown_result.text_content

            except Exception as e:
                logger.error(f"Error fetching content from {url}: {str(e)}")
                return {"success": False, "content": None, "failed_reason": f"Error fetching content: {str(e)}"}
                
            finally:
                if browser:
                    await browser.close()

    async def seaxng_web_search(
        self, query: str, language: str = "en"
    ) -> MetaSearchResult:
        import httpx

        searxng_base_url = os.getenv("SEARXNG_BASE_URL")
        logger.info(f"searxng_base_url: {searxng_base_url}")

        # Prepare search parameters
        params = {"q": query, "format": "json"}
        params["engines"] = "360search"
        params["language"] = language
        # if categories:
        #     params["categories"] = categories
        # if engines:
        #     params["engines"] = engines
        # if language:
        #     params["language"] = language
        # if pageno:
        #     params["pageno"] = str(pageno)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                urljoin(searxng_base_url, "search"), params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            results = data["results"] if "results" in data else []
            fetch_tasks = {}
            for r in results:
                fetch_tasks[r["url"]] = {
                    "task": self.fetch_content_of_url(r["url"], query=query, title=r["title"]),
                    "title": r["title"],
                    "url": r["url"],
                }
            for item in fetch_tasks.values():
                task_result = await item["task"]

                item["success"] = task_result["success"]
                if task_result["success"]:
                    item["content"] = task_result["content"]
                else:
                    item["content"] = None
                    item["failed_reason"] = task_result["failed_reason"]

            logger.info(f"searxng_web_search: {data}")
            
            return MetaSearchResult(
                query=query,
                docs=[
                    MetaSearchDoc(
                        content=value["content"],
                        metadata={
                            "title": value["title"],
                            "url": url,
                        },
                    )
                    for url, value in fetch_tasks.items()
                ],
            )

    @kernel_function(
        name="web_search_and_retrieve",
        description="Search the web using either a query or specific links. When links are provided, retrieve content from those URLs directly. When no links are provided, use the query to search the web.",
    )
    async def web_search_and_retrieve(
        self,
        query: Annotated[str, "The query to search for"] = None,
        language: Annotated[str, "The language to search for"] = "en",
        links: Annotated[list[str], "The links to search for"] = None,
    ) -> Annotated[MetaSearchResult, "The search results"]:
        logger.info(f"web_search_and_retrieve: {query}, {links}")
        if links is not None and len(links) > 0:
            results = MetaSearchResult(query=query, docs=[])
            for link in links:
                content = await self.fetch_content_of_url(link)
                results.docs.append(MetaSearchDoc(content=content, metadata={"url": link}))
            return results
        if query is not None and len(query) > 0:
            data = await self.seaxng_web_search(query, language)
            return data
            # return MetaSearchResult(query=query, docs=[MetaSearchDoc(content=result["content"], metadata=result["metadata"]) for result in data["results"]])
        raise ValueError("No query or links provided")


@register_agent_type("meta_search_agent")
class MetaSearchAgent(DeclarativeSpecMixin, Agent):
    # class MetaSearchAgent(ChatCompletionAgent):
    instructions: str | None = None
    search_config: MetaSearchAgentConfig | None = None
    inner_chat_completion_agent: ChatCompletionAgent | None = None

    def __init__(
        self,
        *,
        config: MetaSearchAgentConfig,
        id: str | None = None,
    ):
        super().__init__(
            id=id,
            instructions=config.response_prompt,
        )
        self.instructions = config.response_prompt
        self.search_config = config
        self.inner_chat_completion_agent = ChatCompletionAgent(
            id=id,
            service=OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            ),
            instructions=self.instructions,
        )

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        pass

    @kernel_function(
        name="local_search_and_retrieve",
        description="Search the local database for the query",
    )
    async def local_search_and_retrieve(
        self, query: Annotated[str, "The query to search for"]
    ):
        pass

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:

        kernel = Kernel()
        kernel.add_service(
            OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            )
        )
        # kernel.add_function(function=KernelFunction.from_method(
        #     method=self.local_search_and_retrieve,
        #     plugin_name="local_search_and_retrieve",
        # ))
        if self.search_config.search_web:
            kernel.add_plugin(plugin_name="web_search", plugin=MetaSearchPlugin())
            
        inner_chat_completion_service = kernel.get_service(type=OpenAIChatCompletion)                
        chat_history = ChatHistory()
        chat_history.add_system_message(self.instructions)
        for message in messages:
            chat_history.add_message(message)

        agent_thread = ChatHistoryAgentThread(chat_history=chat_history)

        settings = inner_chat_completion_service.instantiate_prompt_execution_settings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True),
            temperature=0.0)
        logger.info(f"invoke_stream for {kernel} \n chat_history = {chat_history.model_dump_json(indent=2)} \n settings = {settings.model_dump_json(indent=2, exclude_none=True)}.")
        async for message_content_chunk in inner_chat_completion_service.get_streaming_chat_message_content(chat_history=chat_history, settings=settings, kernel=kernel):
            print(f"{type(message_content_chunk)}: {message_content_chunk.model_dump_json(indent=2, exclude_none=True)}")
            role = message_content_chunk.role
            if (
                role == AuthorRole.ASSISTANT
                and (message_content_chunk.items or message_content_chunk.metadata.get("usage"))
                and not any(
                    isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in message_content_chunk.items
                )
            ):
                yield AgentResponseItem(message=message_content_chunk, thread=agent_thread)
            
            # yield AgentResponseItem(message=message_content_chunk, thread=agent_thread)
        

        # inner_chat_completion_agent = ChatCompletionAgent(
        #     id=self.inner_chat_completion_agent.id,
        #     kernel=kernel,
        #     instructions=self.inner_chat_completion_agent.instructions,
        # )

        # async def internal_on_intermediate_message(message: ChatMessageContent):
        #     logger.info(
        #         f"internal_on_intermediate_message: {type(message)}, {message.items}"
        #     )
        #     if on_intermediate_message:
        #         await on_intermediate_message(message)

        # async for item in inner_chat_completion_agent.invoke_stream(
        #     messages=messages,
        #     thread=thread,
        #     on_intermediate_message=internal_on_intermediate_message,
        #     # function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=Fal),
        #     arguments=arguments,
        #     kernel=kernel,
        #     **kwargs,
        # ):
        #     thread = item.thread
        #     print(item.message.content, end="", flush=True)
        #     yield item

    @override
    @classmethod
    async def _from_dict(
        cls,
        data: dict,
        *,
        kernel: "Kernel | None" = None,
        plugins: (
            list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None
        ) = None,
        **kwargs,
    ) -> "MetaSearchAgent":
        # Returns the normalized spec fields and a kernel configured with plugins, if present.
        fields, kernel = cls._normalize_spec_fields(
            data, kernel=kernel, plugins=plugins, **kwargs
        )

        if "service" in kwargs:
            fields["service"] = kwargs["service"]

        if "function_choice_behavior" in kwargs:
            fields["function_choice_behavior"] = kwargs["function_choice_behavior"]

        return cls(**fields, kernel=kernel)
