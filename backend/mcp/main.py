from fastapi import FastAPI
import uvicorn
from web_search import setup_web_search
from web_fetch import setup_web_fetch
import dotenv

dotenv.load_dotenv()

app = FastAPI()
setup_web_search(app)
setup_web_fetch(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)