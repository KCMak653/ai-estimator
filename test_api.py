import requests
import json

def test_api():
    """Test the API with a sample project"""
    
    # API endpoint
    url = "http://localhost:5000/quote_project"
    
    # Test data
    test_data = {
        "project_name": "Kitchen Renovation Windows",
        "window_descriptions": [
            "picture window 40 x 30 triple pane lowe 180",
            "casement window 36 x 48 double pane lowe 180, white interior",
            "awning window 24 x 36 single pane lowe 180"
        ]
    }
    
    # Make request
    response = requests.post(url, json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print("API Response:")
        print(f"Project: {result['project_name']}")
        print(f"Price Breakdown: {json.dumps(result['price_breakdown'], indent=2)}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_api()