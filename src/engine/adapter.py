from engine.adapters import serpapi_adapter

# Centralized dictionary mapping OpenAI function names to adapter classes
api_adapters = {
    "google_shopping_search": serpapi_adapter.GoogleShoppingAdapter,
    "google_patents_search": serpapi_adapter.GooglePatentsAdapter,
    "google_scholar_search": serpapi_adapter.GoogleScholarAdapter,
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

async def process_with_adapter(function_name, query):
    """
    Processes the query through the corresponding adapter based on the function name.
    
    Args:
        function_name (str): The name of the external service function.
        query (str): The query or result returned from OpenAI function.
    
    Returns:
        dict: The processed data from the external service through the adapter.
    """
    # Step 1: Get the adapter for the function
    adapter = get_adapter(function_name)
    
    if not adapter:
        raise ValueError(f"No adapter found for the service: {function_name}")
    
    # Step 2: Call the adapter's search method with the query
    result = await adapter.search(query=query, function_name=function_name)
    
    # Step 3: Return the result from the adapter
    return result
