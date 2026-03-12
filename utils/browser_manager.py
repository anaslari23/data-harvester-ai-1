from playwright.async_api import async_playwright

class BrowserManager:
    async def fetch(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            html = await page.content()
            await browser.close()
            return html
