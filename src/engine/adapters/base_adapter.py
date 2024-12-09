# base_adapter.py

class BaseAPIAdapter:
    """Base class for all external API adapters."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def perform_search(self, params):
        """To be overridden for specific API clients."""
        raise NotImplementedError("perform_search must be implemented by the subclass")

    def parse_response(self, response):
        """To be overridden to handle specific API response parsing."""
        raise NotImplementedError("parse_response must be implemented by the subclass")
