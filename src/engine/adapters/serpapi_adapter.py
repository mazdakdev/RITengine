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