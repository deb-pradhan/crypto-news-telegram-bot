# Project Tasks: Telegram Crypto News Bot with xAI (Grok)

This document tracks all major tasks and subtasks for building your Telegram bot that uses xAI (Grok) for conversation and fetches news from the MCP server.

---

## ✅ = Complete
## ⬜️ = Not started / In progress

---

## 1. Project Setup
- [x] Create a new Python project directory structure
- [x] Create and configure `.env` file for secrets
- [x] Create `requirements.txt` for dependencies
- [x] Create this `PROJECT_TASKS.md` tracker

## 2. Core Bot Functionality
- [x] Implement basic Telegram bot setup (start, help commands)
- [x] Implement message handler for user queries
- [x] Integrate xAI (Grok) API for conversation and summarization
- [x] Integrate xAI (Grok) API for conversation and summarization
- [x] Integrate MCP server API for fetching crypto news
- [x] Route user queries: decide when to use xAI vs. MCP news

## 3. Advanced Features
- [x] Allow user to specify coins/topics for news
    - [x] Parse user queries for coin/topic keywords
    - [x] Pass parsed filters to MCP server
    - [x] Respond with filtered news
- [x] Summarize or filter news as per user query
    - [x] Use xAI to summarize fetched news for specific coins/topics
    - [ ] Allow user to request summaries or details
- [x] Handle errors and invalid inputs gracefully
    - [x] Add user-friendly error messages
    - [x] Log errors for debugging
- [ ] Support for replying with both news and conversational answers

## 4. Code Quality & DevOps
- [x] Add logging for debugging and monitoring
- [ ] Add comments and docstrings for maintainability
- [ ] Write a README with setup and usage instructions
- [ ] (Optional) Add Dockerfile for easy deployment

## 5. Testing
- [ ] Manual test: Telegram chat interaction
- [ ] Test xAI (Grok) integration
- [ ] Test MCP server integration
- [ ] Test combined flows (user asks for news, bot fetches & summarizes)

---

## Progress
- Tasks will be checked off (✅) as they are completed.
- Subtasks may be added or refined as the project evolves.

---

_Last updated: 2025-04-20_
