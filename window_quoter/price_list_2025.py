# # --- Price List Data (Extracted & Structured) ---
# # (Keep all the dictionaries: base_prices, option_prices, glass_upcharges, etc. here)
# # Base Prices (Window Type -> Finish -> SF Bracket -> Price)
# # SF Brackets: (max_sf, base_price, price_per_sf_over)
# base_prices = {
#     'Casement': { # 4-9/16 Casement p2 (assuming this is the default)
#         'White': [(6, 154.44, 0), (9, 174.49, 0), (12, 194.66, 16.25)],
#         'Interior Paint': [(6, 182.89, 0), (9, 200.79, 0), (12, 218.80, 18.14)],
#     },
#     'Awning': { # p3
#         'White': [(6, 166.19, 0), (9, 186.36, 0), (12, 206.53, 17.70)],
#         'Interior Paint': [(6, 198.38, 0), (9, 216.39, 0), (12, 234.40, 19.75)],
#     },
#     'Fixed Casement': { # p4
#         'White': [(7, 97.33, 13.67)], # Simplified 'Over' logic here
#         'Interior Paint': [(7, 116.90, 15.25)],
#     },
#     'Picture Window': { # p4
#         'White': [(7, 87.44, 12.58)],
#         'Interior Paint': [(7, 107.38, 13.92)],
#     },
#      'Double Hung Tilt': { # p11 (V-A) - Assuming 'WHITE' only listed
#          # Interior Paint price isn't listed, using White for now
#         'White': [(6, 132.48, 0), (9, 148.38, 0), (12, 164.28, 13.69)],
#         'Interior Paint': [(6, 132.48, 0), (9, 148.38, 0), (12, 164.28, 13.69)], # Placeholder
#      },
#     # 'Small Fixed': { # Based on Quote Line 2 V-A/V-SF/V-A - Requires Clarification
#     #      # This type isn't explicitly in list like others, needs mapping
#     #      # Using 'Picture Window' pricing as a proxy - NEEDS VALIDATION
#     #     'White': [(7, 87.44, 12.58)],
#     #     'Interior Paint': [(7, 107.38, 13.92)],
#     #  }
#     # Add other window types here
# }

# # Option Prices (Fixed Add-ons)
# option_prices = {
#     'Exterior Colour Gentek/Kaycan': 0.25, # Percentage
#     'Exterior Custom Colour Match': 200.00, # Flat add-on
#     'Stain Interior (Fixed Casement/Picture)': 70.00,
#     'Stain Exterior (Fixed Casement/Picture)': 50.00,
#     'Stain Interior (Casement/Awning)': 120.00, # Awning uses 140? check list
#     'Stain Exterior (Casement/Awning)': 90.00,
#     'Stain Exterior Only (Sliders/Hung)': 60.00, # Check applicable types
#     'Rotto Corner Drive 1 Corner': 20.00,
#     'Rotto Corner Drive 2 Corners': 45.00,
#     'Egress Hardware': 10.00,
#     'Max Hinges (Over 30in)': 4.00, # Check if width or height
#     'Limiters': 10.00,
#     'Encore Operating System': 10.00,
#     'Folding Handle': 10.00, # From Quote - Check Price List consistency
# }

# # Glass Upcharges (Pane Type -> Glass Desc -> Thickness -> $/SF)
# glass_upcharges = {
#     'Double': { # p14 Double Glazed
#         'LowE 180/272 (Std)': {'N/A': 0.00}, # Assuming this is the base, no upcharge
#         'LowE 366': {'4MM': 3.50, '5MM': 5.00},
#         'Frosted (Pin head)': {'3MM': 1.75, '5MM': 3.50},
#         'LowE 180/272 Pin head': {'3MM': 4.00, '4MM': 4.75, '5MM': 6.50},
#         'LowE 180/272 Neat': {'3MM': 3.00, '4MM': 3.00, '5MM': 6.00, '6MM': 11.00},
#         'Privacy Delta/Taffeta/Everglade/GlueChip/Acid': {'4MM': 8.00, '5MM': 15.00}, # Grouped privacy
#         'LowE 180/272 Privacy': {'3MM': 10.25, '4MM': 11.00, '5MM': 19.00 },
#         'Tinted Bronze/Grey/Blue': {'5MM': 8.50},
#         'Tinted LowE 180/272': {'5MM': 12.00},
#         'Laminated Clear': {'4MM': 13.00, '5MM': 15.00, '6MM': 18.00},
#         'Laminated LowE 180/272': {'4MM': 15.50, '5MM': 19.00, '6MM': 27.00},
#         'Tempered/Tempered': {'4MM': 15.00, '5MM': 17.00, '6MM': 20.00},
#         'Tempered/Tempered LowE 180/272': {'4MM': 17.50, '5MM': 21.00, '6MM': 29.00},
#         'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Placeholder Rate
#     },
#     'Triple': { # p15 Triple Glazed
#         'LowE 180/Clr/LowE 180 (Std)': {'N/A': 0.00}, # Placeholder for std triple
#         'Clear/Clear/Clear': {'3MM': 4.75, '4MM': 7.25, '5MM': 9.50},
#         'LowE 180/Clear/Clear': {'3MM': 6.50, '4MM': 9.00, '5MM': 15.00},
#         'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Placeholder Rate
#         # Add many more triple glaze combinations here...
#     }
# }
# glass_shape_upcharge = { 'Double': 75.00, 'Triple': 100.00 }
# MIN_GLASS_SF = 6.0

