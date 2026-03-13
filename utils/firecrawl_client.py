from firecrawl import FirecrawlApp

class FirecrawlClient:

    def __init__(self, api_key):
        self.app = FirecrawlApp(api_key=api_key)

    def scrape(self, url):
        try:
            result = self.app.scrape_url(url, formats=["markdown"])
            return result.get("markdown", "")
        except Exception as e:
            print("Firecrawl error:", e)
            return ""
