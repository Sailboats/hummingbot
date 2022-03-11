# import aiohttp
import asyncio
# from typing import (
#     Any,
#     AsyncIterable,
#     Dict,
#     List,
#     Optional
# )

from binance_api_order_book_data_source import BinanceAPIOrderBookDataSource

binance_ob_data_source = BinanceAPIOrderBookDataSource(["BTCUSDT", "LTCBTC"])
loop = asyncio.get_event_loop()
# prices = loop.run_until_complete(binance_ob_data_source.get_last_traded_prices(["BTCUSDT", "LTCBTC"]))
# for key, value in prices.items():
#     print(f"{key} last_trade_price: {value}")


loop.run_until_complete(binance_ob_data_source.listen_for_trades(ev_loop=asyncio.get_event_loop(), output=asyncio.Queue()))
print('test ends')
