from fastapi import FastAPI

def setup_web_mcp(app: FastAPI):
    @app.get("/api/v1/web_search")
    async def web_search(request: WebSearchRequest) -> WebSearchResponse:
        return await _web_search(request)

def setup_web_api(app: FastAPI):
    @app.get("/api/v1/web_search")
    async def web_search(request: WebSearchRequest) -> WebSearchResponse:
        return await _web_search(request)