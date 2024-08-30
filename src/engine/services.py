import requests

BASE_URL = "http://api.darkob.co.ir/api/patent_search_RIT"
HEADERS = {
    "Secret": "eyJleHAiOjE0ODUxNDA5ODQsImlhdCI6MTQ4NTEzNzM4NCwiaXNzIjoiYWNtZS5jb20iLCJzdWIiOiIy",
    "X-FP": "mtlhsaazdvwwysngqawnpnpihqnyxcci"
}

async def search_patents(mozoo_ekhtera, kholaseh_ekhterah="", inventor=""):

    params = {
        "operators[0]": "and",
        "fields[0]": "mozoo_ekhtera",
        "values[0]": mozoo_ekhtera,
        "operators[1]": "and",
        "fields[1]": "kholaseh_ekhterah",
        "values[1]": kholaseh_ekhterah,
        "operators[2]": "and",
        "fields[2]": "inventor",
        "values[2]": inventor,
    }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    if response.status_code == 200:
        response_data = response.json()
        return [item['kholaseh_ekhterah'] for item in response_data['data']['aghahi']['data']]
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
