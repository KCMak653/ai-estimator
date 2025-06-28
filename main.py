from valid_config_generator.valid_config_generator import ValidConfigGenerator
from window_quoter.window_quoter import WindowQuoter

if __name__ == "__main__":
    print("This is the main module.")

    model_name = "gpt-3.5-turbo"
    model_name = "gpt-4.1"
    free_text = "picture window half circle 50 x 36 triple pane lowe 180 clear, casing 3 1/2\", brickmould 2\" interior stain"

    valid_config_generator = ValidConfigGenerator(model_name)
    config_generated = valid_config_generator.generate_config(free_text, "window_example2.conf")
    if config_generated:
        window_quoter = WindowQuoter("window_example2.conf", "valid_config_generator/pricing.conf")
        final_price, price_breakdown = window_quoter.quote_project()
        print(f"Final Price: {final_price}")
        print(f"Price Breakdown: {price_breakdown}")
    else:
        print("Failed to generate a valid config")