import unittest
from unittest.mock import patch, MagicMock
from engine.adapters.serpapi_adapter import GooglePatentsAdapter

class GooglePatentsAdapterTest(unittest.TestCase):
    @patch.object(GooglePatentsAdapter, 'perform_search')
    def test_search_format(self, mock_perform_search):
        # Arrange: Set up mock response from SerpApi
        mock_perform_search.return_value = {
            'organic_results': [
                {
                    'title': 'Cranioplasty Mesh Patent 1',
                    'snippet': 'Description of the first patent.',
                    'patent_id': 'US1234567A',
                },
                {
                    'title': 'Cranioplasty Mesh Patent 2',
                    'snippet': 'Description of the second patent.',
                    'patent_id': 'US7654321B',
                }
            ]
        }

        # Initialize the adapter
        adapter = GooglePatentsAdapter()
        
        # Act: Call the search method with the desired parameters
        query = 'cranioplasty mesh'
        result = adapter.search(query=query, number=2)
        
        # Assert: Check that result matches the expected format
        expected_result = [
            {
                'title': str,
                'snippet': str,
                'patent_id': str,
                'link': unittest.mock.ANY  # Allow for partial link match checking below
            },
            {
                'title': str,
                'snippet': str,
                'patent_id': str,
                'link': unittest.mock.ANY
            }
        ]
        
        # Verify the response format
        for item, expected_item in zip(result, expected_result):
            self.assertIsInstance(item['title'], str)
            self.assertIsInstance(item['snippet'], str)
            self.assertIsInstance(item['patent_id'], str)
            self.assertTrue(item['link'].startswith('https://patents.google.com/patent/'))

if __name__ == '__main__':
    unittest.main()
