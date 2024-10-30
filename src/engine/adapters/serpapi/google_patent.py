from engine.adapters.serpapi_adapter import SerpapiAdapter

class GooglePatentsAdapter(SerpapiAdapter):
    """Adapter for Google Patents searches via SerpApi."""
    async def search(self, query: str, number=100, sort=("new", "old"), type=("PATENT", "DESIGN"), status=("GRANT", "APPLICATION")):
        params = {
            "engine": "google_patents",
            "q": query,
            "num": number,
            "sort": sort,
            "type": type,
            "status": status,
        }
        response = self.perform_search(params)
        return self.parse_response(response)

    def parse_response(self, response):

        results = response.get('organic_results', [])
        parsed_results = [
            {
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "patent_id": result.get("patent_id", ""),
                "link": f"https://patents.google.com/patent/{result.get('patent_id', '')}"
            }
            for result in results
        ]
        
        # Print the final parsed results
        print("GOOGLE PATENT")
        print()
        print()
        print()
        print()
        print(parsed_results)
        
        return parsed_results