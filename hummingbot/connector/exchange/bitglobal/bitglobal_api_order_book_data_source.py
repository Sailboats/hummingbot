#!/usr/bin/env python

import asyncio
import aiohttp
import logging
import json
import pandas as pd
from typing import (
    Any,
    AsyncIterable,
    Dict,
    List,
    Optional
)
import time
import websockets
from websockets.exceptions import ConnectionClosed
from hummingbot.core.utils import async_ttl_cache
from hummingbot.core.utils.async_utils import safe_gather
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.logger import HummingbotLogger
from hummingbot.connector.exchange.bitglobal.bitglobal_order_book import BitglobalOrderBook
from hummingbot.connector.exchange.bitglobal.bitglobal_constants import BASE_ENDPOINT, WS_BASE_ENDPOINT, TICKERS_URL


# WS_BASE_ENDPOINT = "wss://global-api.bithumb.pro/message/realtime"
# BASE_ENDPOINT = "https://global-openapi.bithumb.pro/openapi/v1"


class BitglobalAPIOrderBookDataSource(OrderBookTrackerDataSource):
    MESSAGE_TIMEOUT = 30.0
    PING_TIMEOUT = 10.0

    _bitglobalaobds_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._bitglobalaobds_logger is None:
            cls._bitglobalaobds_logger = logging.getLogger(__name__)
        return cls._bitglobalaobds_logger

    def __init__(self, trading_pairs: List[str], domain="com"):
        self.logger().debug(f"__init__: trading_pairs = {trading_pairs}")
        super().__init__(trading_pairs)
        self._order_book_create_function = lambda: OrderBook()
        self._domain = domain

    @classmethod
    async def get_last_traded_prices(cls, trading_pairs: List[str], domain: str = "com") -> Dict[str, float]:
        cls.logger().debug(f'get_last_traded_prices: trading_pairs = {trading_pairs}')
        tasks = [cls.get_last_traded_price(t_pair, domain) for t_pair in trading_pairs]
        results = await safe_gather(*tasks)
        return {t_pair: result for t_pair, result in zip(trading_pairs, results)}

    @classmethod
    async def get_last_traded_price(cls, trading_pair: str, domain: str = "com") -> float:
        cls.logger().debug(f'get_last_traded_price: trading_pair = {trading_pair}')
        async with aiohttp.ClientSession() as client:
            resp = await client.get(f"{BASE_ENDPOINT}/spot/trades?symbol={trading_pair}")
            resp_json = await resp.json()
            return float(resp_json["data"][0]["p"])

    @staticmethod
    async def fetch_trading_pairs(domain="com") -> List[str]:
        try:
            async with aiohttp.ClientSession() as client:
                url = f"{BASE_ENDPOINT}/spot/config"
                async with client.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # fetch d["symbol"] for bitglobal
                        trading_pair_list: List[str] = []
                        trading_pair_list = [d["symbol"] for d in data["data"]["spotConfig"]]
                        return trading_pair_list

        except Exception:
            # Do nothing if the request fails -- there will be no autocomplete for bitglobal trading pairs
            pass

        return []

    @staticmethod
    async def get_snapshot(client: aiohttp.ClientSession, trading_pair: str, limit: int = 1000,
                           domain: str = "com") -> Dict[str, Any]:
        params: Dict = {"symbol": trading_pair}
        url = f"{BASE_ENDPOINT}/spot/orderBook"
        async with client.get(url, params=params) as response:
            response: aiohttp.ClientResponse = response
            if response.status != 200:
                raise IOError(f"Error fetching market snapshot for {trading_pair}. "
                              f"HTTP status is {response.status}.")
            data: Dict[str, Any] = await response.json()

            result: Dict[str, Any] = {}
            result["asks"] = data["data"]["s"]
            result["bids"] = data["data"]["b"]
            result["trading_pair"] = trading_pair
            result["lastUpdateId"] = int(data["data"]["ver"])
            # Need to add the symbol into the snapshot message for the Kafka message queue.
            # Because otherwise, there'd be no way for the receiver to know which market the
            # snapshot belongs to.

            return result

    async def get_new_order_book(self, trading_pair: str) -> OrderBook:
        self.logger().debug(f'get_new_order_book: trading_pair = {trading_pair}')
        async with aiohttp.ClientSession() as client:
            snapshot: Dict[str, Any] = await self.get_snapshot(client, trading_pair, 1000, self._domain)
            snapshot_timestamp: float = time.time()
            snapshot_msg: OrderBookMessage = BitglobalOrderBook.snapshot_message_from_exchange(
                snapshot,
                snapshot_timestamp,
                metadata={"trading_pair": trading_pair}
            )
            order_book = self.order_book_create_function()
            order_book.apply_snapshot(snapshot_msg.bids, snapshot_msg.asks, snapshot_msg.update_id)
            return order_book

    async def _inner_messages(self,
                              ws: websockets.WebSocketClientProtocol) -> AsyncIterable[str]:
        # Terminate the recv() loop as soon as the next message timed out, so the outer loop can reconnect.
        try:
            while True:
                try:
                    msg: str = await asyncio.wait_for(ws.recv(), timeout=self.MESSAGE_TIMEOUT)
                    yield msg
                except asyncio.TimeoutError:
                    pong_waiter = await ws.ping(data='{"cmd":"ping"}')
                    await asyncio.wait_for(pong_waiter, timeout=self.PING_TIMEOUT)
        except asyncio.TimeoutError:
            self.logger().warning("WebSocket ping timed out. Going to reconnect...")
            return
        except ConnectionClosed:
            return
        finally:
            await ws.close()

    async def listen_for_trades(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """Subscribes to the trade channel of the exchange. Adds incoming messages(of filled orders) to the output queue, to be processed by"""
        self.logger().debug('listen_for_trades:')
        while True:
            try:
                # trading_pairs: List[str] = self._trading_pairs
                # print("WS_BASE_ENDPOINT: ", WS_BASE_ENDPOINT)
                async with websockets.connect(WS_BASE_ENDPOINT) as ws:
                    ws: websockets.WebSocketClientProtocol = ws

                    # for trading_pair in trading_pairs:
                    subscribe_request: Dict[str, Any] = {
                        "cmd": "subscribe",
                        "args": list(map(
                            lambda pair: f"TRADE:{pair}",
                            self._trading_pairs
                        ))
                    }
                    self.logger().debug("request: ", json.dumps(subscribe_request))
                    await ws.send(json.dumps(subscribe_request))

                    async for raw_msg in self._inner_messages(ws):
                        decoded_msg: str = raw_msg

                        # self.logger().debug("decode message:", decoded_msg)

                        if '"00002"' in decoded_msg:
                            self.logger().debug("Connect success")
                            # print(f"Connect success")
                        elif '"00001"' in decoded_msg:
                            self.logger().debug(f"Subscribe success: {decoded_msg}")
                            # print(f"Subscribe success: {decoded_msg}")
                        elif '"00006"' in decoded_msg:
                            # self.logger().debug(f"one-time complete trades: {decoded_msg}")
                            # print(f"one-time complete trades: {decoded_msg}")
                            for data in json.loads(decoded_msg)['data']:
                                trade_msg: OrderBookMessage = BitglobalOrderBook.trade_message_from_exchange(data)
                                # self.logger().debug(f"Putting msg in queue: {str(trade_msg)}")
                                output.put_nowait(trade_msg)
                        elif '"00007"' in decoded_msg:
                            # self.logger().debug(f"Received new trade: {decoded_msg}")
                            # print(f"Received new trade: {decoded_msg}")
                            data = json.loads(decoded_msg)["data"]
                            trade_msg: OrderBookMessage = BitglobalOrderBook.trade_message_from_exchange(data)
                            # self.logger().debug(f"Putting msg in queue: {str(trade_msg)}")
                            output.put_nowait(trade_msg)
                        else:
                            self.logger().debug(
                                f"Unrecognized message received from bitglobal websocket: {decoded_msg}")
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error with WebSocket connection. Retrying after 30 seconds...",
                                    exc_info=True)
                await asyncio.sleep(30.0)

    @classmethod
    @async_ttl_cache(ttl=60 * 30, maxsize=1)
    async def get_active_exchange_markets(self) -> pd.DataFrame:
        self.logger().debug('get_active_exchange_markets')
        """
        Performs the necessary API request(s) to get all currently active trading pairs on the
        exchange and returns a pandas.DataFrame with each row representing one active trading pair.

        Also the the base and quote currency should be represented under the baseAsset and quoteAsset
        columns respectively in the DataFrame.

        Refer to Calling a Class method for an example on how to test this particular function.
        Returned data frame should have trading pair as index and include usd volume, baseAsset and quoteAsset
        """
        async with aiohttp.ClientSession() as client:
            async with client.get(f"{BASE_ENDPOINT}{TICKERS_URL}?symbol=ALL") as products_response:
                products_response: aiohttp.ClientResponse = products_response
                if products_response.status != 200:
                    raise IOError(f"Error fetching active Bitglobal markets. HTTP status is {products_response.status}.")

                data = await products_response.json()
                data = data['data']
                all_markets: pd.DataFrame = pd.DataFrame.from_records(data=data)

                all_markets.rename({"v": "volume", "c": "price"},
                                   axis="columns", inplace=True)
                return all_markets

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        self.logger().debug("listen_for_order_book_diffs:")
        while True:
            try:
                # self.logger().debug("WS_BASE_ENDPOINT: ", WS_BASE_ENDPOINT)

                async with websockets.connect(WS_BASE_ENDPOINT) as ws:
                    ws: websockets.WebSocketClientProtocol = ws

                    subscribe_request: Dict[str, Any] = {
                        "cmd": "subscribe",
                        "args": list(map(
                            lambda pair: f"ORDERBOOK:{pair}",
                            self._trading_pairs
                        ))
                    }

                    self.logger().debug("request: ", json.dumps(subscribe_request))
                    await ws.send(json.dumps(subscribe_request))

                    async for raw_msg in self._inner_messages(ws):
                        decoded_msg: str = raw_msg

                        # self.logger().debug("decode message:", decoded_msg)

                        if '00002' in decoded_msg:
                            self.logger().debug("Connect success")
                            # print(f"Connect success")
                        elif '00001' in decoded_msg:
                            self.logger().debug(f"Subscribe success: {decoded_msg}")
                            # print(f"Subscribe success: {decoded_msg}")
                        # elif '"00006"' in decoded_msg:
                        #     self.logger().debug(f"one-time complete orderbooks: {decoded_msg}")
                        #     print(f"one-time complete orderbooks: {decoded_msg}")
                        #     message = json.loads(decoded_msg)
                        #     for data in message['data']:
                        #         trade_msg: OrderBookMessage = BitglobalOrderBook.diff_message_from_exchange(msg=data,timestamp=message["timestamp"])
                        #         self.logger().debug(f"Putting msg in queue: {str(trade_msg)}")
                        #         output.put_nowait(trade_msg)
                        elif '"00006"' or '"00007"' in decoded_msg:
                            # self.logger().debug(f"Received new trade: {decoded_msg}")
                            # print(f"Received new trade: {decoded_msg}")
                            data = json.loads(decoded_msg)
                            trade_msg: OrderBookMessage = BitglobalOrderBook.diff_message_from_exchange(
                                msg=data["data"], timestamp=data["timestamp"])
                            # self.logger().debug(f"Putting msg in queue: {str(trade_msg)}")
                            # print(f"Putting msg in queue: {str(trade_msg)}")
                            output.put_nowait(trade_msg)
                        else:
                            self.logger().debug(
                                f"Unrecognized message received from bitglobal websocket: {decoded_msg}")
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error with WebSocket connection. Retrying after 30 seconds...",
                                    exc_info=True)
                await asyncio.sleep(30.0)

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        self.logger().debug('listen_for_order_book_snapshots:')
        while True:
            try:
                async with aiohttp.ClientSession() as client:
                    for trading_pair in self._trading_pairs:
                        try:
                            snapshot: Dict[str, Any] = await self.get_snapshot(client, trading_pair,
                                                                               domain=self._domain)
                            snapshot_timestamp: float = time.time()
                            snapshot_msg: OrderBookMessage = BitglobalOrderBook.snapshot_message_from_exchange(
                                snapshot,
                                snapshot_timestamp,
                                metadata={"trading_pair": trading_pair}
                            )
                            output.put_nowait(snapshot_msg)
                            self.logger().debug(f"Saved order book snapshot for {trading_pair}")
                            # Be careful not to go above Binance's API rate limits.
                            await asyncio.sleep(5.0)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            self.logger().error("Unexpected error.", exc_info=True)
                            await asyncio.sleep(5.0)
                    this_hour: pd.Timestamp = pd.Timestamp.utcnow().replace(minute=0, second=0, microsecond=0)
                    next_hour: pd.Timestamp = this_hour + pd.Timedelta(hours=1)
                    delta: float = next_hour.timestamp() - time.time()
                    await asyncio.sleep(delta)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error.", exc_info=True)
                await asyncio.sleep(5.0)
