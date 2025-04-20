import os
import logging
import requests
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
GROK_API_URL = os.getenv("GROK_API_URL", "https://api.x.ai/v1/chat/completions")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/get_crypto_news")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_coins_from_query(query: str):
    """Extract possible coin symbols or names from the user query (very basic)."""
    # Example: look for common coins, can be expanded with a full list
    coins = ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "dogecoin", "doge", "bnb", "ripple", "xrp"]
    found = [c for c in coins if c in query.lower()]
    return found if found else None

def fetch_crypto_news(user_query: str, kind: str = "news", num_pages: int = 1) -> str:
    """Fetch crypto news from MCP server (GET), optionally filtered by kind and num_pages."""
    params = {"kind": kind, "num_pages": num_pages}
    try:
        resp = requests.get(MCP_SERVER_URL, params=params, timeout=15)
        resp.raise_for_status()
        news = resp.text.strip()
        if not news or news.lower().startswith("no news"):
            return None
        return news
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return None

import time

def summarize_with_grok(prompt: str) -> str:
    """Send prompt to xAI (Grok) API and return the response, with automatic retries."""
    payload = {
        "model": "grok-3-latest",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes and answers crypto news questions."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "temperature": 0.5
    }
    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.warning(f"xAI API timeout/connection error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2)
                continue
            logger.error(f"Error with xAI API after {max_retries} attempts: {e}")
            return f"[Error summarizing: {e}]"
        except Exception as e:
            logger.error(f"Error with xAI API: {e}")
            return f"[Error summarizing: {e}]"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your crypto news bot powered by xAI. Ask me anything about crypto or request the latest news.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        # Heuristic: If user asks for news, fetch from MCP, else just use xAI
        if any(word in user_message.lower() for word in ["news", "latest", "update", "headline", "price", "market"]):
            news = fetch_crypto_news(user_message)
            if not news:
                await update.message.reply_text("Sorry, I couldn't fetch news at the moment. Please try again later.")
                return
            coins = extract_coins_from_query(user_message)
            if coins:
                prompt = f"User asked: {user_message}\nHere are the latest crypto news headlines for {', '.join(coins)}:\n{news}\nSummarize or answer the user's question using this news."
            else:
                prompt = f"User asked: {user_message}\nHere are the latest crypto news headlines:\n{news}\nSummarize or answer the user's question using this news."
        else:
            prompt = user_message
        summary = summarize_with_grok(prompt)
        if not summary or summary.startswith("[Error summarizing"):
            await update.message.reply_text("Sorry, I couldn't get an answer from xAI at the moment.")
        else:
            await update.message.reply_text(summary)
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("An unexpected error occurred. Please try again later.")

def main():
    # Start MCP server in background
    try:
        mcp_proc = subprocess.Popen([
            "uvicorn", "cryptopanic_server:app", "--host", "127.0.0.1", "--port", "8000"
        ])
        logger.info("[MCP] MCP server started automatically (PID: %s)" % mcp_proc.pid)
    except Exception as e:
        logger.error(f"[MCP] Failed to start MCP server automatically: {e}")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Crypto news bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
