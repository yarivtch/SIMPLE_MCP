import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Ollama API Configuration
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "aya"  # נשנה את זה לפי מה שיש לך

class MCPToolsCaller:
    """מחלקה שמנהלת קריאות לכלים של MCP Server"""
    
    def __init__(self):
        self.available_tools = {
            "get_posts": {
                "description": "Get a list of blog posts",
                "parameters": ["limit"]
            },
            "get_user_info": {
                "description": "Get user information by ID", 
                "parameters": ["user_id"]
            },
            "get_post_by_id": {
                "description": "Get specific post by ID",
                "parameters": ["post_id"]
            },
            "search_posts_by_user": {
                "description": "Get all posts by specific user",
                "parameters": ["user_id"]
            },
            "get_post_comments": {
                "description": "Get post with its comments",
                "parameters": ["post_id"]
            }
        }
    
    def call_tool(self, tool_name, **kwargs):
        """קריאה ישירה לפונקציות MCP (גרסה sync)"""
        BASE_URL = "https://jsonplaceholder.typicode.com"
        
        try:
            if tool_name == "get_posts":
                limit = kwargs.get("limit", 10)
                response = requests.get(f"{BASE_URL}/posts", timeout=10)
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
            
            elif tool_name == "get_user_info":
                user_id = kwargs.get("user_id")
                response = requests.get(f"{BASE_URL}/users/{user_id}", timeout=10)
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
            
            elif tool_name == "get_post_by_id":
                post_id = kwargs.get("post_id")
                response = requests.get(f"{BASE_URL}/posts/{post_id}", timeout=10)
                response.raise_for_status()
                post = response.json()
                
                return {
                    "id": post["id"],
                    "title": post["title"], 
                    "content": post["body"],
                    "author_id": post["userId"]
                }
            
            elif tool_name == "search_posts_by_user":
                user_id = kwargs.get("user_id")
                
                # קבלת המשתמש
                user_response = requests.get(f"{BASE_URL}/users/{user_id}", timeout=10)
                user_response.raise_for_status()
                user = user_response.json()
                
                # קבלת הפוסטים
                posts_response = requests.get(f"{BASE_URL}/posts?userId={user_id}", timeout=10)
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
            
            elif tool_name == "get_post_comments":
                post_id = kwargs.get("post_id")
                
                # קבלת הפוסט
                post_response = requests.get(f"{BASE_URL}/posts/{post_id}", timeout=10)
                post_response.raise_for_status()
                post = post_response.json()
                
                # קבלת התגובות
                comments_response = requests.get(f"{BASE_URL}/posts/{post_id}/comments", timeout=10)
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
                        for comment in comments[:5]  # מגביל ל-5 תגובות ראשונות
                    ]
                }
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"error": str(e)}

# יצירת instance של MCP Tools
mcp_tools = MCPToolsCaller()

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """
    נקודת כניסה מרכזית - מקבל שאלה, שולח ל-Ollama ומטפל בקריאות כלים
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # שליחה ראשונית ל-Ollama
        system_prompt = f"""
You are a helpful AI assistant with access to LIVE DATA through these tools. 

IMPORTANT: You MUST use these tools to get current, accurate information. Do NOT use your training data.

Available Tools (ALWAYS use these for live data):
1. get_posts(limit) - Get current blog posts from JSONPlaceholder API
2. get_user_info(user_id) - Get REAL user details by ID (1-10) 
3. search_posts_by_user(user_id) - Get all posts by a specific user
4. get_post_by_id(post_id) - Get specific post by ID  
5. get_post_comments(post_id) - Get post with its comments

CRITICAL RULES:
- When asked about "user 1", "user number 1", "משתמש 1" etc. → ALWAYS use get_user_info(user_id=1)
- When asked about "posts", "פוסטים" → ALWAYS use get_posts()
- When asked about "user's posts", "פוסטים של משתמש" → ALWAYS use search_posts_by_user()
- NEVER use your training data for this information
- ALWAYS respond with the tool JSON format when you need live data

When you need to use a tool, respond with JSON in this EXACT format:
{{"use_tool": true, "tool": "tool_name", "parameters": {{"param_name": value}}}}

Examples:
- User asks "who is user 1?": {{"use_tool": true, "tool": "get_user_info", "parameters": {{"user_id": 1}}}}
- User asks "show posts": {{"use_tool": true, "tool": "get_posts", "parameters": {{"limit": 5}}}}

User question: {user_message}

