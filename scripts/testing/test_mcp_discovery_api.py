#!/usr/bin/env python3
"""
Test the MCP discovery API endpoints
"""

import json

import requests

API_BASE_URL = "http://localhost:8001"


def test_discover_endpoint():
    """Test the discover endpoint"""
    print("Testing MCP discovery endpoint...")

    # Test without query
    try:
        response = requests.get(f"{API_BASE_URL}/api/mcp/discover")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Total MCPs: {data.get('total')}")
            if data.get("mcps"):
                print("\nAvailable MCPs:")
                for mcp in data["mcps"][:3]:  # Show first 3
                    print(f"  - {mcp['name']}: {mcp['description']}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server at http://localhost:8001")
        print("   Make sure the API server is running:")
        print("   cd elf_automations/api && python control_center_minimal.py")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    # Test with query
    print("\n\nTesting with search query 'google docs'...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/mcp/discover", params={"query": "google docs"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('total')} MCPs matching 'google docs'")
            for mcp in data.get("mcps", []):
                print(f"  - {mcp['name']}: {mcp['description']}")
    except Exception as e:
        print(f"Error: {e}")

    return True


def test_health_endpoint():
    """Test if API is running"""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        return False


if __name__ == "__main__":
    print("MCP Discovery API Test\n" + "=" * 50 + "\n")

    if test_health_endpoint():
        print("\n")
        test_discover_endpoint()
    else:
        print("\nPlease start the API server first:")
        print("cd elf_automations/api && python control_center_minimal.py")
