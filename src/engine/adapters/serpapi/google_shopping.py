from engine.adapters.serpapi_adapter import SerpapiAdapter

class GoogleShoppingAdapter(SerpapiAdapter):
    """Adapter for Google Shopping searches via SerpApi."""
    async def search(self, query: str, language: str = None):
        params = {
            "engine": "google_shopping",
            "google_domain": "google.com",
            "q": query,
            "hl": language
        }
        response = self.perform_search(params)
        return self.parse_response(response)

    def parse_response(self, response):
        results = response.get('shopping_results', [])
        return [{"title": item["title"], "price": item["price"], "thumbnail": item["thumbnail"]} for item in results]