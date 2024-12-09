# import serpapi
# from queue import Queue

# queries = [
#     'burly',
#     'silk',
#     'monkey',
#     'abortive',
#     'hot'
# ]

# search_queue = Queue()

# client = serpapi.Client(api_key="569e4f4be724c749391fb5f2fb3520bc1c993ca136ef9b42d11a041051f0eab7")

# for query in queries:
#     params = {
#         "engine": "google_shopping",
#         "google_domain": "google.com",
#         "q": query,
#         'async': True
#     }

#     search = client.search(params)
#     results = search.as_dict()  # Corrected line
    
#     if 'error' in results:
#         print(results['error'])
#         break

#     print(f"add search to the queue with ID: {results['search_metadata']}")
#     search_queue.put(results)

# print(search_queue)

import serpapi
import serpapi.client

client = serpapi.client("569e4f4be724c749391fb5f2fb3520bc1c993ca136ef9b42d11a041051f0eab7")

params = {
    "engine": "google_patents",
    "q": query,
    "num": number,
    "sort": sort,
    "type": type,
    "status": status,
}

client.search(params)


# title
# price
# thumbnail