from window_quoter.window_quoter import WindowQuoter
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from typing import List, Dict, Tuple, Union
import json
import os


class ProjectQuoter:
    def __init__(self, free_text_descriptions: List[str], model_name: str, pricing_config_path: str = "valid_config_generator/pricing.conf"):
        self.pricing_config_path = pricing_config_path
        self.window_quoters = []
        self.failed_configs = []
        
        # Initialize the config generator
        self.config_generator = ValidConfigGenerator(model_name)
        
        # Process each free text description
        for i, description in enumerate(free_text_descriptions, 1):
            config_file = f"temp_window_{i}.conf"
            print(f"\nProcessing window {i}: {description}")
            
            # Generate and validate config
            if self.config_generator.generate_config(description, config_file):
                try:
                    # Create window quoter with generated config
                    quoter = WindowQuoter(config_file, self.pricing_config_path)
                    self.window_quoters.append(quoter)
                    print(f"✓ Successfully created quoter for window {i}")
                except Exception as e:
                    print(f"✗ Failed to create quoter for window {i}: {e}")
                    self.failed_configs.append((i, description, str(e)))
            else:
                print(f"✗ Failed to generate valid config for window {i}")
                self.failed_configs.append((i, description, "Config generation failed"))
        
    def cleanup_temp_files(self) -> None:
        """Clean up temporary config files"""
        for i in range(1, len(self.window_quoters) + len(self.failed_configs) + 1):
            temp_file = f"temp_window_{i}.conf"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass  # Ignore cleanup errors
            
    def quote_project(self) -> Tuple[float, Dict]:
        """Quote all windows in the project and return total cost and breakdown"""
        total_cost = 0.0
        project_breakdown = {}
        
        # Add failed configs info
        if self.failed_configs:
            project_breakdown['Failed Windows'] = {
                'count': len(self.failed_configs),
                'details': [f"Window {i}: {desc[:50]}... - {error}" for i, desc, error in self.failed_configs]
            }
        
        # Quote successful windows
        successful_window_num = 1
        for i, quoter in enumerate(self.window_quoters):
            window_cost, window_breakdown = quoter.quote_window()
            
            # Add window to project breakdown
            window_key = f"Window {successful_window_num}"
            project_breakdown[window_key] = {
                'cost': f"${window_cost:.2f}",
                'breakdown': window_breakdown
            }
            
            total_cost += window_cost
            successful_window_num += 1
            
        project_breakdown['Total Project Cost'] = f"${total_cost:.2f}"
        project_breakdown['Successful Windows'] = len(self.window_quoters)
        
        # Clean up temp files
        self.cleanup_temp_files()
        
        return total_cost, project_breakdown
        
    def get_window_count(self) -> int:
        """Return the number of windows in the project"""
        return len(self.window_quoters)
        
    def clear_windows(self) -> None:
        """Remove all windows from the project"""
        self.window_quoters = []
        
    def quote_individual_windows(self) -> List[Tuple[float, Dict]]:
        """Get individual quotes for each window"""
        quotes = []
        for quoter in self.window_quoters:
            cost, breakdown = quoter.quote_window()
            quotes.append((cost, breakdown))
        return quotes