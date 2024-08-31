from .adapters import DarkobAdapter

class ExternalServiceFactory:
    @staticmethod
    def get_service_adapter(service_name):
        if service_name == 'darkob':
            return DarkobAdapter()
        return None
