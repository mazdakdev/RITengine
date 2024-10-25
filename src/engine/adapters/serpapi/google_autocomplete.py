from engine.adapters.serpapi_adapter import SerpapiAdapter

class GoogleAutocompleteAdapter(SerpapiAdapter):
    """Adapter for Google Autocomplete suggestions via SerpApi."""
    def search(self, query: str, geo_location: str = None, language: str = None):
        params = {
            "engine": "google_autocomplete",
            "q": query,
            "gl": geo_location,
            "hl": language
        }
        response = self.perform_search(params)
        return self.parse_response(response)

    def parse_response(self, response):
        results = response.get('suggestions', [])
        return [{"value": item["value"], "relevance": item["relevance"]} for item in results]
