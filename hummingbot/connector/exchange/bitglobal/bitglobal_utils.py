
from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.config.config_methods import using_exchange


CENTRALIZED = True
EXAMPLE_PAIR = "BTC-USDT"
DEFAULT_FEES = [0.1, 0.1]

KEYS = {
    "bitglobal_api_key":
        ConfigVar(key="bitglobal_api_key",
                  prompt="Enter your Bitglobal API key >>> ",
                  required_if=using_exchange("bitglobal"),
                  is_secure=True,
                  is_connect_key=True),
    "bitglobal_api_secret":
        ConfigVar(key="bitglobal_api_secret",
                  prompt="Enter your Bitglobal API secret >>> ",
                  required_if=using_exchange("bitglobal"),
                  is_secure=True,
                  is_connect_key=True),
}
