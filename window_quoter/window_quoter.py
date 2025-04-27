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
        self.window_type = self.window_config.get('window_type')
        self.interior_finish = self.window_config.get(f"{self.window_type}.interior") if self.window_type in ['casement', 'awning', 'picture_window','fixed_casement'] else 'white'
        self.exterior_color = self.window_config.get(f"{self.window_type}.exterior_color")
        self.stain_config = self.window_config.get(f"{self.window_type}.stain")
        self.hardware_config = self.window_config.get(f"{self.window_type}.hardware")
        self.shape_config = self.window_config.get(f"{shapes}")
        if self.shape_config is not None and self.shape_config.get("type") is None:
            self.shape_config = None


    def quote_window(self, price_breakdown = {}, current_price = 0.0):

        # 1. Basic Calculations
        sf = calculate_sf(self.width, self.height)
        lf = calculate_lf(self.width, self.height)
        if sf <= 0: # Basic validation
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

        # interior/exterior stain
        # add hardware subtype

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
    def quote_window(self, price_breakdown = {}, current_price = 0.0)
        glass_cost = 0
        glass_type_selection = config.get('glass_type', 'Standard') # Default to a non-upcharge type
        pane_type = config.get('glass_panes', 'Double')
        thickness = config.get('glass_thickness', 'N/A')

        # Find the actual standard type for the selected pane if 'Standard' is chosen
        if glass_type_selection == 'Standard':
            if pane_type == 'Double': glass_type_selection = 'LowE 180/272 (Std)'
            elif pane_type == 'Triple': glass_type_selection = 'LowE 180/Clr/LowE 180 (Std)'
            # else: handle error or default

        if glass_type_selection and glass_type_selection != 'LowE 180/272 (Std)' and glass_type_selection != 'LowE 180/Clr/LowE 180 (Std)':
            try:
                if pane_type not in glass_upcharges or glass_type_selection not in glass_upcharges[pane_type]:
                    raise KeyError(f"Glass type '{glass_type_selection}' for '{pane_type}' panes not found.")

                thickness_options = glass_upcharges[pane_type][glass_type_selection]
                charge_per_sf = 0
                if thickness in thickness_options:
                    charge_per_sf = thickness_options[thickness]
                elif 'N/A' in thickness_options:
                    charge_per_sf = thickness_options['N/A']
                else:
                    # If only one thickness, use it? Or default? Or raise error? Let's try finding *any* value.
                    if len(thickness_options) == 1:
                        charge_per_sf = list(thickness_options.values())[0]
                        st.info(f"Auto-selected thickness for {glass_type_selection} as only one option exists.")
                    else:
                        raise KeyError(f"Thickness '{thickness}' required but not specified/valid for glass '{glass_type_selection}' ({pane_type}). Available: {list(thickness_options.keys())}")

                effective_sf = max(sf, MIN_GLASS_SF)
                glass_cost = charge_per_sf * effective_sf
                price_breakdown[f"Glass Upcharge: {glass_type_selection} ({pane_type} {thickness}) @ {charge_per_sf:.2f}/SF (Min {MIN_GLASS_SF} SF)"] = f"{glass_cost:.2f}"

                # Add shape surcharge for glass
                is_shaped = shape_selection != 'None'
                if is_shaped:
                    shape_glass_surcharge = glass_shape_upcharge.get(pane_type, 0)
                    if shape_glass_surcharge > 0:
                        glass_cost += shape_glass_surcharge
                        price_breakdown[f"Glass Shape Surcharge ({pane_type})"] = f"{shape_glass_surcharge:.2f}"

                current_price += glass_cost
            except KeyError as e:
                st.error(f"Glass Upcharge Error: {e}")
                price_breakdown['Glass Upcharge Error'] = str(e)
            except Exception as e:
                st.error(f"Unexpected error during glass calculation: {e}")
                price_breakdown['Glass Upcharge Error'] = str(e)

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

        # 10. Trim (Exterior & Interior)
        trim_finish_key = get_finish_key(config['finish'], config['exterior_color'], config.get('stain', 'None'))

        # Exterior Trim
        ext_trim_cost = 0
        ext_trim_type = config.get('exterior_trim_type', 'None')
        ext_trim_size = config.get('exterior_trim_size', 'None')
        if ext_trim_type != 'None':
            try:
                price_per_lf = trim_prices_per_lf['exterior'][ext_trim_type][ext_trim_size][trim_finish_key]
                ext_trim_cost = price_per_lf * lf
                price_breakdown[f"Exterior Trim: {ext_trim_type} {ext_trim_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{ext_trim_cost:.2f}"
                current_price += ext_trim_cost
            except KeyError:
                st.warning(f"Exterior trim price not found for {ext_trim_type} {ext_trim_size} {trim_finish_key}")

        # Interior Trim
        int_trim_cost = 0
        int_trim_type = config.get('interior_trim_type', 'None')
        int_trim_size = config.get('interior_trim_size', 'None')
        if int_trim_type != 'None':
            try:
                # Get the price, handling the different structures
                if int_trim_size == 'None': # For types like Woodreturn
                    price_per_lf = trim_prices_per_lf['interior'][int_trim_type]['None'][trim_finish_key]
                else:
                    price_per_lf = trim_prices_per_lf['interior'][int_trim_type][int_trim_size][trim_finish_key]

                # Handle N/A for wood extension colour/stain (where price might be 0)
                is_wood_ext_na = 'Wood Extension' in int_trim_type and trim_finish_key in ['Colour', 'Stain'] and price_per_lf == 0.0

                if is_wood_ext_na:
                    int_trim_cost = 0
                    price_breakdown[f"Interior Trim: {int_trim_type} {int_trim_size} ({trim_finish_key})"] = "N/A"
                else:
                    int_trim_cost = price_per_lf * lf
                    price_breakdown[f"Interior Trim: {int_trim_type} {int_trim_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{int_trim_cost:.2f}"
                    current_price += int_trim_cost

            except KeyError as e:
                st.warning(f"Interior trim price not found for {int_trim_type} {int_trim_size} {trim_finish_key}. Error: {e}")
            except Exception as e:
                st.error(f"Error processing interior trim {int_trim_type} {int_trim_size}: {e}")


        # --- Final Unit Price ---
        unit_price = round(current_price, 2)
        price_breakdown['===> Calculated Unit Price'] = f"${unit_price:.2f}" # Make it stand out

        # Sort breakdown for better readability, placing price last
        sorted_breakdown = dict(sorted(price_breakdown.items(), key=lambda item: item[0].startswith('=')))


        return unit_price, sorted_breakdown