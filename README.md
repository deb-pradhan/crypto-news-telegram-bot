# Telegram Crypto News Bot with xAI (Grok)

A Telegram bot that replies to user queries using xAI (Grok) and can fetch/summarize cryptocurrency news from an MCP server.

## Features
- Conversational AI replies via xAI (Grok)
- Fetches and summarizes latest crypto news from MCP server
- Supports user queries for specific coins/topics

## Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   - `TELEGRAM_BOT_TOKEN=your-telegram-bot-token`
   - `XAI_API_KEY=your-xai-api-key`
   - `GROK_API_URL=https://api.groq.com/openai/v1/chat/completions` (or your xAI endpoint)
   - `MCP_SERVER_URL=http://127.0.0.1:8000/get_crypto_news` (or your MCP endpoint)
4. Run the bot:
   ```bash
   python main.py
   ```

## Usage
- Start a chat with your bot on Telegram.
- Ask for crypto news or general questions!

## License
MIT
