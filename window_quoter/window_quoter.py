from window_quoter.helper_funcs import *
import yaml

class WindowQuoter:
    def __init__(self, window_config, pricing_config_path):
        self.window_config = window_config
        with open(pricing_config_path, "r") as file:
            self.pricing_config = yaml.safe_load(file)
        
        # Window-level properties
        self.width = self.window_config.get('width')
        self.height = self.window_config.get('height')
        self.sf = calculate_sf(self.width, self.height)
        self.lf = calculate_lf(self.width, self.height)
        
        # Units configuration
        self.units = getOrReturnNoneYaml(self.window_config, "units")

    def quote_frame(self, price_breakdown = {}, current_price = 0.0):
        # 1. Basic Calculations
        if self.sf <= 0: # Basic validation
            price_breakdown['Error'] = "Width and Height must be greater than 0."
            return 0, price_breakdown
        price_breakdown['sf'] = self.sf
        price_breakdown['lf'] = self.lf
        
        if self.units is None:
            price_breakdown['Error'] = "No units configuration found."
            return 0, price_breakdown
        
        # 2. Process each unit
        for unit_key, unit_data in self.units.items():
            if not unit_key.startswith('unit_'):
                continue
                
            unit_type = getOrReturnNoneYaml(unit_data, 'unit_type')
            area_frac = getOrReturnNoneYaml(unit_data, 'window_area_frac')
            unit_sf = self.sf * area_frac
            
            if unit_type is None or area_frac is None:
                price_breakdown[f'Error - {unit_key}'] = "Missing unit_type or window_area_frac"
                continue
            
            # Create nested breakdown for this unit
            unit_name = f"{unit_key} - {unit_type}"
            price_breakdown[unit_name] = {}
            unit_breakdown = price_breakdown[unit_name]
            
            # Unit interior/exterior finishes
            interior_finish = getOrReturnNoneYaml(unit_data, 'interior') 
            exterior_finish = getOrReturnNoneYaml(unit_data, 'exterior')
            interior_finish = "white" if interior_finish is None else interior_finish

            # Price adjustment factor
            price_adjustment_factor = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.price_list_adjustment_factor")
            price_adjustment_factor = price_adjustment_factor if price_adjustment_factor is not None else 1
            
            # 3. Base Price for this unit
            try:
                base_finish = 'white' if interior_finish == 'stain' else interior_finish
                base_p = get_base_price(unit_type, base_finish, self.pricing_config, unit_sf)
                base_p = base_p / price_adjustment_factor
                unit_breakdown[f'Base Price ({base_finish}, {area_frac:.1%} of window)'] = base_p
                current_price += base_p
            except ValueError as e:
                unit_breakdown['Error'] = f"Base Price Error: {e}"
                continue

            # 4. Exterior Finish Upcharge for this unit
            if exterior_finish is not None and exterior_finish != 'white':
                if exterior_finish == 'colour':
                    exterior_upcharge = base_p * getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.colour_base_perc")
                    unit_breakdown['Exterior Colour Upcharge'] = exterior_upcharge
                    current_price += exterior_upcharge
                elif exterior_finish == 'custom_colour':
                    exterior_upcharge = base_p * getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.colour_base_perc")
                    custom_colour_add_on = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.custom_colour_add_on")
                    exterior_upcharge += custom_colour_add_on
                    unit_breakdown['Exterior Custom colour Upcharge'] = exterior_upcharge
                    current_price += exterior_upcharge
                elif exterior_finish == 'stain':
                    stain_cost = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.stain_add_on")
                    if stain_cost is not None:
                        unit_breakdown['Exterior Stain Add-on'] = stain_cost
                        current_price += stain_cost
                
            # 5. Interior Stain Upcharge for this unit
            if interior_finish == 'stain':
                stain_cost = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.interior.stain_add_on")
                if stain_cost is not None:
                    unit_breakdown['Interior Stain Add-on'] = stain_cost
                    current_price += stain_cost

            # 6. Hardware Options for this unit
            hardware_config = getOrReturnNoneYaml(unit_data, 'hardware')
            if hardware_config:
                for hardware, incl_bool in hardware_config.items():
                    if incl_bool:
                        cost = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.{hardware}")
                        if cost is not None:
                            unit_breakdown[f"Hardware ({hardware})"] = cost
                            current_price += cost

            
            # 7. Required Add-on for this unit - not in the unit description, but in the pricing
            req_add_ons = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.required_addons")
            if req_add_ons is not None:
                for add_on, cost in req_add_ons.items():
                    unit_breakdown[f"Hardware ({add_on})"] = cost
                    current_price += cost 

        return current_price, price_breakdown

    def quote_glass(self, price_breakdown = {}, current_price = 0.0):
        if self.units is None:
            price_breakdown['Error'] = "No units configuration found."
            return 0, price_breakdown
        
        # Process glass for each unit
        for unit_key, unit_data in self.units.items():
            if not unit_key.startswith('unit_'):
                continue
                
            unit_type = getOrReturnNoneYaml(unit_data, 'unit_type')
            glass_config = getOrReturnNoneYaml(unit_data, 'glass')

            # Simplified config may omit glass; skip this unit for glass pricing without error
            if glass_config is None:
                continue

            area_frac = getOrReturnNoneYaml(unit_data, 'window_area_frac')
            unit_sf = self.sf * area_frac
            
            # Create or access nested breakdown for this unit
            unit_name = f"{unit_key} - {unit_type}"

            if unit_name not in price_breakdown:
                price_breakdown[unit_name] = {}
            unit_breakdown = price_breakdown[unit_name]
            
            glass_type = getOrReturnNoneYaml(glass_config, 'type')
            glass_subtype = getOrReturnNoneYaml(glass_config, 'subtype')
            glass_thickness = getOrReturnNoneYaml(glass_config, 'thickness_mm')
            min_sf = getOrReturnNoneYaml(self.pricing_config, f"glass.{glass_type}.min_size_sf")
            
            # Get the glass price brackets for the specific subtype
            glass_price_brackets = getOrReturnNoneYaml(self.pricing_config, f"glass.{glass_type}.{glass_subtype}")

            if glass_price_brackets is None:
                unit_breakdown['Error'] = f"Glass pricing not found for {glass_type}.{glass_subtype}"
                continue
                
            # Find the matching thickness bracket
            glass_price_unit = None
            for bracket in glass_price_brackets:
                if getOrReturnNoneYaml(bracket, 'thickness') == glass_thickness:
                    glass_price_unit = getOrReturnNoneYaml(bracket, 'price')
                    break
                    
            if glass_price_unit is None:
                unit_breakdown['Error'] = f"Glass price not found for thickness {glass_thickness}mm"
                continue

            # Calculate base glass price for this unit
            glass_price = glass_price_unit * max(unit_sf, min_sf)
            current_price += glass_price
            unit_breakdown[f"Glass Base Price ({glass_type} {glass_subtype} {glass_thickness}mm)"] = glass_price

        return current_price, price_breakdown

    def quote_labour(self, price_breakdown = {}):
        """Add labour costs"""
        labour_pricing = self.pricing_config.get("labour")
        labour_cost = max(labour_pricing.get("min_sf"), self.sf) * labour_pricing.get("per_sf_rate")
        price_breakdown["labour"] = labour_cost
        return price_breakdown
    
    def quote_window(self):
        current_price = 0
        price_breakdown = {}

        current_price, price_breakdown = self.quote_frame(price_breakdown, current_price)
        current_price, price_breakdown = self.quote_glass(price_breakdown, current_price)
        price_breakdown = self.quote_labour(price_breakdown)  # labour does not get added to window price

        return current_price, price_breakdown

