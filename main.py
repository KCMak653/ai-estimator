from project_quoter import ProjectQuoter
from collections import OrderedDict

if __name__ == "__main__":
    print("Demo: ProjectQuoter with multiple window descriptions")
    
    # List of free text descriptions
    window_descriptions = [
        "picture window 40 x 30 triple pane lowe 180, jamb 3.5",
        "picture window 40 x 30 triple pane lowe 180, brickmould 1.25",
        "picture window 40 x 30 triple pane lowe 180, brickmould 1 5/8"
        # "awning window 24 x 36 single pane lowe 180"
    ]
    
    model_name = "gpt-4.1"
    
    print(f"Creating project with {len(window_descriptions)} windows...")
    
    # Create project quoter with list of descriptions
    project_quoter = ProjectQuoter(model_name, debug=True)
    
    # Get project quote
    total_cost, project_breakdown = project_quoter.quote_project(window_descriptions)
    

    def pretty_print_dict(d, indent=0):
        """Pretty print OrderedDict with proper indentation"""
        spaces = "  " * indent
        for key, value in d.items():
            if isinstance(value, (dict, OrderedDict)):
                print(f"{spaces}{key}:")
                pretty_print_dict(value, indent + 1)
            else:
                print(f"{spaces}{key}: {value}")
    
    print("\nProject Breakdown:")
    pretty_print_dict(project_breakdown)