from project_quoter import ProjectQuoter

if __name__ == "__main__":
    print("Demo: ProjectQuoter with multiple window descriptions")
    
    # List of free text descriptions
    window_descriptions = [
        "picture window 40 x 30 triple pane lowe 180",
        "casement window 36 x 48 double pane lowe 180, white interior",
        "awning window 24 x 36 single pane lowe 180"
    ]
    
    model_name = "gpt-4.1"
    
    print(f"Creating project with {len(window_descriptions)} windows...")
    
    # Create project quoter with list of descriptions
    project_quoter = ProjectQuoter(window_descriptions, model_name)
    
    # Get project quote
    total_cost, project_breakdown = project_quoter.quote_project()
    
    print(f"\n{'='*60}")
    print(f"PROJECT QUOTE SUMMARY")
    print(f"{'='*60}")
    print(f"Total Cost: ${total_cost:.2f}")
    print(f"Successful Windows: {project_breakdown.get('Successful Windows', 0)}")
    
    if 'Failed Windows' in project_breakdown:
        print(f"Failed Windows: {project_breakdown['Failed Windows']['count']}")
        
    print(f"\n{'='*60}")
    print(f"DETAILED BREAKDOWN")
    print(f"{'='*60}")
    
    for key, value in project_breakdown.items():
        if key.startswith("Window"):
            print(f"\n{key}:")
            print(f"  Cost: {value['cost']}")
            print("  Key Components:")
            breakdown = value['breakdown']
            for detail_key, detail_value in breakdown.items():
                if 'Price' in detail_key or 'Add-on' in detail_key or 'Upcharge' in detail_key:
                    print(f"    {detail_key}: {detail_value}")
        elif key == "Total Project Cost":
            print(f"\n{key}: {value}")
        elif key == "Failed Windows" and value['count'] > 0:
            print(f"\nFailed Windows ({value['count']}):")
            for detail in value['details']:
                print(f"  - {detail}")

    print(f"Project Breakdown: {project_breakdown}")