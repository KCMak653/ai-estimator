from valid_config_generator.valid_config_generator import ValidConfigGenerator
from project_quoter import ProjectQuoter

if __name__ == "__main__":
    print("Testing ProjectQuoter with multiple windows")
    
    model_name = "gpt-4.1"
    
    # Multiple window descriptions
    window_descriptions = [
        "picture window half circle 50 x 36 triple pane lowe 180 clear, casing 3 1/2\", brickmould 2\" interior stain",
        "casement window 30 x 48 double pane clear glass, white interior, bronze exterior",
        "awning window 24 x 24 single pane clear glass, wood interior stain exterior"
    ]
    
    # Generate configs for each window
    valid_config_generator = ValidConfigGenerator(model_name)
    config_files = []
    
    for i, description in enumerate(window_descriptions, 1):
        config_file = f"window_test_{i}.conf"
        print(f"\nGenerating config for window {i}: {description}")
        
        config_generated = valid_config_generator.generate_config(description, config_file)
        if config_generated:
            config_files.append(config_file)
            print(f"✓ Config generated: {config_file}")
        else:
            print(f"✗ Failed to generate config for window {i}")
    
    # Quote the project if we have valid configs
    if config_files:
        print(f"\nQuoting project with {len(config_files)} windows...")
        
        project_quoter = ProjectQuoter("valid_config_generator/pricing.conf")
        project_quoter.add_windows(config_files)
        
        total_cost, project_breakdown = project_quoter.quote_project()
        
        print(f"\n{'='*50}")
        print(f"PROJECT QUOTE SUMMARY")
        print(f"{'='*50}")
        print(f"Total Windows: {project_quoter.get_window_count()}")
        print(f"Total Cost: ${total_cost:.2f}")
        
        print(f"\n{'='*50}")
        print(f"DETAILED BREAKDOWN")
        print(f"{'='*50}")
        
        for key, value in project_breakdown.items():
            if key.startswith("Window"):
                print(f"\n{key}:")
                print(f"  Cost: {value['cost']}")
                print("  Breakdown:")
                for detail_key, detail_value in value['breakdown'].items():
                    print(f"    {detail_key}: {detail_value}")
            elif key == "Total Project Cost":
                print(f"\n{key}: {value}")
    else:
        print("\nNo valid configs generated. Cannot quote project.")