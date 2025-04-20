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

def fetch_cryptopanic_news(
    num_pages: int = 1,
    public: bool = True,
    filter: str = None,
    currencies: str = None,
    regions: str = None,
    kind: str = None,
    following: bool = False
) -> str:
    """Fetch news, analysis, media, or following feed from CryptoPanic with all filters."""
    logger.info(f"[MCP] Fetching CryptoPanic news with parameters: num_pages={num_pages}, public={public}, filter={filter}, currencies={currencies}, regions={regions}, kind={kind}, following={following}")
    headlines = []
    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "public": str(public).lower(),
        "page": 1
    }
    if filter:
        params["filter"] = filter
    if currencies:
        params["currencies"] = currencies
    if regions:
        params["regions"] = regions
    if kind:
        params["kind"] = kind
    if following:
        params["following"] = "true"
    for page in range(1, min(num_pages, 10) + 1):
        params["page"] = page
        logger.info(f"[MCP] Fetching page {page} with params: {params}")
        try:
            resp = requests.get(CRYPTOPANIC_API_URL, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"[MCP] CryptoPanic API error: status_code={resp.status_code} response={resp.text} | params: {params}")
                continue
            data = resp.json()
            for item in data.get("results", []):
                title = item.get("title")
                if title:
                    headlines.append(f"- {title}")
        except Exception as e:
            logger.error(f"[MCP] Exception fetching CryptoPanic news: {e} | params: {params}")
    return "\n".join(headlines) if headlines else "No news found."

@app.get("/get_crypto_news", response_class=PlainTextResponse)
def get_crypto_news(
    num_pages: int = Query(1, ge=1, le=10, description="Number of pages to fetch (max 10)"),
    public: bool = Query(True, description="Set to true for public API access"),
    filter: str = Query(None, description="UI filter: rising, hot, bullish, bearish, important, saved, lol"),
    currencies: str = Query(None, description="Comma-separated currency codes (e.g. BTC,ETH)"),
    regions: str = Query(None, description="Comma-separated region codes (e.g. en,de)"),
    kind: str = Query(None, description="news or media"),
    following: bool = Query(False, description="Set to true to fetch following feed (private only)")
):
    """Get latest crypto news from CryptoPanic with all supported filters."""
    logger.info(f"[MCP] /get_crypto_news endpoint called with parameters: num_pages={num_pages}, public={public}, filter={filter}, currencies={currencies}, regions={regions}, kind={kind}, following={following}")
    news = fetch_cryptopanic_news(
        num_pages=num_pages,
        public=public,
        filter=filter,
        currencies=currencies,
        regions=regions,
        kind=kind,
        following=following
    )
    logger.info(f"[MCP] /get_crypto_news response: {len(news.splitlines())} headlines | parameters fetched: num_pages={num_pages}, public={public}, filter={filter}, currencies={currencies}, regions={regions}, kind={kind}, following={following}")
    return news

