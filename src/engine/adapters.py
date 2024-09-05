from abc import ABC, abstractmethod
from django.conf import settings
import httpx

class ExternalServiceAdapter(ABC):
    @abstractmethod
    async def perform_action(self, message):
        pass

class DarkobAdapter(ExternalServiceAdapter):
    def __init__(self):
        self.BASE_URL = "http://api.darkob.co.ir/api/patent_search_RIT"
        self.HEADERS = {
            "Secret": settings.DARKOB_SECRET,
            "X-FP": settings.DARKOB_XFP,
        }

    async def perform_action(self, message):
        params = {
            "operators[0]": "and",
            "fields[0]": "mozoo_ekhtera",
            "values[0]": message,
            "operators[1]": "and",
            "fields[1]": "kholaseh_ekhterah",
            "values[1]": "",
            "operators[2]": "and",
            "fields[2]": "inventor",
            "values[2]": "",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, headers=self.HEADERS, params=params)

        if response.status_code == 200:
            try:
                response_data = response.json()
                return {"patents_data": [item['kholaseh_ekhterah'] for item in response_data['data']['aghahi']['data']]}
            except Exception:
                return ["Something went wrong, the patents data couldn't be retrieved."]
        return ["Something went wrong, the patents data couldn't be retrieved."]
