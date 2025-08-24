# SIMPLE MCP - Ollama Integration with JSONPlaceholder API

## תיאור בעברית
פרויקט Python שמדגים איך לחבר בין Ollama AI ל-API חיצוני באמצעות פרוטוקול MCP. המערכת מאפשרת לשאול שאלות בעברית ולקבל מידע חי מ-JSONPlaceholder API עם תשובות AI מותאמות.

## English Description
A Python-based MCP (Model Context Protocol) implementation that demonstrates how to integrate Ollama AI with external APIs. The project connects Ollama to the JSONPlaceholder API to provide live data queries with AI assistance.

## Features

- 🤖 **Ollama Integration**: Uses local Ollama models for AI responses
- 🔧 **MCP Tools**: Implements MCP tools for external API calls
- 🌐 **Live Data**: Retrieves real-time data from JSONPlaceholder API
- 🗣️ **Hebrew Support**: Supports Hebrew language queries and responses
- ⚡ **FastAPI/Flask Backend**: RESTful API for chat interactions
- 🧠 **Intelligent Tool Selection**: AI automatically chooses appropriate tools

## Available Tools

- `get_posts(limit)` - Retrieve blog posts
- `get_user_info(user_id)` - Get user information
- `get_post_by_id(post_id)` - Get specific post details
- `search_posts_by_user(user_id)` - Find all posts by a user
- `get_post_comments(post_id)` - Get post with comments

## Files

- `mcp_ollama_client_sync.py` - Main Flask server with synchronous Ollama integration
- `mcp_ollama_client.py` - Alternative async implementation
- `api_server.py` - MCP server with FastMCP tools
- `ai_chat.html` - Web interface for testing

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- An Ollama model (default: "aya")

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

4. Pull the required model:
   ```bash
   ollama pull aya
   ```

## Usage

### Start the Flask Server

```bash
python mcp_ollama_client_sync.py
```

The server will start on `http://localhost:3000`

### Test the API

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me 3 posts"}'
```

### Available Endpoints

- `POST /api/chat` - Chat with AI using MCP tools
- `GET /api/tools` - Get available tools
- `GET /` - API status

## Example Queries

- "Show me 5 posts" / "הראה לי 5 פוסטים"
- "Who is user 1?" / "מי זה משתמש 1?"
- "Show posts by user 2" / "הראה פוסטים של משתמש 2"
- "What are the comments on post 1?" / "מה התגובות על פוסט 1?"

## Configuration

Edit the configuration variables in `mcp_ollama_client_sync.py`:

- `OLLAMA_API_URL` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model to use (default: "aya")

## License

MIT License