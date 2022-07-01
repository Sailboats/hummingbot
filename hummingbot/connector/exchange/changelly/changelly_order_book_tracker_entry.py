from hummingbot.connector.exchange.changelly.changelly_active_order_tracker import ChangellyActiveOrderTracker
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_tracker_entry import OrderBookTrackerEntry


class ChangellyOrderBookTrackerEntry(OrderBookTrackerEntry):
    def __init__(
        self, trading_pair: str, timestamp: float, order_book: OrderBook, active_order_tracker: ChangellyActiveOrderTracker
    ):
        self._active_order_tracker = active_order_tracker
        super(ChangellyOrderBookTrackerEntry, self).__init__(trading_pair, timestamp, order_book)

    def __repr__(self) -> str:
        return (
            f"ChangellyOrderBookTrackerEntry(trading_pair='{self._trading_pair}', timestamp='{self._timestamp}', "
            f"order_book='{self._order_book}')"
        )

    @property
    def active_order_tracker(self) -> ChangellyActiveOrderTracker:
        return self._active_order_tracker
