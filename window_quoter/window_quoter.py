from helper_funcs import *
from price_list_2025 import *
from pyhocon import ConfigFactory
# --- Main Quoting Function --- (Keep quote_single_item as before)

class WindowQuoter:
    def __init__(self, config_path):
        self.window_config = ConfigFactory.parse_file("window.conf")
        self.pricing_config = ConfigFactor.parse_file("pricing.conf")
        ## TODO add a bunch of validation, probably to go before the window quoter. So
        ## as to form feedback loop with AI valid_config_generator
        self.width = self.window_config.get('width')
        self.height = self.window_config.get('height')
        self.sf = calculate_sf(self.width, self.height)
        self.lf = calculate_lf(self.width, self.height)
        self.window_type = self.window_config.get('window_type')
        self.interior_finish = self.window_config.get(f"{self.window_type}.interior") if self.window_type in ['casement', 'awning', 'picture_window','fixed_casement'] else 'white'
        self.exterior_color = self.window_config.get(f"{self.window_type}.exterior_color")
        self.stain_config = self.window_config.get(f"{self.window_type}.stain")
        self.hardware_config = self.window_config.get(f"{self.window_type}.hardware")
        self.shape_config = self.window_config.get(f"{shapes}")
        if self.shape_config is not None and self.shape_config.get("type") is None:
            self.shape_config = None
        self.glass_config = self.window_config.get("glass")
        self.brickmould_config = self.window_config.get("brickmould")
        if self.brickmould_config is not None and not self.brickmould_config.get("include"):
            self.brickmould_config = None
        self.casing_extension_config = self.window_config.get("casing_extension")
        if self.casing_extension_config is not None and not self.casing_extension_config.get("type"):
            self.casing_extension_config = None

    def quote_window(self, price_breakdown = {}, current_price = 0.0):

        # 1. Basic Calculations
        if self.sf <= 0: # Basic validation
            price_breakdown['Error'] = "Width and Height must be greater than 0."
            return 0, price_breakdown
        price_breakdown['Calculated SF'] = f"{sf:.2f}"
        price_breakdown['Calculated LF'] = f"{lf:.2f}"

        # 2. Base Price
        try:
            base_p = get_base_price(self.window_type, self.interior_finish, self.pricing_config, sf)
            price_breakdown['Base Price (SF based)'] = f"{base_p:.2f}"
            current_price = base_p
        except ValueError as e:
            price_breakdown['Error'] = f"Base Price Error: {e}"
            return 0, price_breakdown

        # 3. Exterior Color Upcharge
        if self.exterior_color is not None:
            exterior_upcharge = color_upcharge = base_p * self.pricing_config.get(f"{window_type}.exterior_color.base_perc")
            price_breakdown['Exterior Colour Upcharge'] = f"{exterior_upcharge:.2f}"
            if self.exterior_color == 'color_match':
                color_upcharge = self.pricing_config.get(f"{window_type}.exterior_color.color_match_add_on") 
                exterior_upcharge += color_upcharge
                price_breakdown['Exterior Colour Match'] = f"{color_upcharge:.2f}"
            current_price += exterior_upcharge
            
        # 4. Stain Upcharge
        for loc in ['exterior', 'interior']:
            if self.stain_config.get(loc):
                stain_cost = self.pricing_config.get(f"{window_type}.stain.{loc}")
                if stain_cost is not None:
                    price_breakdown[f"Stain Add-on ({loc})"] = f"{stain_cost:.2f}"
                    current_price += stain_cost

        # 5. Hardware Options
        for hardware, incl_bool in self.hardware_config.items():
            if incl_bool:
                cost = self.pricing_config.get(f"{window_type}.{hardware}")
                if cost is not None:
                    price_breakdown[f"Hardware: {hardware}"] = f"{cost:.2f}"
                    current_price += cost

        # 6. Shape Add-on
        if self.shape_config is not None:
            shape_type = self.shape_config.get("type")
            shape_cost = pricing_config.get(f"shapes.{shape_type}")
            price_breakdown[f"Shape Add-on: {shape_type}"] = f"{shape_cost:.2f}"
            current_price += shape_cost
            for extra, incl_bool in self.shape_config.get("extras").items():
                if incl_bool:
                    cost = self.pricing_config.get(f"shapes.{extra}")
                    price_breakdown[f"Shape Add-on Extra: {extra}"] = f"{cost:.2f}"
                    current_price += cost

        return current_price, price_breakdown

        # 7. Glass Upcharge
    def quote_glass(self, price_breakdown = {}, current_price = 0.0):
        glass_type = self.glass_config.get('type')
        glass_thickness = self.glass_config.get('thickness')
        min_sf = self.pricing_config.get(f"glass.{glass_type}.min_size_sf")
        glass_price_bracket = self.pricing_config.get(f"glass.{glass_type}")
        glass_price_dict = {thickness:price for thickness,price in glass_price_bracket}
        current_price = glass_price_dict.get(glass_thickness) * min(self.sf, min_sf)
        price_breakdown[f"Glass Base Price ({glass_type} {glass_thickness})"] = f"{current_price:.2f}"
        if self.shape_config is not None:
            shape_add_on = self.pricing_config.get(f"glass.{glass_type}.shaped_add_on")
            current_price += shape_add_on
            price_breakdown[f"Glass Shape Add-on"] = f"{shape_add_on:.2f}"
        return current_price, price_breakdown

    def quote_trim(self, price_breakdown = {}, current_price = 0.0):
        if self.brickmould_config:
            brickmould_cost = self.lf * self.pricing_config.get(f"brickmould.{self.brickmould_config.get('size')}.{self.brickmould_config.get('finish')}")
            price_breakdown[f"Brickmould"] = f"{brickmould_cost:.2f}"
            current_price += brickmould_cost

        if self.casing_extension_config:
            if self.casing_extension_config.get('type') == 'wood_ext':
                casing_extension_cost = calculate_price_from_brackets(self.lf, self.pricing_config.get(f"casing_extension.wood_ext"))
            else:
                casing_extension_cost = self.lf * self.pricing_config.get(f"casing_extension.{self.casing_extension_config.get('size')}.{self.casing_extension_config.get('finish')}")
            price_breakdown[f"Casing Extension"] = f"{casing_extension_cost:.2f}"
            current_price += casing_extension_cost

        if self.casing_extension_config.get("include_bay_bow_extension"):
            bay_bow_extension_cost = self.pricing_config.get(f"casing_extension.bay_bow_extension")
            price_breakdown[f"Bay & Bow Extension"] = f"{bay_bow_extension_cost:.2f}"
            current_price += bay_bow_extension_cost

        if self.casing_extension_config.get("include_bay_bow_plywood"):
            bay_bow_plywood_cost = calculate_price_from_brackets(self.lf, self.pricing_config.get(f"casing_extension.bay_bow_plywood"))
            price_breakdown[f"Bay & Bow Plywood"] = f"{bay_bow_plywood_cost:.2f}"
            current_price += bay_bow_plywood_cost

        return current_price, price_breakdown

    def tidy_breakdown_and_price(self, price_breakdown, current_price):
        unit_price = round(current_price, 2)
        # Sort breakdown for better readability, placing price last
        price_breakdown['===> Calculated Unit Price'] = f"${unit_price:.2f}" # Make it stand out

        sorted_breakdown = dict(sorted(price_breakdown.items(), key=lambda item: item[0].startswith('=')))
        return sorted_breakdown

        return unit_price, sorted_breakdown



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