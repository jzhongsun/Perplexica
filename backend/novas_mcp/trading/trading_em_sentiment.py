from novas_mcp.trading_core import MarketCode
import httpx
import json
from datetime import datetime
from typing import Optional
import markdownify

EM_HTTP_HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

from pydantic import BaseModel, Field, ConfigDict, field_validator
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class EmNewsFetchResult(BaseModel):
    source: Optional[str] = Field(default=None, description="The source of the news")
    url: str = Field(description="The url of the news")
    publish_date: Optional[str] = Field(
        default=None, description="The publish date of the news"
    )
    title: Optional[str] = Field(default=None, description="The title of the news")
    snippet: Optional[str] = Field(default=None, description="The snippet of the news")
    content_text: Optional[str] = Field(
        default=None, description="The content of the news in text format"
    )
    content_html: Optional[str] = Field(
        default=None, description="The content of the news in html format"
    )
    content_markdown: Optional[str] = Field(
        default=None, description="The content of the news in markdown format"
    )


async def em_fetch_news_content(
    url: str, include_markdown: bool = True, redirect_count: int = 0
) -> tuple[str, str, str]:
    import lxml.html
    from lxml.html.clean import Cleaner

    cleaner = Cleaner(
        scripts=False,
        javascript=False,
        style=False,
        inline_style=False,
    )
    url = url.replace("http://", "https://")
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        response = await client.get(url)
        if response.status_code == 302:
            logger.info(f"302 redirect to {response.headers['Location']}")
            if redirect_count > 3:
                logger.error(f"Too many redirects, return empty content")
                raise RuntimeError(f"Too many redirects, return empty content")
            else:
                return await em_fetch_news_content(
                    response.headers["Location"], include_markdown, redirect_count + 1
                )

        doc = lxml.html.fromstring(response.text)
        path = "//div[@class='main']/div[@class='contentwrap']/div[@class='contentbox']/div[@class='mainleft']"
        path = path + "/div[@class='zwinfos']/div[@id='ContentBody']"
        content_body_html = doc.xpath(path)[0]

        content_text = content_body_html.text_content()
        content_html = cleaner.clean_html(
            lxml.html.tostring(
                content_body_html, pretty_print=True, encoding="unicode", method="html"
            )
        )
        if include_markdown:
            content_markdown = markdownify.markdownify(content_html)
        else:
            content_markdown = None
        logger.info(f"{url}:\n{content_text}")
        return content_text, content_html, content_markdown


async def em_retrieve_company_news(
    company_name: str,
    symbol: str,
    num_results: int = 10,
) -> list[EmNewsFetchResult]:
    """
    获取股票内幕消息，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#zyzb-0
    """
    _t = int(datetime.now().timestamp() * 1000)
    params = {
        "uid": "2037027445274012",
        "keyword": f"({symbol}){company_name}",
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": num_results,
                "preTag": "<em>",
                "postTag": "</em>",
            }
        },
    }
    import urllib.parse

    params_encoded = urllib.parse.quote(json.dumps(params))
    url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery35107699970789290389_{_t}&param={params_encoded}&_={_t}"
    # print(url)
    results: list[EmNewsFetchResult] = []
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        response = await client.get(url)
        response.raise_for_status()
        # print(response.text)
        response_text = response.text.replace(
            f"jQuery35107699970789290389_{_t}(", ""
        ).replace(")", "")
        response_json = json.loads(response_text)
        # print(response_json)
        result_json = response_json["result"]["cmsArticleWebOld"]
        # print(json.dumps(result_json, ensure_ascii=False, indent=2))
        for item in result_json:
            # print(item)
            results.append(
                EmNewsFetchResult(
                    url=item.get("url", None),
                    title=item.get("title", None),
                    snippet=item.get("content", None),
                    publish_date=item.get("date", None),
                    source=item.get("mediaName", None),
                )
            )

        for r in results:
            content_text, content_html, content_markdown = await em_fetch_news_content(
                r.url
            )
            r.content_text = content_text
            r.content_html = content_html
            r.content_markdown = content_markdown

    return results


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(em_retrieve_company_news("贵州茅台", "600519"))
