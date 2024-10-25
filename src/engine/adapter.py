# adapter.py

from engine.adapters import serpapi_adapter

# Centralized dictionary mapping OpenAI function names to adapter classes
api_adapters = {
    "google_patents_search": serpapi_adapter.GooglePatentsAdapter,
    "google_scholar_search": serpapi_adapter.GoogleScholarAdapter,
    "google_shopping_search": serpapi_adapter.GoogleShoppingAdapter,
    "google_autocomplete_search": serpapi_adapter.GoogleAutocompleteAdapter,
}

def get_adapter(function_name):
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
