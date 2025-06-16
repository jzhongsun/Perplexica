
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from agents.sk_agents import setup_sk_agents
import click
from fastapi import FastAPI
import httpx
from pathlib import Path
import dotenv

dotenv.load_dotenv()

def setup_a2a_server(app: FastAPI):
    setup_sk_agents(app)
@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10010)
def main(host, port):
    """Starts the AG2 MCP Agent server."""
    app = FastAPI()

    setup_a2a_server(app)
    import uvicorn

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
