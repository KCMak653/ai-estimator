from flask import Flask, request, jsonify
from project_quoter import ProjectQuoter
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")
app.json.sort_keys = False
@app.route('/quote_project', methods=['POST'])
def quote_project():
    """
    Quote a window project from JSON input
    
    Expected JSON structure:
    {
        "project_name": "My Project",
        "window_descriptions": ["window 1 description", "window 2 description", ...]
    }
    
    Returns JSON structure:
    {
        "project_name": "My Project", 
        "price_breakdown": {...}
    }
    """
    data = request.get_json()
    
    project_name = data['project_name']
    window_descriptions = data['window_descriptions']
    
    # Default model for now - could be configurable later
    model_name = "gpt-4.1"
    
    # Create project quoter and get quote
    project_quoter = ProjectQuoter(model_name)
    total_cost, price_breakdown = project_quoter.quote_project(window_descriptions)
    print("price_breakdown", price_breakdown)
    json_response = jsonify({
        "project_name": project_name,
        "price_breakdown": price_breakdown
    })
    print("json_response", json_response)
    return json_response

@app.route('/test', methods=['GET'])
def test():
    response = jsonify({"status": "working", "message": "GET request successful"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)