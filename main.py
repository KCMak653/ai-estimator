from project_quoter import ProjectQuoter
from collections import OrderedDict
from utils import pretty_print_dict

if __name__ == "__main__":
    print("Demo: ProjectQuoter with combined window descriptions")

    # Project with combined window descriptions in single string
    project = {
        "project_name": "123 Main Street",
        "project_description": "black black 180/clear",
        "window_descriptions": "3x 36 x 48 casement, 34x34 white white awning"
    }
    model_name = "gpt-4.1"

    # Create project quoter
    project_quoter = ProjectQuoter(model_name, debug=True)
    
    # Get project quote
    total_cost, project_breakdown = project_quoter.quote_project(project)
    

    print("\nProject Breakdown:")
    pretty_print_dict(project_breakdown)