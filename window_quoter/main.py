
from window_quoter import WindowQuoter
from config_loader import ConfigLoader

if __name__ == "__main__":
    quoter = WindowQuoter()
    config = ConfigLoader().load_test_config()
    price = quoter.quote_single_item(config)
    print("Quoted price:", price)