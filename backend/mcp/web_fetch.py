import logging
import os
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from typing import Optional, Any
from openai import AsyncOpenAI
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole
import uuid

WEB_PAGE_FETCH_BASE_FOLDER = os.environ.get(
    "WEB_PAGE_FETCH_BASE_FOLDER", "./web_fetch_content"
)
WEB_PAGE_FETCH_MARKDOWN_CONVERTER_ENGINE_NAME = os.environ.get(
    "WEB_PAGE_FETCH_MARKDOWN_CONVERTER_ENGINE_NAME", "MARKITDOWN"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WebFetchRequest(BaseModel):
    url: str
    query: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)


class TextContentFetchResult(BaseModel):
    result_id: str = Field(default=str(uuid.uuid4()))
    success: bool = Field(default=False)
    failed_reason: Optional[str] = None
    text_content: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    publish_date: Optional[str] = None
    screenshot_filename: Optional[str] = Field(default=None)


async def _save_fetch_result(
    fetch_result: dict[str, Any], result_id: str = str(uuid.uuid4())
) -> str:
    fetch_content_base_folder = os.path.join(WEB_PAGE_FETCH_BASE_FOLDER, result_id)
    os.makedirs(fetch_content_base_folder, exist_ok=True)
    if fetch_result.get("screenshot") is not None:
        file_path = os.path.join(
            fetch_content_base_folder,
            f"{result_id}.{fetch_result.get('screenshot_type')}",
        )
        with open(file_path, "wb") as f:
            f.write(fetch_result.get("screenshot"))
    if fetch_result.get("html_content_raw") is not None:
        file_path = os.path.join(fetch_content_base_folder, f"{result_id}.raw.html")
        with open(file_path, "w") as f:
            f.write(fetch_result.get("html_content_raw"))
    if fetch_result.get("html_content") is not None:
        file_path = os.path.join(fetch_content_base_folder, f"{result_id}.clean.html")
        with open(file_path, "w") as f:
            f.write(fetch_result.get("html_content"))
    if fetch_result.get("markdown_content") is not None:
        file_path = os.path.join(fetch_content_base_folder, f"{result_id}.final.md")
        with open(file_path, "w") as f:
            f.write(fetch_result.get("markdown_content"))
    return result_id


