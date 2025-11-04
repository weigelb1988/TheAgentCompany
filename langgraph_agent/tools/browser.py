"""
Browser interaction client using Playwright.

This module provides browser automation capabilities for web interactions,
including navigation, element interaction, content extraction, and screenshots.
"""

import asyncio
import base64
from typing import Dict, Any, List, Optional, Tuple
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
)


class BrowserClient:
    """
    Browser automation client using Playwright.

    Provides methods for:
    - Navigation (goto, back, forward, refresh)
    - Element interaction (click, type, fill, select)
    - Content extraction (text, html, attributes)
    - Screenshots and page analysis
    - Tab management
    """

    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout: int = 30000,
    ):
        """
        Initialize browser client.

        Args:
            headless: Run browser in headless mode
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            timeout: Default timeout for operations (milliseconds)
        """
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.default_timeout = timeout

        # Playwright components
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # State tracking
        self._initialized = False
        self._current_url = ""
        self._pages: List[Page] = []

    async def initialize(self):
        """Initialize the browser and create a new page."""
        if self._initialized:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.default_timeout)
        self._pages = [self._page]

        self._initialized = True

    async def _ensure_initialized(self):
        """Ensure browser is initialized before operations."""
        if not self._initialized:
            await self.initialize()

    # ==================== Navigation ====================

    async def goto(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: Wait until this event ('load', 'domcontentloaded', 'networkidle')

        Returns:
            Response information
        """
        await self._ensure_initialized()

        try:
            response = await self._page.goto(url, wait_until=wait_until)
            self._current_url = self._page.url

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None,
            }
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout navigating to {url}",
                "url": self._page.url,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to navigate: {str(e)}",
                "url": self._page.url,
            }

    async def back(self) -> Dict[str, Any]:
        """Navigate back in history."""
        await self._ensure_initialized()

        try:
            await self._page.go_back(wait_until="load")
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def forward(self) -> Dict[str, Any]:
        """Navigate forward in history."""
        await self._ensure_initialized()

        try:
            await self._page.go_forward(wait_until="load")
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def refresh(self) -> Dict[str, Any]:
        """Refresh the current page."""
        await self._ensure_initialized()

        try:
            await self._page.reload(wait_until="load")
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Element Interaction ====================

    async def click(self, selector: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Click an element.

        Args:
            selector: CSS selector or text selector
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.click(selector, timeout=timeout or self.default_timeout)
            return {"success": True, "selector": selector}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def type_text(
        self, selector: str, text: str, delay: int = 0, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Type text into an element (doesn't clear first).

        Args:
            selector: CSS selector
            text: Text to type
            delay: Delay between keystrokes in milliseconds
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.type(
                selector, text, delay=delay, timeout=timeout or self.default_timeout
            )
            return {"success": True, "selector": selector, "text": text}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def fill(
        self, selector: str, value: str, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fill an input element (clears first, then types).

        Args:
            selector: CSS selector
            value: Value to fill
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.fill(selector, value, timeout=timeout or self.default_timeout)
            return {"success": True, "selector": selector, "value": value}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def select_option(
        self, selector: str, value: str, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Select an option from a dropdown.

        Args:
            selector: CSS selector for the select element
            value: Value or label to select
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.select_option(
                selector, value, timeout=timeout or self.default_timeout
            )
            return {"success": True, "selector": selector, "value": value}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def press(
        self, selector: str, key: str, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Press a key on an element.

        Args:
            selector: CSS selector
            key: Key to press (e.g., 'Enter', 'Escape', 'ArrowDown')
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.press(selector, key, timeout=timeout or self.default_timeout)
            return {"success": True, "selector": selector, "key": key}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def hover(self, selector: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Hover over an element.

        Args:
            selector: CSS selector
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.hover(selector, timeout=timeout or self.default_timeout)
            return {"success": True, "selector": selector}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for element: {selector}",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def scroll(
        self, direction: str = "down", amount: int = 500
    ) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction: 'up', 'down', 'left', 'right'
            amount: Scroll amount in pixels

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            if direction == "down":
                await self._page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self._page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "right":
                await self._page.evaluate(f"window.scrollBy({amount}, 0)")
            elif direction == "left":
                await self._page.evaluate(f"window.scrollBy(-{amount}, 0)")
            else:
                return {"success": False, "error": f"Invalid direction: {direction}"}

            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Content Extraction ====================

    async def get_text(self, selector: Optional[str] = None) -> str:
        """
        Get text content from an element or the entire page.

        Args:
            selector: CSS selector (if None, returns all page text)

        Returns:
            Text content
        """
        await self._ensure_initialized()

        try:
            if selector:
                element = await self._page.query_selector(selector)
                if element:
                    return await element.text_content()
                return ""
            else:
                return await self._page.inner_text("body")
        except Exception:
            return ""

    async def get_html(self, selector: Optional[str] = None) -> str:
        """
        Get HTML content from an element or the entire page.

        Args:
            selector: CSS selector (if None, returns all page HTML)

        Returns:
            HTML content
        """
        await self._ensure_initialized()

        try:
            if selector:
                element = await self._page.query_selector(selector)
                if element:
                    return await element.inner_html()
                return ""
            else:
                return await self._page.content()
        except Exception:
            return ""

    async def get_attribute(
        self, selector: str, attribute: str
    ) -> Optional[str]:
        """
        Get an attribute value from an element.

        Args:
            selector: CSS selector
            attribute: Attribute name

        Returns:
            Attribute value or None
        """
        await self._ensure_initialized()

        try:
            element = await self._page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
            return None
        except Exception:
            return None

    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get current page information.

        Returns:
            Page information
        """
        await self._ensure_initialized()

        return {
            "url": self._page.url,
            "title": await self._page.title(),
        }

    async def get_elements(self, selector: str) -> List[Dict[str, Any]]:
        """
        Get all elements matching a selector.

        Args:
            selector: CSS selector

        Returns:
            List of element information
        """
        await self._ensure_initialized()

        try:
            elements = await self._page.query_selector_all(selector)
            result = []

            for i, element in enumerate(elements):
                text = await element.text_content()
                tag = await element.evaluate("el => el.tagName.toLowerCase()")
                result.append({
                    "index": i,
                    "tag": tag,
                    "text": text.strip() if text else "",
                })

            return result
        except Exception as e:
            return []

    async def wait_for_selector(
        self, selector: str, state: str = "visible", timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wait for an element to reach a certain state.

        Args:
            selector: CSS selector
            state: 'attached', 'detached', 'visible', 'hidden'
            timeout: Wait timeout in milliseconds

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        try:
            await self._page.wait_for_selector(
                selector, state=state, timeout=timeout or self.default_timeout
            )
            return {"success": True, "selector": selector, "state": state}
        except PlaywrightTimeout:
            return {
                "success": False,
                "error": f"Timeout waiting for {selector} to be {state}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Screenshots ====================

    async def screenshot(
        self, path: Optional[str] = None, full_page: bool = False
    ) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.

        Args:
            path: File path to save screenshot (optional)
            full_page: Capture full scrollable page

        Returns:
            Screenshot information with base64 data if no path provided
        """
        await self._ensure_initialized()

        try:
            screenshot_bytes = await self._page.screenshot(
                path=path, full_page=full_page
            )

            result = {
                "success": True,
                "url": self._page.url,
                "full_page": full_page,
            }

            if path:
                result["path"] = path
            else:
                result["data"] = base64.b64encode(screenshot_bytes).decode("utf-8")
                result["data_uri"] = f"data:image/png;base64,{result['data']}"

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot_element(
        self, selector: str, path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take a screenshot of a specific element.

        Args:
            selector: CSS selector
            path: File path to save screenshot (optional)

        Returns:
            Screenshot information
        """
        await self._ensure_initialized()

        try:
            element = await self._page.query_selector(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}

            screenshot_bytes = await element.screenshot(path=path)

            result = {
                "success": True,
                "selector": selector,
            }

            if path:
                result["path"] = path
            else:
                result["data"] = base64.b64encode(screenshot_bytes).decode("utf-8")
                result["data_uri"] = f"data:image/png;base64,{result['data']}"

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Tab Management ====================

    async def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Open a new tab.

        Args:
            url: URL to navigate to in the new tab (optional)

        Returns:
            New tab information
        """
        await self._ensure_initialized()

        try:
            new_page = await self._context.new_page()
            new_page.set_default_timeout(self.default_timeout)
            self._pages.append(new_page)
            self._page = new_page

            if url:
                await self.goto(url)

            return {
                "success": True,
                "tab_index": len(self._pages) - 1,
                "url": self._page.url,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def switch_tab(self, index: int) -> Dict[str, Any]:
        """
        Switch to a different tab.

        Args:
            index: Tab index (0-based)

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        if 0 <= index < len(self._pages):
            self._page = self._pages[index]
            return {
                "success": True,
                "tab_index": index,
                "url": self._page.url,
                "title": await self._page.title(),
            }
        else:
            return {"success": False, "error": f"Invalid tab index: {index}"}

    async def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        """
        Close a tab.

        Args:
            index: Tab index to close (if None, closes current tab)

        Returns:
            Operation result
        """
        await self._ensure_initialized()

        if len(self._pages) == 1:
            return {"success": False, "error": "Cannot close the last tab"}

        try:
            if index is None:
                page_to_close = self._page
                close_index = self._pages.index(self._page)
            else:
                if 0 <= index < len(self._pages):
                    page_to_close = self._pages[index]
                    close_index = index
                else:
                    return {"success": False, "error": f"Invalid tab index: {index}"}

            await page_to_close.close()
            self._pages.remove(page_to_close)

            # Switch to the previous tab if we closed the current one
            if page_to_close == self._page:
                self._page = self._pages[max(0, close_index - 1)]

            return {
                "success": True,
                "closed_index": close_index,
                "current_tab": self._pages.index(self._page),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_tabs(self) -> List[Dict[str, Any]]:
        """
        List all open tabs.

        Returns:
            List of tab information
        """
        await self._ensure_initialized()

        result = []
        for i, page in enumerate(self._pages):
            result.append({
                "index": i,
                "url": page.url,
                "title": await page.title(),
                "is_current": page == self._page,
            })

        return result

    # ==================== Advanced ====================

    async def execute_javascript(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Script execution result
        """
        await self._ensure_initialized()

        try:
            result = await self._page.evaluate(script)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait(self, milliseconds: int) -> Dict[str, Any]:
        """
        Wait for a specified amount of time.

        Args:
            milliseconds: Time to wait in milliseconds

        Returns:
            Operation result
        """
        await asyncio.sleep(milliseconds / 1000)
        return {"success": True, "waited": milliseconds}

    # ==================== Cleanup ====================

    async def close(self):
        """Close the browser and cleanup resources."""
        if self._initialized:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            self._initialized = False
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._pages = []
