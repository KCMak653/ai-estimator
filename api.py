from flask import Flask, request, jsonify
from project_quoter import ProjectQuoter
from flask_cors import CORS
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        "project_description": "brickmould 1_5_8",
        "window_descriptions": {
            "window_1": {
                "quantity": "2",
                "description": "casement white vinyl frame",
                "width": "36",
                "height": "48"
            },
            "window_2": {
                "quantity": "1", 
                "description": "double hung energy efficient",
                "width": "24",
                "height": "36"
            },
            "window_3": {
                "quantity": "4",
                "description": "sliding patio door tempered glass",
                "width": "72",
                "height": "80"
            }
        }
    }
    
    Returns JSON structure:
    {
        "project_name": "My Project", 
        "price_breakdown": {...}
    }
    """
    project_dict = request.get_json()

    project_name = project_dict['project_name']
 
    # Default model for now - could be configurable later
    model_name = "gpt-4.1"
    
    # Create project quoter and get quote
    project_quoter = ProjectQuoter(model_name)
    total_cost, price_breakdown = project_quoter.quote_project(project_dict)
    logger.debug(f"price_breakdown: {price_breakdown}")
    json_response = jsonify({
        "project_name": project_name,
        "price_breakdown": price_breakdown
    })
    logger.debug(f"json_response: {json_response}")
    return json_response

@app.route('/test', methods=['GET'])
def test():
    response = jsonify({"status": "working", "message": "GET request successful"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))