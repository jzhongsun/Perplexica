from fastapi import FastAPI
import uvicorn
from mcp.server.fastmcp import FastMCP
import dotenv

dotenv.load_dotenv()

app = FastAPI()
def setup_web_api(app: FastAPI):
    from novas_mcp.trading_api import setup_trading_webapi_server
    setup_trading_webapi_server(app)

def setup_mcp_servers(app: FastAPI):
    from novas_mcp.trading_mcp import setup_trading_mcp_server
    trading_mcp = FastMCP(name="trading", stateless_http=True)
    setup_trading_mcp_server(trading_mcp)
    
    for mcp in [trading_mcp]:
        sse_app = mcp.sse_app()
        app.mount(f"/{mcp.name}", sse_app)

@app.get("/")
async def root():
    return {"message": "Hello World"}

setup_web_api(app)
setup_mcp_servers(app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)