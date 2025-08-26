#!/usr/bin/env python3
"""
Direct test of MCP server functionality
"""
import asyncio
from api_server import get_posts, get_user_info

async def test_mcp_tools():
    """Test the MCP tools directly"""
    print("Testing MCP tools directly...")
    print("=" * 50)
    
    try:
        # Test get_posts
        print("1. Testing get_posts(limit=3):")
        posts = await get_posts(limit=3)
        print(f"   Retrieved {len(posts)} posts")
        if posts:
            print(f"   First post: {posts[0]['title']}")
        print()
        
        # Test get_user_info  
        print("2. Testing get_user_info(user_id=1):")
        user = await get_user_info(user_id=1)
        print(f"   User: {user['name']} ({user['email']})")
        print(f"   Company: {user['company']}")
        print()
        
        print("[SUCCESS] All MCP tools working correctly!")
        return True
        
    except Exception as e:
        print(f"[ERROR] MCP tools failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_tools())
    exit(0 if success else 1)