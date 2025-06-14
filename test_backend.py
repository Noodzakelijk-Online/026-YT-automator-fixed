#!/usr/bin/env python3
"""
Test script for YouTube Automator Unified Backend
Tests basic functionality without requiring authentication
"""

import requests
import json
import sys
import time

API_BASE_URL = "http://localhost:5000/api"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_auth_status():
    """Test authentication status endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/auth/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Auth status endpoint working")
            print(f"  Authenticated: {data.get('authenticated')}")
            return True
        else:
            print(f"✗ Auth status failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Auth status failed: {e}")
        return False

def test_metadata_generation():
    """Test metadata generation endpoint"""
    try:
        test_data = {
            "text": "This is a test video about web development and programming tutorials",
            "topic": "Web Development Tutorial",
            "audience": "developers",
            "style": "educational"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/metadata/generate",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Metadata generation working")
            print(f"  Generated title: {data.get('title', 'N/A')[:50]}...")
            print(f"  Generated tags: {len(data.get('tags', []))} tags")
            return True
        else:
            print(f"✗ Metadata generation failed: {response.status_code}")
            if response.text:
                print(f"  Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Metadata generation failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("YouTube Automator Unified - Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Authentication Status", test_auth_status),
        ("Metadata Generation", test_metadata_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

