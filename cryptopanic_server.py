import os
import logging
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MCP] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MCP")

load_dotenv()

CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

app = FastAPI()

def fetch_cryptopanic_news(kind: str = "news", num_pages: int = 1) -> str:
    """Fetch news, analysis, or videos from CryptoPanic."""
    logger.info(f"Fetching CryptoPanic news: kind={kind}, num_pages={num_pages}")
    headlines = []
    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "kind": kind,
        "public": "true",
        "page": 1
    }
    for page in range(1, min(num_pages, 10) + 1):
        params["page"] = page
        try:
            resp = requests.get(CRYPTOPANIC_API_URL, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"[MCP] CryptoPanic API error: status_code={resp.status_code} response={resp.text}")
                continue
            data = resp.json()
            for item in data.get("results", []):
                title = item.get("title")
                if title:
                    headlines.append(f"- {title}")
        except Exception as e:
            logger.error(f"[MCP] Exception fetching CryptoPanic news: {e}")
    return "\n".join(headlines) if headlines else "No news found."

@app.get("/get_crypto_news", response_class=PlainTextResponse)
def get_crypto_news(
    kind: str = Query("news", description="Content type: news, analysis, videos"),
    num_pages: int = Query(1, ge=1, le=10, description="Number of pages to fetch (max 10)")
):
    """Get latest crypto news from CryptoPanic."""
    logger.info(f"[MCP] /get_crypto_news endpoint called: kind={kind}, num_pages={num_pages}")
    news = fetch_cryptopanic_news(kind=kind, num_pages=num_pages)
    logger.info(f"[MCP] /get_crypto_news response: {len(news.splitlines())} headlines")
    return news
