# adapter.py

from engine.adapters.serpapi import (google_patent, google_scholar, google_shopping, google_autocomplete)

# Centralized dictionary mapping OpenAI function names to adapter classes
api_adapters = {
    "google_patents_search": google_patent.GooglePatentsAdapter,
    "google_scholar_search": google_scholar.GoogleScholarAdapter,
    "google_shopping_search": google_shopping.GoogleShoppingAdapter,
    "google_autocomplete_search": google_autocomplete.GoogleAutocompleteAdapter,
}

async def get_adapter(function_name):
    """
    Returns the corresponding adapter instance for the given function name.
    
    Args:
        function_name (str): The name of the function to map to an adapter.
    
    Returns:
        BaseAPIAdapter: An instance of the adapter for the given function.
    """
    adapter_class = api_adapters.get(function_name)
    
    if not adapter_class:
        raise ValueError(f"No adapter found for function: {function_name}")
    
    return adapter_class()
