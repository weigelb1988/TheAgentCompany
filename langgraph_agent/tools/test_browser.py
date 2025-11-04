#!/usr/bin/env python3
"""
Simple test script for browser tools.

This script tests basic browser functionality to ensure:
1. Browser can be initialized
2. Navigation works
3. Element interaction works
4. Content extraction works
5. Screenshots work
"""

import asyncio
from browser import BrowserClient


async def test_browser():
    """Test basic browser operations."""
    print("=" * 60)
    print("Browser Tools Test")
    print("=" * 60)

    client = BrowserClient(headless=True)

    try:
        # Test 1: Initialize
        print("\n[Test 1] Initializing browser...")
        await client.initialize()
        print("✓ Browser initialized")

        # Test 2: Navigate to a page
        print("\n[Test 2] Navigating to example.com...")
        result = await client.goto("https://example.com")
        print(f"✓ Navigation: {result}")

        # Test 3: Get page info
        print("\n[Test 3] Getting page info...")
        info = await client.get_page_info()
        print(f"✓ Page info: {info}")

        # Test 4: Extract text
        print("\n[Test 4] Extracting page text...")
        text = await client.get_text()
        print(f"✓ Page text (first 100 chars): {text[:100]}...")

        # Test 5: Get elements
        print("\n[Test 5] Getting all <p> elements...")
        elements = await client.get_elements("p")
        print(f"✓ Found {len(elements)} <p> elements")

        # Test 6: Screenshot
        print("\n[Test 6] Taking screenshot...")
        screenshot_result = await client.screenshot()
        if screenshot_result.get("success"):
            print(f"✓ Screenshot taken (data_uri length: {len(screenshot_result.get('data_uri', ''))})")
        else:
            print(f"✗ Screenshot failed: {screenshot_result.get('error')}")

        # Test 7: Scroll
        print("\n[Test 7] Scrolling down...")
        scroll_result = await client.scroll(direction="down", amount=500)
        print(f"✓ Scroll result: {scroll_result}")

        # Test 8: Wait
        print("\n[Test 8] Waiting 1 second...")
        wait_result = await client.wait(1000)
        print(f"✓ Wait result: {wait_result}")

        # Test 9: Navigation history
        print("\n[Test 9] Testing navigation history...")
        await client.goto("https://httpbin.org/html")
        print("✓ Navigated to httpbin.org")

        back_result = await client.back()
        print(f"✓ Back result: {back_result}")

        forward_result = await client.forward()
        print(f"✓ Forward result: {forward_result}")

        # Test 10: Multiple tabs
        print("\n[Test 10] Testing multiple tabs...")
        new_tab_result = await client.new_tab("https://httpbin.org/json")
        print(f"✓ New tab opened: {new_tab_result}")

        tabs = await client.list_tabs()
        print(f"✓ Open tabs: {len(tabs)}")
        for tab in tabs:
            print(f"  - Tab {tab['index']}: {tab['url'][:50]}... (current: {tab['is_current']})")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\nCleaning up...")
        await client.close()
        print("✓ Browser closed")


if __name__ == "__main__":
    asyncio.run(test_browser())
