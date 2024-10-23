import json
# from .adapters.serpapi_adapter import GoogleShoppingAdapter, GooglePatentsAdapter, GoogleScholarAdapter, GoogleAutocompleteAdapter

class ExternalServiceFactory:
    # adapter_mapping = {
    #     "google_patent": GooglePatentsAdapter,
    #     "google_shopping": GoogleShoppingAdapter,
    #     "google_scholar": GoogleScholarAdapter,
    #     "google_autocomplete": GoogleAutocompleteAdapter,
    # }

    @staticmethod
    def get_service_adapter(service_name):
        # adapter_class = ExternalServiceFactory.adapter_mapping.get(service_name)
        # if adapter_class:
            # return adapter_class()
        pass
        # raise ValueError(f"No adapter found for service: {service_name}")
