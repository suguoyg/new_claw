#!/usr/bin/env python3
"""
NewClaw Integration Test Script
Tests the backend API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n[TEST] Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("  ✓ Health check passed")
        return True
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False

def test_auth_register():
    """Test user registration"""
    print("\n[TEST] User Registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": "testuser",
            "password": "testpass123"
        })
        data = response.json()
        if data.get("code") == 0:
            print("  ✓ Registration passed")
            return True
        else:
            print(f"  ✗ Registration failed: {data.get('message')}")
            return False
    except Exception as e:
        print(f"  ✗ Registration failed: {e}")
        return False

def test_auth_login():
    """Test user login"""
    print("\n[TEST] User Login...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        data = response.json()
        if data.get("code") == 0 and "token" in data.get("data", {}):
            print("  ✓ Login passed")
            return data["data"]["token"]
        else:
            print(f"  ✗ Login failed")
            return None
    except Exception as e:
        print(f"  ✗ Login failed: {e}")
        return None

def test_agents(token):
    """Test agents endpoints"""
    print("\n[TEST] Agents API...")
    headers = {"Authorization": f"Bearer {token}"}

    # List agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
        if response.status_code == 200:
            print("  ✓ List agents passed")
        else:
            print(f"  ✗ List agents failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ List agents failed: {e}")
        return False

    # Create agent
    try:
        response = requests.post(f"{BASE_URL}/api/agents", headers=headers, json={
            "name": "Test Agent",
            "description": "A test agent",
            "dialog_model": {
                "provider": "ollama",
                "model_name": "llama2"
            }
        })
        data = response.json()
        if data.get("code") == 0:
            agent_id = data["data"]["agent_id"]
            print(f"  ✓ Create agent passed (ID: {agent_id})")
            return agent_id
        else:
            print(f"  ✗ Create agent failed")
            return None
    except Exception as e:
        print(f"  ✗ Create agent failed: {e}")
        return None

def test_skills(token):
    """Test skills endpoints"""
    print("\n[TEST] Skills API...")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/skills", headers=headers)
        if response.status_code == 200:
            print("  ✓ List skills passed")
            return True
        else:
            print(f"  ✗ List skills failed")
            return False
    except Exception as e:
        print(f"  ✗ List skills failed: {e}")
        return False

def test_memory(token):
    """Test memory endpoints"""
    print("\n[TEST] Memory API...")
    headers = {"Authorization": f"Bearer {token}"}

    # Create memory
    try:
        response = requests.post(f"{BASE_URL}/api/memory", headers=headers, json={
            "title": "Test Memory",
            "content": "This is a test memory",
            "type": "private"
        })
        data = response.json()
        if data.get("code") == 0:
            memory_id = data["data"]["memory_id"]
            print(f"  ✓ Create memory passed (ID: {memory_id})")
            return True
        else:
            print(f"  ✗ Create memory failed")
            return False
    except Exception as e:
        print(f"  ✗ Create memory failed: {e}")
        return False

def test_models(token):
    """Test models endpoints"""
    print("\n[TEST] Models API...")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/models", headers=headers)
        if response.status_code == 200:
            print("  ✓ List models passed")
            return True
        else:
            print(f"  ✗ List models failed")
            return False
    except Exception as e:
        print(f"  ✗ List models failed: {e}")
        return False

def test_files(token):
    """Test file upload"""
    print("\n[TEST] Files API...")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Create a test file
        files = {"file": ("test.txt", b"Hello, World!", "text/plain")}
        response = requests.post(f"{BASE_URL}/api/files/upload", headers=headers, files=files)
        data = response.json()
        if data.get("code") == 0:
            file_id = data["data"]["file_id"]
            print(f"  ✓ File upload passed (ID: {file_id})")
            return file_id
        else:
            print(f"  ✗ File upload failed")
            return None
    except Exception as e:
        print(f"  ✗ File upload failed: {e}")
        return None

def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("NewClaw Integration Tests")
    print("=" * 50)

    results = {}

    # Test health
    results["health"] = test_health()

    # Test auth
    results["register"] = test_auth_register()
    token = test_auth_login()
    results["login"] = token is not None

    if not token:
        print("\n⚠️ Skipping authenticated tests (no token)")
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        for test, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test}: {status}")
        return

    # Test authenticated endpoints
    results["agents"] = test_agents(token) is not None
    results["skills"] = test_skills(token)
    results["memory"] = test_memory(token)
    results["models"] = test_models(token)
    results["files"] = test_files(token) is not None

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    run_all_tests()
