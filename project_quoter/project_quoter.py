from window_quoter.window_quoter import WindowQuoter
from typing import List, Dict, Tuple, Union
import json


class ProjectQuoter:
    def __init__(self, pricing_config_path: str):
        self.pricing_config_path = pricing_config_path
        self.window_quoters = []
        
    def add_window(self, window_config_path: str) -> None:
        """Add a window configuration to the project"""
        quoter = WindowQuoter(window_config_path, self.pricing_config_path)
        self.window_quoters.append(quoter)
        
    def add_windows(self, window_config_paths: List[str]) -> None:
        """Add multiple window configurations to the project"""
        for config_path in window_config_paths:
            self.add_window(config_path)
            
    def quote_project(self) -> Tuple[float, Dict]:
        """Quote all windows in the project and return total cost and breakdown"""
        total_cost = 0.0
        project_breakdown = {}
        
        for i, quoter in enumerate(self.window_quoters, 1):
            window_cost, window_breakdown = quoter.quote_project()
            
            # Add window to project breakdown
            window_key = f"Window {i}"
            project_breakdown[window_key] = {
                'cost': f"${window_cost:.2f}",
                'breakdown': window_breakdown
            }
            
            total_cost += window_cost
            
        project_breakdown['Total Project Cost'] = f"${total_cost:.2f}"
        
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
            cost, breakdown = quoter.quote_project()
            quotes.append((cost, breakdown))
        return quotes