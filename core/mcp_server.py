#!/usr/bin/env python3
"""
SIMPLE MCP - MCP Server (Core Component)

Purpose: Real MCP (Model Context Protocol) server implementation
Technology: FastMCP framework with asyncio
API: JSONPlaceholder (https://jsonplaceholder.typicode.com)

This is the CORE MCP server that provides real tools to AI agents.
It implements the official MCP protocol and connects to external APIs.

Tools Available:
- get_posts(limit) - Get blog posts from JSONPlaceholder
- get_user_info(user_id) - Get user information  
- search_posts_by_user(user_id) - Get posts by specific user
- get_post_by_id(post_id) - Get specific post
- get_post_comments(post_id) - Get post with comments

Created: 2025-08-26
Author: SIMPLE MCP Project
Status: PRODUCTION READY ✅
"""

import asyncio
import httpx
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

# Initialize MCP Server with FastMCP framework
mcp = FastMCP("jsonplaceholder-api")

# Base URL for JSONPlaceholder API
BASE_URL = "https://jsonplaceholder.typicode.com"

@mcp.tool()
async def get_posts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get blog posts from JSONPlaceholder API
    
    Args:
        limit: Maximum number of posts to return (default: 10)
    
    Returns:
        List of posts with id, title, content, and author_id
    """
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

@mcp.tool()
async def get_post_by_id(post_id: int) -> Dict[str, Any]:
    """
    Get specific post by ID
    
    Args:
        post_id: Post ID to retrieve
    
    Returns:
        Post details with full content
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/posts/{post_id}")
        response.raise_for_status()
        post = response.json()
        
        return {
            "id": post["id"],
            "title": post["title"], 
            "content": post["body"],
            "author_id": post["userId"]
        }

@mcp.tool() 
async def get_user_info(user_id: int) -> Dict[str, Any]:
    """
    Get user information by ID
    
    Args:
        user_id: User ID to retrieve (1-10 available)
    
    Returns:
        User details including name, email, company, and location
    """
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

@mcp.tool()
async def search_posts_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all posts by specific user
    
    Args:
        user_id: User ID to search for
    
    Returns:
        User info and all their posts
    """
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

@mcp.tool()
async def get_post_comments(post_id: int) -> Dict[str, Any]:
    """
    Get post with its comments
    
    Args:
        post_id: Post ID to get comments for
    
    Returns:
        Post details with all comments
    """
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
                for comment in comments[:5]  # Limit to 5 comments
            ]
        }

# MCP Resource - API Information
@mcp.resource("api://info")
def get_api_info() -> str:
    """
    Information about the JSONPlaceholder API
    """
    return """
    JSONPlaceholder API Information:
    
    Base URL: https://jsonplaceholder.typicode.com
    Description: Free fake API for testing and prototyping
    
    Available Endpoints:
    • Posts: 100 sample blog posts
    • Users: 10 sample users  
    • Comments: 500 comments on posts
    
    Tools Available:
    1. get_posts() - Get list of posts
    2. get_post_by_id() - Get specific post
    3. get_user_info() - Get user details
    4. search_posts_by_user() - Find user's posts
    5. get_post_comments() - Get post with comments
    """

if __name__ == "__main__":
    print("[START] SIMPLE MCP Server Starting...")
    print("[API] Connecting to JSONPlaceholder API...")
    print("[TOOLS] MCP Tools: get_posts, get_user_info, search_posts_by_user, get_post_comments")
    print("[PROTOCOL] MCP stdio transport")
    print("[READY] Server ready!")
    
    # Run MCP server with stdio transport
    mcp.run(transport='stdio')