"""
                ## TODO: implement grills, sdl
        # 8. Grills
        grill_cost = 0
        grill_type_sel = config.get('grill_type', 'None')
        if grill_type_sel != 'None':
            num_squares = config.get('grill_squares', 0)
            price_per_sq = grill_prices_per_sq.get(grill_type_sel)
            if price_per_sq is not None and num_squares > 0:
                grill_cost = price_per_sq * num_squares
                price_breakdown[f"Grills: {grill_type_sel} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{grill_cost:.2f}"
                current_price += grill_cost
            elif num_squares <= 0:
                st.warning(f"Number of squares must be > 0 for grills.")
            else:
                st.warning(f"Grill type '{grill_type_sel}' not found.")

        # 9. SDL
        sdl_cost = 0
        sdl_type_sel = config.get('sdl_type', 'None')
        if sdl_type_sel != 'None':
            num_squares = config.get('sdl_squares', 0)
            price_per_sq = sdl_prices_per_sq.get(sdl_type_sel)
            if price_per_sq is not None and num_squares > 0:
                sdl_cost = price_per_sq * num_squares
                price_breakdown[f"SDL: {sdl_type_sel} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{sdl_cost:.2f}"
                current_price += sdl_cost
            elif num_squares <= 0:
                st.warning(f"Number of squares must be > 0 for SDL.")
            else:
                st.warning(f"SDL type '{sdl_type_sel}' not found.")
"""