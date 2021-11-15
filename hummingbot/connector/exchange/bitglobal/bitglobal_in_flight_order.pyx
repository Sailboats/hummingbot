from decimal import Decimal
from typing import (
    Any,
    Dict,
    Optional
)

from hummingbot.core.event.events import (
    OrderType,
    TradeType
)
from hummingbot.connector.exchange.bitglobal.bitglobal_exchange import BitglobalExchange
from hummingbot.connector.in_flight_order_base import InFlightOrderBase
from hummingbot.logger import HummingbotLogger
import logging

hm_logger = None

cdef class BitglobalInFlightOrder(InFlightOrderBase):

    @classmethod
    def logger(cls) -> HummingbotLogger:
        global hm_logger
        if hm_logger is None:
            hm_logger = logging.getLogger(__name__)
        return hm_logger

    def __init__(self,
                 client_order_id: str,
                 exchange_order_id: str,
                 trading_pair: str,
                 order_type: OrderType,
                 trade_type: TradeType,
                 price: Decimal,
                 amount: Decimal,
                 initial_state: str = "live"):
#        self.logger().debug(f'__init__: client_order_id = {client_order_id}, exchange_order_id = {exchange_order_id}, trading_pair = {trading_pair}, order_type = {order_type}, trade_type = {trade_type}, price = {price}, amount = {amount}, initial_state = {initial_state}')
        super().__init__(
            client_order_id,
            exchange_order_id,
            trading_pair,
            order_type,
            trade_type,
            price,
            amount,
            initial_state  # submitted, partial-filled, cancelling, filled, canceled, partial-canceled
        )

    @property
    def is_done(self) -> bool:
        return self.last_state in {"fullDealt", "canceled", "success", "cancel"}

    @property
    def is_cancelled(self) -> bool:
        return self.last_state in {"canceled", "cancel"}

    @property
    def is_failure(self) -> bool:
        return self.last_state in {"canceled", "cancel"}

    @property
    def is_open(self) -> bool:
        return self.last_state in {"live", "created", "partDealt", "send", "pending"}

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> InFlightOrderBase:
#        cls.logger().debug(f'from_json: data = {data}')
        cdef:
            BitglobalInFlightOrder retval = BitglobalInFlightOrder(
                client_order_id=data["client_order_id"],
                exchange_order_id=data["exchange_order_id"],
                trading_pair=data["trading_pair"],
                order_type=getattr(OrderType, data["order_type"]),
                trade_type=getattr(TradeType, data["trade_type"]),
                price=Decimal(data["price"]),
                amount=Decimal(data["amount"]),
                initial_state=data["last_state"]
            )
        retval.executed_amount_base = Decimal(data["executed_amount_base"])
        retval.executed_amount_quote = Decimal(data["executed_amount_quote"])
        retval.fee_asset = data["fee_asset"]
        retval.fee_paid = Decimal(data["fee_paid"])
        retval.last_state = data["last_state"]
        return retval
