from window_quoter.window_quoter import WindowQuoter
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from typing import List, Dict, Tuple, Union
import json
import os


class ProjectQuoter:
    def __init__(self, model_name: str, pricing_config_path: str = "valid_config_generator/pricing.conf"):
        self.pricing_config_path = pricing_config_path
        self.model_name = model_name
        
    def cleanup_temp_files(self, num_windows: int) -> None:
        """Clean up temporary config files"""
        for i in range(1, num_windows + 1):
            temp_file = f"temp_window_{i}.conf"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass  # Ignore cleanup errors
            
    def quote_project(self, free_text_descriptions: List[str]) -> Tuple[float, Dict]:
        """Quote all windows in the project and return total cost and breakdown"""
        failed_configs = []
        
        # Initialize the config generator
        config_generator = ValidConfigGenerator(self.model_name)
        total_cost = 0.0
        project_breakdown = {}
        successful_window_num = 0

        # Process each free text description
        for i, description in enumerate(free_text_descriptions, 1):
            config_file = f"temp_window_{i}.conf"
            print(f"\nProcessing window {i}: {description}")
            
            # Generate and validate config
            if config_generator.generate_config(description, config_file):
                try:
                    # Create window quoter with generated config
                    window_cost, window_breakdown = WindowQuoter(config_file, self.pricing_config_path).quote_window()
                    if 'Error' in window_breakdown.keys():
                        print(f"✗ Failed to generate price breakdown for window {i}")
                        failed_configs.append((i, description, "Price breakdown generation failed"))
                    else:
                        window_key = f"Window {i}"
                        project_breakdown[window_key] = {
                            'cost': f"${window_cost:.2f}",
                            'breakdown': window_breakdown
                        }
                        total_cost += window_cost
                        successful_window_num += 1
                        print(f"✓ Successfully created quote for window {i}")
                except Exception as e:
                    print(f"✗ Failed to create quote for window {i}: {e}")
                    failed_configs.append((i, description, str(e)))
            else:
                print(f"✗ Failed to generate valid config for window {i}")
                failed_configs.append((i, description, "Config generation failed"))
        
        

        # Add failed configs info
        if failed_configs:
            project_breakdown['Failed Windows'] = {
                'count': len(failed_configs),
                'details': [f"Window {i}: {desc[:50]}... - {error}" for i, desc, error in failed_configs]
            }
            
        project_breakdown['Total Project Cost'] = f"${total_cost:.2f}"
        project_breakdown['Quoted Windows'] = len(free_text_descriptions)
        
        # Clean up temp files
        self.cleanup_temp_files(len(free_text_descriptions))
        
        return total_cost, project_breakdown
        

        