# # Grills / SDL Prices (Style -> Price Per Square)
# grill_prices_per_sq = { # p16
#     'None': 0.0,
#     'Colonial White': 3.00, 'Colonial Brass': 4.50, 'Colonial Pewter': 4.50,
#     'Colonial 2 Tone': 4.00, 'Georgian White': 4.50, 'Georgian Two Tone': 5.00,
#     'Pencil White': 4.50, 'Pencil Brass or Pewter': 5.00, 'Box White or Pewter': 5.00,
#     'Prairie': 5.00, 'Small Scroll': 5.00, 'Large Scroll': 10.00,
# }
# sdl_prices_per_sq = { # p17
#     'None': 0.0,
#     'SDL 7/8 White': 15.00, 'SDL 7/8 Colour Out': 20.00, 'SDL 7/8 Colour In & Out': 25.00,
#     'SDL 1 1/4 White': 15.00,
#     # Add rest of SDL types
# }

# # Shape Add-ons (Shape -> Fixed Price)
# shape_prices = { # p13
#     'None': 0.0,
#     'Half Circle': 200.00, 'Quarter Circle': 200.00, 'Ellipse': 250.00,
#     'True Ellipse': 250.00, 'Triangle': 225.00, 'Trapezoid': 225.00,
#     'Extended Arch': 250.00, 'Brickmould': 75.00, 'Shape Inside Casing': 75.00,
#     'Shape Extension': 50.00,
# }

# # Trim Prices (Side -> Type -> Size -> Finish -> Price Per LF) - Restructured slightly
# trim_prices_per_lf = { # p18, p19
#     'exterior': {
#         'None': {'None': {'White': 0.0, 'Colour': 0.0, 'Stain': 0.0}},
#         'Brickmould': {
#             '0"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
#             '5/8"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
#             '1 1/4"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
#             '1 5/8"': {'White': 2.57, 'Colour': 3.62, 'Stain': 7.00},
#             '2"': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00},
#         },
#         'Bay/Bow Coupler': {'None': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00}},
#     },
#     'interior': {
#         'None': {'None': {'White': 0.0, 'Colour': 0.0, 'Stain': 0.0}},
#         'Woodreturn': {'None':{'White': 1.54, 'Colour': 2.59, 'Stain': 4.29}},
#         'Vinyl Pkg 2 3/4 Casing': {
#             '1 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
#             '2 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
#             '3 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
#             '4 5/8': {'White': 4.63, 'Colour': 6.50, 'Stain': 10.50},
#         },
#          'Vinyl Pkg 3 1/2 Casing': {
#              '1 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
#              '2 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
#              '3 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
#              '4 5/8': {'White': 5.40, 'Colour': 7.40, 'Stain': 12.00},
#          },
#          'Vinyl Extension': { # Standalone Extension
#              '1 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
#              '2 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
#              '3 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
#              '4 5/8': {'White': 3.40, 'Colour': 4.45, 'Stain': 7.40},
#          },
#          'Wood Extension': {
#             '1-4"': {'White': 4.00, 'Colour': 0.0, 'Stain': 0.0}, # Indicate N/A with 0?
#             '4-7 1/4"': {'White': 5.00, 'Colour': 0.0, 'Stain': 0.0},
#             '7-12"': {'White': 7.00, 'Colour': 0.0, 'Stain': 0.0},
#          }
#     }
# }