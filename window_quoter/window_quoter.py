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
        self.sf_raw = calculate_sf_raw(self.width, self.height)
        self.sf = calculate_sf(self.width, self.height)  # rounded up to next even number
        self.lf = calculate_lf(self.width, self.height)
        
        # Units configuration
        self.units = getOrReturnNoneYaml(self.window_config, "units")

    def quote_frame(self, price_breakdown = {}, current_price = 0.0):
        # 1. Basic Calculations
        if self.sf <= 0: # Basic validation
            price_breakdown['Error'] = "Width and Height must be greater than 0."
            return 0, price_breakdown
        price_breakdown['sf_raw'] = self.sf_raw
        price_breakdown['sf'] = self.sf  # rounded up to next even number
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

   
        return current_price, price_breakdown

    def quote_glass(self, price_breakdown=None, current_price=0.0):
        """Glass price by window sq footage; glass config is tiered (flat + per_sf_rate per tier)."""
        if price_breakdown is None:
            price_breakdown = {}
        if self.pricing_config is None:
            price_breakdown["Error"] = "Pricing config is missing"
            return current_price, price_breakdown
        glass_brackets = self.pricing_config.get("glass")
        if glass_brackets is None:
            price_breakdown["Error"] = "Glass pricing not found in config"
            return current_price, price_breakdown
        if self.sf <= 0:
            return current_price, price_breakdown
        try:
            sorted_brackets = sorted(glass_brackets, key=lambda x: x.get("max_sf"))
            total = 0
            prev_max = 0
            for bracket in sorted_brackets:
                max_val = bracket.get("max_sf")
                price = bracket.get("price", 0)
                rate = bracket.get("per_sf_rate", 0)
                if self.sf <= prev_max:
                    break
                amount_in_tier = min(self.sf, max_val) - prev_max
                if amount_in_tier <= 0:
                    prev_max = max_val
                    continue
                if rate > 0:
                    total += amount_in_tier * rate
                else:
                    total += price
                prev_max = max_val
                if self.sf <= max_val:
                    break
            price_breakdown["Glass"] = total
            current_price += total
        except Exception as e:
            price_breakdown["Error - Glass"] = str(e)
        return current_price, price_breakdown

    def quote_labour(self, price_breakdown = {}):
        """Add labour costs (uses raw sf)."""
        if self.pricing_config is None:
            price_breakdown["Error"] = "Pricing config is missing"
            return price_breakdown
        labour_pricing = self.pricing_config.get("labour")
        if labour_pricing is None:
            price_breakdown["Error"] = "Labour pricing not found in config"
            return price_breakdown
        labour_cost = max(labour_pricing.get("min_sf"), self.sf_raw) * labour_pricing.get("per_sf_rate")
        price_breakdown["labour"] = labour_cost
        return price_breakdown
    
    def quote_window(self):
        current_price = 0
        price_breakdown = {}

        current_price, price_breakdown = self.quote_frame(price_breakdown, current_price)
        current_price, price_breakdown = self.quote_glass(price_breakdown, current_price)
        price_breakdown = self.quote_labour(price_breakdown)  # labour does not get added to window price

        return current_price, price_breakdown

