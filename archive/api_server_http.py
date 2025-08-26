#!/usr/bin/env python3
"""
MCP Server with HTTP transport instead of stdio
"""
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

# יצירת MCP Server עם HTTP transport
mcp = FastMCP("jsonplaceholder-api")

# Base URL לAPI
BASE_URL = "https://jsonplaceholder.typicode.com"

@mcp.tool()
async def get_posts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    קבלת רשימה של פוסטים מהבלוג
    
    Args:
        limit: מספר מקסימלי של פוסטים (ברירת מחדל: 10)
    
    Returns:
        רשימה של פוסטים עם title, body, userId
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/posts")
        response.raise_for_status()
        posts = response.json()
        
        # מגביל למספר הנדרש
        limited_posts = posts[:limit]
        
        # מנקה הנתונים לפורמט פשוט יותר
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
    קבלת פוסט ספציפי לפי ID
    
    Args:
        post_id: מזהה הפוסט
    
    Returns:
        פרטי הפוסט המבוקש
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
    קבלת מידע על משתמש לפי ID
    
    Args:
        user_id: מזהה המשתמש
    
    Returns:
        פרטי המשתמש
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
    חיפוש כל הפוסטים של משתמש מסוים
    
    Args:
        user_id: מזהה המשתמש
    
    Returns:
        רשימת פוסטים של המשתמש
    """
    async with httpx.AsyncClient() as client:
        # קודם נקבל את פרטי המשתמש
        user_response = await client.get(f"{BASE_URL}/users/{user_id}")
        user_response.raise_for_status()
        user = user_response.json()
        
        # עכשיו נקבל את הפוסטים שלו
        posts_response = await client.get(f"{BASE_URL}/posts?userId={user_id}")
        posts_response.raise_for_status()
        posts = posts_response.json()
        
        # נשלב את המידע
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
    קבלת תגובות לפוסט מסוים
    
    Args:
        post_id: מזהה הפוסט
    
    Returns:
        הפוסט והתגובות שלו
    """
    async with httpx.AsyncClient() as client:
        # קבלת הפוסט
        post_response = await client.get(f"{BASE_URL}/posts/{post_id}")
        post_response.raise_for_status()
        post = post_response.json()
        
        # קבלת התגובות
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
                for comment in comments[:5]  # מגביל ל-5 תגובות ראשונות
            ]
        }

if __name__ == "__main__":
    print("MCP Server Starting - HTTP Mode")
    print("Server will be available at http://localhost:8000/mcp")
    mcp.run(transport='streamable-http', mount_path='/mcp')