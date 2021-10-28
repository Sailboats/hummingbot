# A single source of truth for constant variables related to the exchange

# from hummingbot.core.api_throttler.data_types import RateLimit

EXCHANGE_NAME = "bitglobal"
BASE_ENDPOINT = "https://global-openapi.bithumb.pro/openapi/v1"
WS_BASE_ENDPOINT = "wss://global-api.bithumb.pro/message/realtime"

BITGLOBAL_WS_CODE_NOMAL = "00007"

BITGLOBAL_WS_CODES = {
    BITGLOBAL_WS_CODE_NOMAL
}

SERVER_TIME = "/serverTime"
BALANCE_URL = "/spot/assetList"
ORDER_CANCEL = "/spot/cancelOrder"
BATCH_ORDER_CANCEL = "/spot/cancelOrder/batch"
ORDER_DETAILS_URL = "/spot/singleOrder"
INSTRUMENTS_URL = "/spot/config"
SERVER_TIME = "/serverTime"
PLACE_ORDER = "/spot/placeOrder"
TICKERS_URL = "/spot/ticker"

# Crypto.com has a per method API limit

# RATE_LIMITS = [
#     RateLimit(limit_id="ALL", limit=100, time_interval=1),
#     RateLimit(limit_id=CHECK_NETWORK_PATH_URL, limit=100, time_interval=1, linked_limits=["ALL"]),
#     RateLimit(limit_id=GET_TRADING_RULES_PATH_URL, limit=100, time_interval=1, linked_limits=["ALL"]),
#     RateLimit(limit_id=CREATE_ORDER_PATH_URL, limit=15, time_interval=0.1, linked_limits=["ALL"]),
#     RateLimit(limit_id=CANCEL_ORDER_PATH_URL, limit=15, time_interval=0.1, linked_limits=["ALL"]),
#     RateLimit(limit_id=GET_ACCOUNT_SUMMARY_PATH_URL, limit=3, time_interval=0.1, linked_limits=["ALL"]),
#     RateLimit(limit_id=GET_ORDER_DETAIL_PATH_URL, limit=30, time_interval=0.1, linked_limits=["ALL"]),
#     RateLimit(limit_id=GET_OPEN_ORDERS_PATH_URL, limit=3, time_interval=0.1, linked_limits=["ALL"]),
# ]

# RATE_LIMITS = [
#     RateLimit(limit_id=CHECK_NETWORK_PATH_URL, limit=100, time_interval=1),
#     RateLimit(limit_id=GET_TRADING_RULES_PATH_URL, limit=100, time_interval=1),
#     RateLimit(limit_id=CREATE_ORDER_PATH_URL, limit=15, time_interval=0.1),
#     RateLimit(limit_id=CANCEL_ORDER_PATH_URL, limit=15, time_interval=0.1),
#     RateLimit(limit_id=GET_ACCOUNT_SUMMARY_PATH_URL, limit=3, time_interval=0.1),
#     RateLimit(limit_id=GET_ORDER_DETAIL_PATH_URL, limit=30, time_interval=0.1),
#     RateLimit(limit_id=GET_OPEN_ORDERS_PATH_URL, limit=3, time_interval=0.1),
# ]
#
#
# API_REASONS = {
#     0: "Success",
#     10001: "Malformed request, (E.g. not using application/json for REST)",
#     10002: "Not authenticated, or key/signature incorrect",
#     10003: "IP address not whitelisted",
#     10004: "Missing required fields",
#     10005: "Disallowed based on user tier",
#     10006: "Requests have exceeded rate limits",
#     10007: "Nonce value differs by more than 30 seconds from server",
#     10008: "Invalid method specified",
#     10009: "Invalid date range",
#     20001: "Duplicated record",
#     20002: "Insufficient balance",
#     30003: "Invalid instrument_name specified",
#     30004: "Invalid side specified",
#     30005: "Invalid type specified",
#     30006: "Price is lower than the minimum",
#     30007: "Price is higher than the maximum",
#     30008: "Quantity is lower than the minimum",
#     30009: "Quantity is higher than the maximum",
#     30010: "Required argument is blank or missing",
#     30013: "Too many decimal places for Price",
#     30014: "Too many decimal places for Quantity",
#     30016: "The notional amount is less than the minimum",
#     30017: "The notional amount exceeds the maximum",
# }
