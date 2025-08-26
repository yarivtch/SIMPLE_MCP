import asyncio
import json
import subprocess
import threading
import queue
import time
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "aya"

class MCPGateway:
    """Gateway שמתרגם HTTP ל-MCP stdio protocol"""
    
    def __init__(self, mcp_command, mcp_args):
        self.mcp_command = mcp_command
        self.mcp_args = mcp_args
        self.process = None
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = False
        self.request_id_map = {}  # מיפוי בין request IDs לresponse handlers
        
    def start(self):
        """הפעלת MCP Server subprocess"""
        print(f"Starting MCP Server: {self.mcp_command} {' '.join(self.mcp_args)}")
        
        self.process = subprocess.Popen(
            [self.mcp_command] + self.mcp_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        self.running = True
        
        # Threads לתקשורת
        self.writer_thread = threading.Thread(target=self._write_requests, daemon=True)
        self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        
        self.writer_thread.start()
        self.reader_thread.start()
        
        # אתחול MCP connection
        self._initialize_mcp()
        
    def _initialize_mcp(self):
        """אתחול חיבור MCP"""
        print("Initializing MCP connection...")
        
        # Initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mcp-gateway",
                    "version": "1.0.0"
                }
            }
        }
        
        self.request_queue.put(json.dumps(init_request))
        
        # Wait for initialize response
        time.sleep(2)
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        self.request_queue.put(json.dumps(initialized))
        print("MCP initialization completed")
    
    def _write_requests(self):
        """Thread לכתיבת requests לMCP Server"""
        while self.running:
            try:
                request = self.request_queue.get(timeout=1)
                if self.process and self.process.stdin:
                    self.process.stdin.write(request + '\n')
                    self.process.stdin.flush()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing to MCP server: {e}")
                break
    
    def _read_responses(self):
        """Thread לקריאת responses מMCP Server"""
        while self.running:
            try:
                if self.process and self.process.stdout:
                    line = self.process.stdout.readline()
                    if line.strip():
                        self.response_queue.put(line.strip())
                    elif self.process.poll() is not None:
                        # Process ended
                        break
            except Exception as e:
                print(f"Error reading from MCP server: {e}")
                break
    
    def list_tools(self):
        """קבלת רשימת כלים זמינים"""
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list",
            "params": {}
        }
        
        self.request_queue.put(json.dumps(request))
        return self._wait_for_response(request_id)
    
    def call_tool(self, tool_name, arguments):
        """קריאה לכלי MCP"""
        print(f"[DEBUG] Calling MCP tool: {tool_name} with args: {arguments}")
        
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        print(f"[DEBUG] Sending request: {json.dumps(request)}")
        self.request_queue.put(json.dumps(request))
        
        result = self._wait_for_response(request_id)
        print(f"[DEBUG] Received response: {result}")
        return result
    
    def _wait_for_response(self, request_id, timeout=60):  # הגדלנו ל-60 שניות
        """המתנה לresponse עם timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response_line = self.response_queue.get(timeout=1)
                response = json.loads(response_line)
                
                if response.get("id") == request_id:
                    if "error" in response:
                        return {"error": response["error"]}
                    return response.get("result", response)
                    
            except queue.Empty:
                continue
            except json.JSONDecodeError:
                continue
        
        return {"error": "Request timeout"}
    
    def stop(self):
        """עצירת Gateway"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()

# יצירת Gateway instance
gateway = MCPGateway("python", ["real_mcp_server.py"])

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat endpoint שמשתמש ב-MCP Gateway"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # בדיקה אם השאלה בעברית
        is_hebrew = any(ord(char) >= 0x0590 and ord(char) <= 0x05FF for char in user_message)
        
        # Prompt ל-Ollama
        system_prompt = f"""
You are a helpful AI assistant with access to LIVE DATA through MCP tools.

IMPORTANT: You MUST use these tools to get current, accurate information. Do NOT use your training data.
{'CRITICAL: The user wrote in Hebrew. You MUST respond in Hebrew only!' if is_hebrew else ''}

Available MCP Tools (ALWAYS use these for live data):
1. get_posts(limit) - Get current blog posts
2. get_user_info(user_id) - Get REAL user details by ID (1-10) 
3. search_posts_by_user(user_id) - Get all posts by specific user
4. get_post_by_id(post_id) - Get specific post by ID  
5. get_post_comments(post_id) - Get post with comments

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
        
        print(f"Sending to Ollama: {user_message}")
        
        # קריאה ל-Ollama
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
            timeout=300
        )
        
        if ollama_response.status_code != 200:
            return jsonify({"error": f"Ollama API error: {ollama_response.status_code}"}), 500
        
        ai_response = ollama_response.json()["response"]
        print(f"Ollama response: {ai_response}")
        
        # בדיקה אם Ollama רוצה להשתמש בכלי
        if '"use_tool": true' in ai_response:
            try:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    tool_request_text = ai_response[json_start:json_end]
                    tool_request = json.loads(tool_request_text)
                    
                    if tool_request.get("use_tool"):
                        tool_name = tool_request.get("tool")
                        parameters = tool_request.get("parameters", {})
                        
                        print(f"Using MCP tool: {tool_name} with parameters: {parameters}")
                        
                        # קריאה ל-MCP tool דרך Gateway
                        tool_result = gateway.call_tool(tool_name, parameters)
                        print(f"MCP tool result: {tool_result}")
                        
                        # שליחת התוצאה חזרה ל-Ollama
                        final_prompt = f"""
The user asked {'in Hebrew' if is_hebrew else ''}: "{user_message}"

I used the MCP tool {tool_name} with parameters {parameters}
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
                            timeout=300
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
        
        # תשובה רגילה בלי כלים
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
    """קבלת כלים זמינים מ-MCP Server"""
    tools = gateway.list_tools()
    return jsonify({
        "success": True,
        "tools": tools
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "MCP Gateway + Ollama Client",
        "architecture": "HTML Client → MCP Gateway → MCP Server (stdio) → JSONPlaceholder API",
        "status": "running"
    })

if __name__ == '__main__':
    print("Starting MCP Gateway + Ollama Client...")
    print("Architecture: HTTP ↔ MCP Gateway ↔ MCP Server (stdio)")
    
    # הפעלת MCP Gateway
    try:
        gateway.start()
        print("✅ MCP Gateway connected to server")
        
        # בדיקת Ollama
        test_response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("✅ Ollama connection verified")
        
        print("🌐 Server starting on http://localhost:3000")
        app.run(host='0.0.0.0', port=3000, debug=True)
        
    except Exception as e:
        print(f"❌ Failed to start: {e}")
    finally:
        gateway.stop()