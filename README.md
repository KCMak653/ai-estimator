# AI Window Estimator

An intelligent window replacement quoting system that converts natural language descriptions into structured configurations and generates detailed price estimates.

## Features

- **Natural Language Processing**: Convert free-text window descriptions into structured configurations
- **Automated Validation**: Validate configurations against business rules and pricing constraints
- **Comprehensive Pricing**: Calculate detailed quotes including frame, glass, trim, and add-ons
- **Multi-Window Projects**: Quote entire projects with multiple windows
- **Intelligent Config Generation**: AI-powered configuration generation with error correction

## System Architecture

### Core Components

1. **ValidConfigGenerator** (`valid_config_generator/`)
   - Converts natural language to YAML configuration files
   - Uses OpenAI models for intelligent parsing
   - Validates and corrects configurations automatically

2. **WindowQuoter** (`window_quoter/`)
   - Processes window configurations into detailed quotes
   - Handles frame, glass, trim, and hardware pricing
   - Supports all major window types (casement, awning, picture, etc.)

3. **ProjectQuoter** (`project_quoter/`)
   - Manages multi-window projects
   - Processes lists of free-text descriptions
   - Provides consolidated project quotes

4. **ConfigValidator** (`valid_config_generator/config_validator.py`)
   - Validates configuration syntax and values
   - Ensures compliance with pricing structure
   - Provides detailed error reporting

## Quick Start

### Single Window Quote

```python
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from window_quoter.window_quoter import WindowQuoter

# Generate configuration from natural language
generator = ValidConfigGenerator("gpt-4.1")
generator.generate_config("casement window 36x48 double pane lowe 180", "window.yaml")

# Generate quote
quoter = WindowQuoter("window.yaml", "valid_config_generator/pricing.yaml")
price, breakdown = quoter.quote_window()

print(f"Price: ${price:.2f}")
print("Breakdown:", breakdown)
```

### Multi-Window Project Quote

```python
from project_quoter import ProjectQuoter

# Define multiple windows in natural language
windows = [
    "picture window 40 x 30 triple pane lowe 180",
    "casement window 36 x 48 double pane lowe 180, white interior", 
    "awning window 24 x 36 single pane lowe 180"
]

# Generate project quote
project_quoter = ProjectQuoter(windows, "gpt-4.1")
total_cost, breakdown = project_quoter.quote_project()

print(f"Total Project Cost: ${total_cost:.2f}")
```

## Configuration Structure

### Window Types Supported
- Casement
- Awning  
- Picture Window
- Fixed Casement
- Single/Double Slider
- Single/Double Hung

### Finish Options
- **Interior**: `white` (default), `color`, `stain`
- **Exterior**: `white` (default), `color`, `custom_color`, `stain`

### Glass Options
- **Double Pane**: Low-E 180, Low-E 272, Low-E 366, tinted, laminated, tempered
- **Triple Pane**: Various Low-E combinations, specialty glass types

### Hardware & Trim
- Window-specific hardware options
- Brickmould in multiple sizes and finishes
- Casing extensions (vinyl, wood)
- Shape add-ons (half-circle, quarter-circle, etc.)

## Example Configuration

```yaml
window_type: "casement"
width: 36
height: 48

casement:
  interior: "white"
  exterior: "color"

glass:
  type: "double"
  subtype: "lowe_180"
  thickness_mm: 4

shapes:
  type: "half_circle"

brickmould:
  include: true
  size: "1_5_8"
  finish: "white"
```

## Pricing Logic

The system uses a sophisticated pricing model:

1. **Base Price**: Determined by window type and interior finish
2. **Stain Handling**: Uses white base price + stain add-on for stain finishes
3. **Exterior Upcharges**: Percentage-based for colors, flat rate for stains
4. **Glass Pricing**: Thickness and type-based with minimum square footage
5. **Shape Add-ons**: Flat rates for specialty shapes
6. **Hardware**: À la carte pricing for optional hardware

## Running the Examples

```bash
# Multi-window project demo
python3 main.py

# Single window demo
python3 -m window_quoter.main

# Config generator testing
python3 -m valid_config_generator.main
```

## Requirements

- Python 3.9+
- pyyaml
- OpenAI API access
- Custom pricing configuration files

## File Structure

```
ai-estimator/
├── valid_config_generator/     # AI config generation
│   ├── config_validator.py     # Configuration validation
│   ├── valid_config_generator.py
│   ├── window.yaml             # Template configuration
│   └── pricing.yaml            # Pricing database
├── window_quoter/              # Quote calculation engine
│   ├── window_quoter.py        # Main quoter class
│   └── helper_funcs.py         # Utility functions
├── project_quoter/             # Multi-window project handling
│   └── project_quoter.py
├── llm_io/                     # LLM interface
│   └── model_io.py
├── util/                       # Shared utilities
│   └── yaml_util.py
└── main.py                     # Multi-window project demo
```

## Configuration Options

The system supports extensive customization through:
- Window type specifications
- Interior/exterior finish combinations
- Glass type and thickness options
- Hardware selections
- Trim and casing configurations
- Shape modifications

Each option is validated against the pricing database to ensure accurate quotes.