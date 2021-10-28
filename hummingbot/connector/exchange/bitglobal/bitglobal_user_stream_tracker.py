#!/usr/bin/env python

import asyncio
import logging
from typing import (
    Optional,
    List
)
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.logger import HummingbotLogger
from hummingbot.core.data_type.user_stream_tracker import UserStreamTracker
from hummingbot.core.utils.async_utils import (
    safe_ensure_future,
    safe_gather,
)
from hummingbot.connector.exchange.bitglobal.bitglobal_api_user_stream_data_source import BitglobalAPIUserStreamDataSource
from hummingbot.connector.exchange.bitglobal.bitglobal_auth import BitglobalAuth
from hummingbot.connector.exchange.bitglobal.bitglobal_constants import EXCHANGE_NAME


class BitglobalUserStreamTracker(UserStreamTracker):
    _bitglobalust_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._bitglobalust_logger is None:
            cls._bitglobalust_logger = logging.getLogger(__name__)
        return cls._bitglobalust_logger

    def __init__(self,
                 bitglobal_auth: Optional[BitglobalAuth] = None,
                 trading_pairs: Optional[List[str]] = [],
                 ):
        self.logger().debug(f'__init__: bitglobal_auth = {bitglobal_auth}, trading_pairs = {trading_pairs}')
        super().__init__()
        self._ev_loop: asyncio.events.AbstractEventLoop = asyncio.get_event_loop()
        self._data_source: Optional[UserStreamTrackerDataSource] = None
        self._user_stream_tracking_task: Optional[asyncio.Task] = None
        self._bitglobal_auth: BitglobalAuth = bitglobal_auth
        self._trading_pairs: List[str] = trading_pairs

    @property
    def data_source(self) -> UserStreamTrackerDataSource:
        if not self._data_source:
            self._data_source = BitglobalAPIUserStreamDataSource(bitglobal_auth=self._bitglobal_auth,
                                                                 trading_pairs=self._trading_pairs)
        return self._data_source

    @property
    def exchange_name(self) -> str:
        return EXCHANGE_NAME

    async def start(self):
        self._user_stream_tracking_task = safe_ensure_future(
            self.data_source.listen_for_user_stream(self._ev_loop, self._user_stream)
        )
        await safe_gather(self._user_stream_tracking_task)
