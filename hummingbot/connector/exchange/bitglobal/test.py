# import aiohttp
import asyncio
# from typing import (
#     Any,
#     AsyncIterable,
#     Dict,
#     List,
#     Optional
# )

from bitglobal_api_order_book_data_source import BitglobalAPIOrderBookDataSource
from bitglobal_api_user_stream_data_source import BitglobalAPIUserStreamDataSource
from bitglobal_auth import BitglobalAuth

ds = BitglobalAPIOrderBookDataSource(["QTUM-USDT"])

loop = asyncio.get_event_loop()

# loop.run_until_complete(ds.listen_for_trades(ev_loop=asyncio.get_event_loop(), output=asyncio.Queue()))
# loop.run_until_complete(ds.listen_for_order_book_diffs(ev_loop=asyncio.get_event_loop(), output=asyncio.Queue()))
# loop.run_until_complete(ds.listen_for_order_book_snapshots(ev_loop=asyncio.get_event_loop(), output=asyncio.Queue()))

usds = BitglobalAPIUserStreamDataSource(bitglobal_auth=BitglobalAuth(api_key="88bec0dffb8d031d1ffb0ff52535bbad", secret_key="e7d61138a647a00a447bca1e206db53ee08e249560281c8258b51d142f3adf1f"), trading_pairs=["QTUM-USDT"])
loop.run_until_complete(usds.listen_for_user_stream(ev_loop=asyncio.get_event_loop(), output=asyncio.Queue()))
