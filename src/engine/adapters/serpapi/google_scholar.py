from engine.adapters.serpapi_adapter import SerpapiAdapter

class GoogleScholarAdapter(SerpapiAdapter):
    """Adapter for Google Scholar searches via SerpApi."""
    def search(self, query: str, language: str = None):
        params = {
            "engine": "google_scholar",
            "q": query,
            "hl": language
        }
        response = self.perform_search(params)
        return self.parse_response(response)

    def parse_response(self, response):
        results = response.get('organic_results', [])
        return [{"title": item["title"], "snippet": item["snippet"], "link": item["link"]} for item in results]