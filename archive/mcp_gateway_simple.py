#!/usr/bin/env python3
"""
Simplified MCP Gateway - Direct HTTP integration
"""
import asyncio
import httpx
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "aya"
BASE_URL = "https://jsonplaceholder.typicode.com"

# Direct MCP tools integration (no stdio)
async def get_posts_tool(limit: int = 10):
    """Direct integration of get_posts tool"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/posts")
        response.raise_for_status()
        posts = response.json()
        
        limited_posts = posts[:limit]
        
        cleaned_posts = []
        for post in limited_posts:
            cleaned_posts.append({
                "id": post["id"],
                "title": post["title"],
                "content": post["body"][:100] + "..." if len(post["body"]) > 100 else post["body"],
                "author_id": post["userId"]
            })
        
        return cleaned_posts

async def get_user_info_tool(user_id: int):
    """Direct integration of get_user_info tool"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/users/{user_id}")
        response.raise_for_status()
        user = response.json()
        
        return {
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "email": user["email"],
            "phone": user["phone"],
            "website": user["website"],
            "company": user["company"]["name"],
            "city": user["address"]["city"]
        }

async def search_posts_by_user_tool(user_id: int):
    """Direct integration of search_posts_by_user tool"""
    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{BASE_URL}/users/{user_id}")
        user_response.raise_for_status()
        user = user_response.json()
        
        posts_response = await client.get(f"{BASE_URL}/posts?userId={user_id}")
        posts_response.raise_for_status()
        posts = posts_response.json()
        
        result = {
            "user_name": user["name"],
            "user_email": user["email"], 
            "posts_count": len(posts),
            "posts": []
        }
        
        for post in posts:
            result["posts"].append({
                "id": post["id"],
                "title": post["title"],
                "content": post["body"][:80] + "..." if len(post["body"]) > 80 else post["body"]
            })
            
        return result

