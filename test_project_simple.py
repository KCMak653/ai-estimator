from project_quoter import ProjectQuoter

if __name__ == "__main__":
    print("Testing ProjectQuoter with existing window configs")
    
    # Use existing valid config files
    config_files = [
        "window_example.conf",
        "window_example2.conf", 
        "window_test_1.conf"  # This one was successfully generated
    ]
    
    print(f"Quoting project with {len(config_files)} windows...")
    
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