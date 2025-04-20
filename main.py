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
# MCP server registry for conversion layer
MCP_SERVERS = {
    "cryptopanic": os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/get_crypto_news"),
    # Add more MCP server mappings here if needed
}

class TelegramFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Skip Telegram POST requests
        if (
            msg.startswith("HTTP Request: POST https://api.telegram.org/") and
            any(endpoint in msg for endpoint in ["sendMessage", "getUpdates", "getMe", "deleteWebhook"])
        ):
            return False
        return True

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.addFilter(TelegramFilter())

def extract_coins_from_query(query: str):
    """Extract possible coin symbols or names from the user query (very basic)."""
    # Example: look for common coins, can be expanded with a full list
    coins = ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "dogecoin", "doge", "bnb", "ripple", "xrp"]
    found = [c for c in coins if c in query.lower()]
    return found if found else None

def call_mcp_server(mcp_choice: str, params: dict) -> str:
    """Call the specified MCP server with given params."""
    url = MCP_SERVERS.get(mcp_choice)
    if not url:
        logger.error(f"Unknown MCP server: {mcp_choice}")
        return None
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        news = resp.text.strip()
        if not news or news.lower().startswith("no news"):
            return None
        return news
    except Exception as e:
        logger.error(f"Error fetching from {mcp_choice}: {e}")
        return None

import json

def get_mcp_selection_from_llm(user_query: str) -> dict:
    """Prompt xAI/Grok to select the MCP server and arguments for the user's query."""
    prompt = (
        "Given the following user query, decide which MCP server to use and what arguments to pass. "
        "Respond ONLY with a JSON object with keys 'mcp_server' and 'params'. "
        "Example: {\"mcp_server\": \"cryptopanic\", \"params\": {\"kind\": \"news\", \"filter\": \"hot\", \"currencies\": \"BTC,ETH\", \"regions\": \"en,es\", \"public\": true, \"num_pages\": 2}}.\n"
        f"User query: {user_query}"
    )
    response = summarize_with_grok(prompt)
    try:
        data = json.loads(response)
        if not ("mcp_server" in data and "params" in data):
            raise ValueError("Missing required keys in LLM response")
        return data
    except Exception as e:
        logger.error(f"Failed to parse LLM MCP response: {e} | Raw response: {response}")
        # Fallback to default
        return {"mcp_server": "cryptopanic", "params": {"kind": "news", "num_pages": 1}}

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
            logger.info(f"[XAI] Requesting Grok (attempt {attempt}): {payload}")
            resp = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"[XAI] Grok response: {summary}")
            return summary
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
    logger.info(f"[USER] Message: {user_message}")
    try:
        # Ask LLM which MCP server and arguments to use for this query
        llm_decision = get_mcp_selection_from_llm(user_message)
        logger.info(f"[LLM] Decision: {llm_decision}")
        mcp_server = llm_decision.get("mcp_server", "cryptopanic")
        params = llm_decision.get("params", {"kind": "news", "num_pages": 1})
        logger.info(f"[MCP] Requesting {mcp_server} with params: {params}")
        news = call_mcp_server(mcp_server, params)
        if not news:
            logger.warning(f"[MCP] No news returned for {mcp_server} with params: {params}")
            await update.message.reply_text("Sorry, I couldn't fetch news at the moment. Please try again later.")
            return
        # Optionally, include MCP server info in the prompt to xAI
        prompt = (
            f"User asked: {user_message}\n"
            f"MCP server used: {mcp_server}\n"
            f"Parameters: {params}\n"
            f"Here are the latest crypto news headlines:\n{news}\nSummarize or answer the user's question using this news."
        )
        logger.info(f"[XAI] Prompt to Grok: {prompt}")
        summary = summarize_with_grok(prompt)
        logger.info(f"[BOT] Reply: {summary}")
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