async def get_post_comments_tool(post_id: int):
    """Direct integration of get_post_comments tool"""
    async with httpx.AsyncClient() as client:
        post_response = await client.get(f"{BASE_URL}/posts/{post_id}")
        post_response.raise_for_status()
        post = post_response.json()
        
        comments_response = await client.get(f"{BASE_URL}/posts/{post_id}/comments")
        comments_response.raise_for_status()
        comments = comments_response.json()
        
        return {
            "post": {
                "id": post["id"],
                "title": post["title"],
                "content": post["body"]
            },
            "comments_count": len(comments),
            "comments": [
                {
                    "id": comment["id"],
                    "author_name": comment["name"],
                    "author_email": comment["email"],
                    "content": comment["body"][:60] + "..." if len(comment["body"]) > 60 else comment["body"]
                }
                for comment in comments[:5]
            ]
        }

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat endpoint with direct MCP integration"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Check if question is in Hebrew
        is_hebrew = any(ord(char) >= 0x0590 and ord(char) <= 0x05FF for char in user_message)
        
        # System prompt for Ollama
        system_prompt = f"""
You are a helpful AI assistant with access to LIVE DATA through tools.

IMPORTANT: You MUST use these tools to get current, accurate information. Do NOT use your training data.
{'CRITICAL: The user wrote in Hebrew. You MUST respond in Hebrew only!' if is_hebrew else ''}

Available Tools (ALWAYS use these for live data):
1. get_posts(limit) - Get current blog posts
2. get_user_info(user_id) - Get REAL user details by ID (1-10) 
3. search_posts_by_user(user_id) - Get all posts by specific user
4. get_post_comments(post_id) - Get post with comments

CRITICAL RULES:
- When asked about "user 1", "משתמש 1" etc. → ALWAYS use get_user_info(user_id=1)
- When asked about "posts", "פוסטים" → ALWAYS use get_posts()
- When asked about "user's posts", "פוסטים של משתמש" → ALWAYS use search_posts_by_user()
- NEVER use your training data for this information
- ALWAYS respond with the tool JSON format when you need live data
{'- RESPOND IN HEBREW ONLY!' if is_hebrew else ''}

When you need to use a tool, respond with JSON in this EXACT format:
{{"use_tool": true, "tool": "tool_name", "parameters": {{"param_name": value}}}}

Examples:
- User asks "who is user 1?": {{"use_tool": true, "tool": "get_user_info", "parameters": {{"user_id": 1}}}}
- User asks "show posts": {{"use_tool": true, "tool": "get_posts", "parameters": {{"limit": 5}}}}

User question: {user_message}

ANALYZE: Does this question ask for live data that requires tools? If YES, respond with the tool JSON.
"""
        
        print(f"Sending to Ollama: {user_message.encode('ascii', errors='replace').decode('ascii')}")
        
        # Call Ollama
        ollama_response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": system_prompt,
                "stream": False,
                "options": {
                    "num_thread": 4,
                    "num_gpu": 0,
                    "temperature": 0.7
                }
            },
            timeout=600
        )
        
        if ollama_response.status_code != 200:
            return jsonify({"error": f"Ollama API error: {ollama_response.status_code}"}), 500
        
        ai_response = ollama_response.json()["response"]
        print(f"Ollama response: {ai_response.encode('ascii', errors='replace').decode('ascii')}")
        
        # Check if Ollama wants to use a tool
        if '"use_tool": true' in ai_response:
            try:
                import json
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    tool_request_text = ai_response[json_start:json_end]
                    tool_request = json.loads(tool_request_text)
                    
                    if tool_request.get("use_tool"):
                        tool_name = tool_request.get("tool")
                        parameters = tool_request.get("parameters", {})
                        
                        print(f"Using tool: {tool_name} with parameters: {parameters}")
                        
                        # Execute tool directly (no MCP stdio)
                        tool_result = None
                        if tool_name == "get_posts":
                            limit = parameters.get("limit", 10)
                            tool_result = asyncio.run(get_posts_tool(limit))
                        elif tool_name == "get_user_info":
                            user_id = parameters.get("user_id")
                            if user_id:
                                tool_result = asyncio.run(get_user_info_tool(user_id))
                        elif tool_name == "search_posts_by_user":
                            user_id = parameters.get("user_id")
                            if user_id:
                                tool_result = asyncio.run(search_posts_by_user_tool(user_id))
                        elif tool_name == "get_post_comments":
                            post_id = parameters.get("post_id")
                            if post_id:
                                tool_result = asyncio.run(get_post_comments_tool(post_id))
                        
                        if tool_result:
                            print(f"Tool result: {tool_result}")
                            
                            # Send result back to Ollama
                            final_prompt = f"""
The user asked {'in Hebrew' if is_hebrew else ''}: "{user_message}"

I used the tool {tool_name} with parameters {parameters}
The result was: {json.dumps(tool_result, ensure_ascii=False)}

{'IMPORTANT: The user asked in Hebrew, so you MUST respond in Hebrew.' if is_hebrew else ''}
Please provide a helpful and natural response based on this data.
Format the response nicely and explain what you found.
{'התשובה שלך חייבת להיות בעברית!' if is_hebrew else ''}
"""
                            
                            final_response = requests.post(
                                f"{OLLAMA_API_URL}/api/generate",
                                json={
                                    "model": OLLAMA_MODEL,
                                    "prompt": final_prompt,
                                    "stream": False,
                                    "options": {
                                        "num_thread": 4,
                                        "num_gpu": 0,
                                        "temperature": 0.7
                                    }
                                },
                                timeout=600
                            )
                            
                            if final_response.status_code == 200:
                                final_answer = final_response.json()["response"]
                                return jsonify({
                                    "success": True,
                                    "message": final_answer,
                                    "tool_used": tool_name,
                                    "tool_result": tool_result
                                })
            
            except Exception as e:
                print(f"Error using tool: {e}")
        
        # Regular response without tools
        return jsonify({
            "success": True,
            "message": ai_response,
            "tool_used": None
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_available_tools():
    """Get available tools"""
    tools = {
        "get_posts": "Get blog posts with limit parameter",
        "get_user_info": "Get user information by user_id",
        "search_posts_by_user": "Get all posts by specific user_id",
        "get_post_comments": "Get post with comments by post_id"
    }
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Simple MCP Gateway - Direct Integration",
        "architecture": "HTML Client -> Flask Gateway -> Direct Tools -> JSONPlaceholder API",
        "status": "running"
    })

if __name__ == '__main__':
    print("Starting Simple MCP Gateway...")
    print("Architecture: HTTP <-> Direct MCP Tools <-> JSONPlaceholder API")
    
    try:
        # Test Ollama connection
        test_response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("[OK] Ollama connection verified")
        
        print("[INFO] Server starting on http://localhost:3001")
        app.run(host='0.0.0.0', port=3001, debug=True)
        
    except Exception as e:
        print(f"[ERROR] Failed to start: {e}")