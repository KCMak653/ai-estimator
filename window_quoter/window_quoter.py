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
        
        # Window-scoped configurations (apply to whole window)
        self.brickmould_config = getOrReturnNoneYaml(self.window_config, "brickmould")
        if self.brickmould_config is not None and not getOrReturnNoneYaml(self.brickmould_config, "include"):
            self.brickmould_config = None
            
        self.casing_extension_config = getOrReturnNoneYaml(self.window_config, "casing_extension")
        if self.casing_extension_config is not None and not getOrReturnNoneYaml(self.casing_extension_config, "type"):
            self.casing_extension_config = None

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
            
            # 3. Base Price for this unit
            try:
                base_finish = 'white' if interior_finish == 'stain' else interior_finish
                base_p = get_base_price(unit_type, base_finish, self.pricing_config, unit_sf)
                unit_breakdown[f'Base Price ({base_finish}, {area_frac:.1%} of window)'] = base_p
                current_price += base_p
            except ValueError as e:
                unit_breakdown['Error'] = f"Base Price Error: {e}"
                continue

            # 4. Exterior Finish Upcharge for this unit
            if exterior_finish is not None and exterior_finish != 'white':
                if exterior_finish == 'color':
                    exterior_upcharge = base_p * getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.color_base_perc")
                    unit_breakdown['Exterior Color Upcharge'] = exterior_upcharge
                    current_price += exterior_upcharge
                elif exterior_finish == 'custom_color':
                    exterior_upcharge = base_p * getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.color_base_perc")
                    custom_color_add_on = getOrReturnNoneYaml(self.pricing_config, f"{unit_type}.exterior.custom_color_add_on")
                    exterior_upcharge += custom_color_add_on
                    unit_breakdown['Exterior Custom Color Upcharge'] = exterior_upcharge
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
                            unit_breakdown[f"Hardware: {hardware}"] = cost
                            current_price += cost

            # 7. Shape Add-on for this unit
            shape_config = getOrReturnNoneYaml(unit_data, 'shapes')
            if shape_config is not None:
                shape_type = getOrReturnNoneYaml(shape_config, "type")
                if shape_type is not None:
                    shape_cost = getOrReturnNoneYaml(self.pricing_config, f"shapes.{shape_type}")
                    unit_breakdown[f"Shape Add-on: {shape_type}"] = shape_cost
                    current_price += shape_cost
                    
                    extras = getOrReturnNoneYaml(shape_config, "extras")
                    if extras:
                        for extra, incl_bool in extras.items():
                            if incl_bool:
                                cost = getOrReturnNoneYaml(self.pricing_config, f"shapes.{extra}")
                                unit_breakdown[f"Shape Extra: {extra}"] = cost
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

            if glass_config is None:
                price_breakdown[f'Error - {unit_key}'] = "No glass configuration found"
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
            
            # Add shape surcharge if applicable for this unit
            shape_config = getOrReturnNoneYaml(unit_data, 'shapes')
            if shape_config is not None and getOrReturnNoneYaml(shape_config, 'type') is not None:
                shape_add_on = getOrReturnNoneYaml(self.pricing_config, f"glass.{glass_type}.shaped_add_on")
                current_price += shape_add_on
                unit_breakdown["Glass Shape Add-on"] = shape_add_on
            
        return current_price, price_breakdown

    def quote_trim(self, price_breakdown = {}, current_price = 0.0):
        if self.brickmould_config:
            brickmould_cost = self.lf * getOrReturnNoneYaml(self.pricing_config, f"brickmould.{getOrReturnNoneYaml(self.brickmould_config, 'size')}.{getOrReturnNoneYaml(self.brickmould_config, 'finish')}")
            price_breakdown[f"Brickmould ({getOrReturnNoneYaml(self.brickmould_config, 'size')}, {getOrReturnNoneYaml(self.brickmould_config, 'finish')})"] = brickmould_cost
            current_price += brickmould_cost

        if self.casing_extension_config:
            if getOrReturnNoneYaml(self.casing_extension_config, 'type') == 'wood_ext':
                # Get wood extension price brackets
                wood_ext_brackets = getOrReturnNoneYaml(self.pricing_config, "casing_extension.wood_ext")
                if wood_ext_brackets is None:
                    price_breakdown['Error'] = "Wood extension pricing not found"
                    return 0, price_breakdown
                    
                casing_extension_cost = calculate_price_from_yaml_brackets(self.lf, wood_ext_brackets, "Wood extension")
            else:
                casing_extension_cost = self.lf * getOrReturnNoneYaml(self.pricing_config, f"casing_extension.{getOrReturnNoneYaml(self.casing_extension_config, 'type')}.{getOrReturnNoneYaml(self.casing_extension_config, 'finish')}")
            price_breakdown[f"Casing Extension ({getOrReturnNoneYaml(self.casing_extension_config, 'type')}, {getOrReturnNoneYaml(self.casing_extension_config, 'finish')})"] = casing_extension_cost
            current_price += casing_extension_cost

            if getOrReturnNoneYaml(self.casing_extension_config, "include_bay_bow_extension"):
                bay_bow_extension_cost = getOrReturnNoneYaml(self.pricing_config, "casing_extension.bay_bow_extension")
                price_breakdown[f"Bay & Bow Extension"] = bay_bow_extension_cost
                current_price += bay_bow_extension_cost

            if getOrReturnNoneYaml(self.casing_extension_config, "include_bay_bow_plywood"):
                # Get bay/bow plywood price brackets
                plywood_brackets = getOrReturnNoneYaml(self.pricing_config, "casing_extension.bay_bow_plywood")
                if plywood_brackets is None:
                    price_breakdown['Error'] = "Bay/bow plywood pricing not found"
                    return 0, price_breakdown
                    
                bay_bow_plywood_cost = calculate_price_from_yaml_brackets(self.lf, plywood_brackets, "Bay/bow plywood")
                price_breakdown[f"Bay & Bow Plywood"] = bay_bow_plywood_cost
                current_price += bay_bow_plywood_cost

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
        current_price, price_breakdown = self.quote_trim(price_breakdown, current_price)
        price_breakdown = self.quote_labour(price_breakdown) # labour does not get added to window price

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