from typing import Annotated, Any
from semantic_kernel.functions import (
    KernelFunction,
    KernelArguments,
    kernel_function,
    FunctionResult,
)
from semantic_kernel.kernel import Kernel
from pydantic import BaseModel


class WebSearchOption(BaseModel):
    pass


class WebSearchResult(BaseModel):
    results: list[str]


@kernel_function(
    name="web_search",
    description="Search the web using SearXNG",
)
async def searxng_web_search(
    query: Annotated[str, "The query to search for"],
    kernel: Kernel,
    arguments: KernelArguments,
    **kwargs: Any
) -> FunctionResult | None:
    pass

@kernel_function(name="retieve_web_page_content")
async def retrieve_web_content(url: Annotated[str, ""]):
    pass


SEARXNG_SEARCH_KERNEL_FUNCTION = KernelFunction.from_method(
    method=searxng_web_search,
    plugin_name="searxng_search",
)
