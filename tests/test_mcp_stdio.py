#!/usr/bin/env python3
"""
Test MCP stdio protocol communication
"""
import subprocess
import json
import time

def test_mcp_stdio():
    """Test MCP server through stdio protocol"""
    print("Testing MCP stdio protocol...")
    print("=" * 50)
    
    try:
        # Start MCP server process
        process = subprocess.Popen(
            ["python", "api_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        print("Sending initialize request...")
        request_json = json.dumps(init_request)
        process.stdin.write(request_json + '\n')
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        response_line = process.stdout.readline()
        print(f"Response: {response_line}")
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        print("Sending initialized notification...")
        process.stdin.write(json.dumps(initialized) + '\n')
        process.stdin.flush()
        
        # Test tools/list
        list_request = {
            "jsonrpc": "2.0",
            "id": "list_tools",
            "method": "tools/list",
            "params": {}
        }
        
        print("Requesting tools list...")
        process.stdin.write(json.dumps(list_request) + '\n')
        process.stdin.flush()
        
        # Wait and read response
        time.sleep(2)
        response_line = process.stdout.readline()
        print(f"Tools response: {response_line}")
        
        # Cleanup
        process.terminate()
        process.wait()
        
        print("[SUCCESS] MCP stdio protocol test completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] MCP stdio test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False

if __name__ == "__main__":
    success = test_mcp_stdio()
    exit(0 if success else 1)