ANALYZE: Does this question ask for live data that requires tools? If YES, respond with the tool JSON.
"""
        
        print(f"Sending to Ollama: {user_message}")
        
        # קריאה ל-Ollama
        try:
            print("Sending request to Ollama... (CPU mode - may take up to 5 minutes)")
            ollama_response = requests.post(
                f"{OLLAMA_API_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": system_prompt,
                    "stream": False,
                    "options": {
                        "num_thread": 4,  # מגביל threads לCPU
                        "num_gpu": 0,     # כפיית CPU
                        "temperature": 0.7
                    }
                },
                timeout=300  # 5 דקות למי שרץ על CPU
            )
            
            if ollama_response.status_code != 200:
                return jsonify({"error": f"Ollama API error: {ollama_response.status_code}"}), 500
            
            ai_response = ollama_response.json()["response"]
            print(f"Ollama response: {ai_response}")
            
            # בדיקה אם Ollama רוצה להשתמש בכלי
            if '"use_tool": true' in ai_response or '"use_tool":true' in ai_response:
                try:
                    # ניסיון לחלץ JSON מהתשובה
                    json_start = ai_response.find("{")
                    json_end = ai_response.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        tool_request_text = ai_response[json_start:json_end]
                        print(f"Extracted JSON: {tool_request_text}")
                        
                        tool_request = json.loads(tool_request_text)
                        
                        if tool_request.get("use_tool"):
                            tool_name = tool_request.get("tool")
                            parameters = tool_request.get("parameters", {})
                            
                            print(f"Using tool: {tool_name} with parameters: {parameters}")
                            
                            # קריאה לכלי MCP
                            tool_result = mcp_tools.call_tool(tool_name, **parameters)
                            print(f"Tool result: {tool_result}")
                            
                            # שליחת התוצאה חזרה ל-Ollama ליצירת תשובה סופית
                            final_prompt = f"""
The user asked in Hebrew: "{user_message}"

I used the tool {tool_name} with parameters {parameters}
The result was: {json.dumps(tool_result, ensure_ascii=False)}

IMPORTANT: The user asked in Hebrew, so you MUST respond in Hebrew.
Please provide a helpful and natural response in Hebrew based on this data.
Format the response nicely and explain what you found.

התשובה שלך חייבת להיות בעיה בעברית !
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
                                timeout=300  # 5 דקות
                            )
                            
                            if final_response.status_code == 200:
                                final_answer = final_response.json()["response"]
                                return jsonify({
                                    "success": True,
                                    "message": final_answer,
                                    "tool_used": tool_name,
                                    "tool_result": tool_result
                                })
                
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"Error parsing tool request: {e}")
                    pass  # אם לא הצלחנו לחלץ JSON, נמשיך עם התשובה הרגילה
            
            # תשובה רגילה בלי כלים
            return jsonify({
                "success": True,
                "message": ai_response,
                "tool_used": None
            })
            
        except requests.exceptions.RequestException as e:
            print(f"Ollama connection error: {e}")
            return jsonify({"error": f"Cannot connect to Ollama: {str(e)}"}), 500
            
    except Exception as e:
        print(f"General error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_available_tools():
    """החזרת רשימת כלים זמינים"""
    return jsonify({
        "success": True,
        "tools": mcp_tools.available_tools
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "MCP-Ollama Client API",
        "endpoints": {
            "POST /api/chat": "Chat with AI using MCP tools",
            "GET /api/tools": "Get available tools"
        },
        "status": "running"
    })

if __name__ == '__main__':
    print("🚀 MCP-Ollama Client Starting...")
    print(f"🧠 Using Ollama model: {OLLAMA_MODEL}")
    print("🔌 MCP Tools integrated")
    print("🌐 Server starting on http://localhost:3000")
    print()
    print("Test with:")
    print('curl -X POST http://localhost:3000/api/chat -H "Content-Type: application/json" -d "{\\"message\\": \\"show me 3 posts\\"}"')
    print()
    
    # בדיקה שOllama זמין
    try:
        test_response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("✅ Ollama connection verified!")
            
            # ניסיון לטעון את המודל מראש
            print(f"🔄 Pre-loading model {OLLAMA_MODEL}...")
            preload_response = requests.post(
                f"{OLLAMA_API_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "Hi",
                    "stream": False
                },
                timeout=60
            )
            if preload_response.status_code == 200:
                print("✅ Model loaded successfully!")
            else:
                print("⚠️  Model preload failed, but continuing...")
                
        else:
            print("⚠️  Ollama may not be running properly")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
    
    app.run(host='0.0.0.0', port=3000, debug=True)