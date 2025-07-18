
from window_quoter import WindowQuoter
# from config_loader import ConfigLoader

if __name__ == "__main__":
    window_quoter = WindowQuoter("window_example2.yaml", "valid_config_generator/pricing.yaml")
    final_price, price_breakdown = window_quoter.quote_window()
    print(f"Final Price: {final_price}")
    print(f"Price Breakdown: {price_breakdown}")