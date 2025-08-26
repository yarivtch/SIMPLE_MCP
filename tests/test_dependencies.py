#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed
"""
import sys

def test_imports():
    """Test all required imports"""
    tests = []
    
    # Test Flask
    try:
        import flask
        from flask import Flask, request, jsonify
        from flask_cors import CORS
        tests.append(("[OK] Flask", f"v{flask.__version__}"))
    except ImportError as e:
        tests.append(("[FAIL] Flask", f"FAILED: {e}"))
    
    # Test requests
    try:
        import requests
        tests.append(("[OK] requests", f"v{requests.__version__}"))
    except ImportError as e:
        tests.append(("[FAIL] requests", f"FAILED: {e}"))
    
    # Test httpx
    try:
        import httpx
        tests.append(("[OK] httpx", f"v{httpx.__version__}"))
    except ImportError as e:
        tests.append(("[FAIL] httpx", f"FAILED: {e}"))
    
    # Test MCP
    try:
        import mcp
        from mcp.server.fastmcp import FastMCP
        version = getattr(mcp, '__version__', 'unknown')
        tests.append(("[OK] mcp", f"v{version}"))
    except ImportError as e:
        tests.append(("[FAIL] mcp", f"FAILED: {e}"))
    
    # Test standard library
    std_libs = ['asyncio', 'json', 'subprocess', 'threading', 'queue', 'time', 'uuid', 'typing']
    for lib in std_libs:
        try:
            __import__(lib)
            tests.append(("[OK] " + lib, "standard library"))
        except ImportError as e:
            tests.append(("[FAIL] " + lib, f"FAILED: {e}"))
    
    return tests

def main():
    print("Testing SIMPLE MCP Dependencies")
    print("=" * 50)
    
    tests = test_imports()
    
    failed = 0
    for status, info in tests:
        print(f"{status:<15} {info}")
        if status.startswith("[FAIL]"):
            failed += 1
    
    print("=" * 50)
    
    if failed == 0:
        print("SUCCESS: All dependencies are properly installed!")
        print("Ready to run SIMPLE MCP")
        return 0
    else:
        print(f"WARNING: {failed} dependencies failed to import")
        print("Run: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())