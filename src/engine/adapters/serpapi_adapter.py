from django.conf import settings
import serpapi
from .base_adapter import BaseAPIAdapter

class SerpapiAdapter(BaseAPIAdapter):
    """SerpApi adapter class for performing searches using SerpApi."""
    def __init__(self):
        # Fetch API key for SerpApi from Django settings
        api_key = settings.SERPAPI_KEY  # Use the API key from Django settings
        super().__init__(api_key)
        self.client = serpapi.Client(api_key=api_key)

    def perform_search(self, params):
        return self.client.search(params)

class GoogleShoppingAdapter(SerpapiAdapter):
    """Adapter for Google Shopping searches via SerpApi."""
    def search(self, query: str, language: str = None):
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
        return [{"title": item["title"], "price": item["price"]} for item in results]

class GooglePatentsAdapter(SerpapiAdapter):
    """Adapter for Google Patents searches via SerpApi."""
    def search(self, query: str, number=100, sort=("new", "old"), type=("PATENT", "DESIGN"), status=("GRANT", "APPLICATION")):
        params = {
            "engine": "google_patents",
            "q": query,
            "num": number,
            "sort": sort,
            "type": type,
            "status": status,
        }
        response = self.perform_search(params)
        return self.parse_response(response)

    def parse_response(self, response):

        results = response.get('organic_results', [])
        parsed_results = [
            {
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "patent_id": result.get("patent_id", ""),
                "link": f"https://patents.google.com/patent/{result.get('patent_id', '')}"
            }
            for result in results
        ]
        
        # Print the final parsed results
        print("GOOGLE PATENT")
        print()
        print()
        print()
        print()
        print(parsed_results)
        
        return parsed_results

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