async def _playwright_fetch_content_of_url(
    url: str, query: str | None = None, title: str | None = None
) -> TextContentFetchResult:
    from playwright.async_api import async_playwright
    from lxml import html
    from lxml_html_clean.clean import Cleaner

    basic_safe_attrs = frozenset(["alt", "title", "name"])

    cleaner = Cleaner(
        scripts=True,
        javascript=True,
        style=True,
        inline_style=True,
        links=True,
        embedded=True,
        forms=True,
        remove_unknown_tags=False,
        kill_tags=["svg", "img", "video", "audio"],
        # allow_tags=['table', 'tr', 'td', 'th', 'thead', 'tbody', 'tfoot', 'ul', 'li', 'ol', 'div'],  # 明确允许表格标签
        safe_attrs_only=True,
        safe_attrs=basic_safe_attrs,
    )

    fetch_result = {}
    async with async_playwright() as ps:
        browser = None
        try:
            logger.info(f"Fetching content from URL: {url}")
            browser = await ps.chromium.launch(
                headless=False,
                args=["--disable-font-download", "--disable-remote-fonts"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            # Set reasonable timeout and wait conditions
            page.set_default_timeout(30_000)
            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=30_000
            )

            if not response:
                return f"Failed to load URL: {url}"

            if response.status >= 400:
                return f"HTTP error {response.status} for URL: {url}"

            # Wait for content to load
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except TimeoutError as e:
                logger.warning(f"Error waiting for load state: {e}")

            if title is None:
                title = await page.title()

            # Get the main content
            html_content = await page.content()
            clean_html_content = cleaner.clean_html(html_content)
            tree = html.fromstring(clean_html_content)
            clean_html_content = html.tostring(
                tree, pretty_print=False, encoding="utf-8", method="html"
            )
            if isinstance(clean_html_content, bytes):
                clean_html_content = clean_html_content.decode("utf-8")

            if clean_html_content is not None and len(clean_html_content) > 0:
                clean_html_content = (
                    clean_html_content.replace("  ", " ")
                    .replace("\t\t", "\t")
                    .replace("\n\n", "\n")
                )
                clean_html_content = (
                    clean_html_content.replace("  ", " ")
                    .replace("\t\t", "\t")
                    .replace("\n\n", "\n")
                )

            fetch_result["html_content_raw"] = html_content
            fetch_result["html_content"] = clean_html_content
            fetch_result["title"] = title
            fetch_result["url"] = url
            fetch_result["query"] = query
            fetch_result["screenshot"] = await page.screenshot(
                full_page=True, type="png"
            )
            fetch_result["screenshot_type"] = "png"

        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return TextContentFetchResult(
                success=False,
                url=url,
                text_content="",
                publish_date=None,
                title=title,
                failed_reason=f"Error fetching content {url}: {str(e)}",
            )

        finally:
            if browser:
                await browser.close()

        if WEB_PAGE_FETCH_MARKDOWN_CONVERTER_ENGINE_NAME.upper() == "MARKITDOWN":
            import markitdown.converters
            converter = markitdown.converters.HtmlConverter()
            fetch_result["markdown_content"] = converter.convert_string(html_content = fetch_result["html_content"]).markdown
        else:
            chat_completion_service = OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
                async_client=AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL"),
                ),
            )
            system_message = (
                "You are a content extraction specialist. Your task is to extract relevant content from HTML and convert it to clean Markdown format.\n\n"
                "INSTRUCTIONS:\n"
                "1. Extract ONLY content that is directly relevant to the user's query or page title\n"
                "2. IGNORE advertisements, recommendations, navigation menus, sidebars, and other peripheral content\n"
                "3. Preserve the original language of the content - MUST NOT translate it\n"
                "4. Format the extracted content as clean, well-structured Markdown\n"
                "5. Maintain the original text content and meaning\n"
                "6. Focus on the main article/content body\n"
                "7. Do not add any commentary or additional information not present in the source\n"
                "8. Only output the markdown content, no other text such as reasoning, explanation, etc.\n"
                "9. DO NOT process, analyze, or modify the content - only format the original raw content into Markdown\n"
                "10. Return the formatted original content as-is for subsequent analysis stages\n"
                "11. When encountering detailed data, especially tables, MUST retain ALL detailed content completely\n"
                "12. For tables: preserve all rows, columns, headers, and data values without omission\n"
                "13. For data lists, statistics, or numerical content: include every item and value\n"
                "14. Never summarize or abbreviate detailed data - maintain complete information integrity"
            )
            if query is not None:
                system_message += f"\n\nPlease extract the main content from the HTML that is relevant to this query: {query}"
            if title is not None:
                system_message += f"\n\nOr extract content related to the page title: {fetch_result['title']}"

            logger.info(f"fetched result: \n {fetch_result['html_content']}")
            settings = chat_completion_service.instantiate_prompt_execution_settings(
                temperature=0.0
            )
            message_content = await chat_completion_service.get_chat_message_content(
                chat_history=ChatHistory(
                    messages=[
                        ChatMessageContent(
                            role=AuthorRole.USER, content=fetch_result["html_content"]
                        )
                    ]
                ),
                system_message=system_message,
                settings=settings,
            )
            logger.info(f"extracted -> markdown: \n {message_content.content}")
            final_markdown_content = (
                message_content.content
                if message_content is not None and len(message_content.content) > 0
                else ""
            )
            fetch_result["markdown_content"] = final_markdown_content
        
        final_markdown_content = fetch_result.get("markdown_content")
        logger.info(f"fetched result: \n {fetch_result['markdown_content']}")
        result_id = await _save_fetch_result(fetch_result, result_id=str(uuid.uuid4()))
        final_failed_reason = (
            ""
            if final_markdown_content is not None and len(final_markdown_content) > 0
            else "Failed to extract markdown content"
        )
        final_success = (
            final_markdown_content is not None and len(final_markdown_content) > 0
        )
        return TextContentFetchResult(
            result_id=result_id,
            success=final_success,
            url=url,
            text_content=final_markdown_content,
            publish_date=None,
            title=title,
            failed_reason=final_failed_reason,
            screenshot_filename=f"{result_id}.png",
        )


def setup_web_fetch(app: FastAPI) -> FastMCP | None:
    mcp = FastMCP(
        name="web_fetch",
        version="1.0.0",
        description="Fetch content from a web page",
        stateless_http=True,
    )

    @app.get(
        "/web_page_fetch/{result_id}/screenshots/{screenshot_filename}",
        tags=["web_page_fetch"],
        response_model=TextContentFetchResult,
    )
    async def web_page_fetch_screenshot(
        result_id: str, screenshot_filename: str, request: Request, response: Response
    ):
        screenshot_file_path = os.path.join(WEB_PAGE_FETCH_BASE_FOLDER, result_id, screenshot_filename)
        if not os.path.exists(screenshot_file_path):
            return Response(status_code=404, content="Screenshot not found")
        with open(screenshot_file_path, "rb") as f:
            return Response(content=f.read(), media_type="image/png")

    @app.post(
        "/api/v1/web_page_fetch",
        tags=["web_page_fetch"],
        response_model=TextContentFetchResult,
    )
    async def web_page_fetch(request: WebFetchRequest) -> TextContentFetchResult:
        return await _playwright_fetch_content_of_url(
            url=request.url, query=request.query, title=request.title
        )

    @mcp.tool(name="web_page_fetch", description="Fetch content from a web page")
    async def web_page_fetch_tool(request: WebFetchRequest) -> TextContentFetchResult:
        return await _playwright_fetch_content_of_url(
            url=request.url, query=request.query, title=request.title
        )

    app.mount("/mcp/web_page_fetch", mcp.sse_app())
    return mcp
