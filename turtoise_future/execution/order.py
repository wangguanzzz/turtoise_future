"""Order management"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class Order:
    """Order representation"""

    def __init__(
        self,
        order_id: str,
        market: str,
        side: str,
        size: float,
        price: float,
        order_type: OrderType = OrderType.LIMIT,
    ):
        self.order_id = order_id
        self.market = market
        self.side = side  # BUY or SELL
        self.size = size
        self.price = price
        self.order_type = order_type
        self.status = OrderStatus.PENDING
        self.filled_size = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "market": self.market,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "order_type": self.order_type.value,
            "status": self.status.value,
            "filled_size": self.filled_size,
            "created_at": self.created_at.isoformat(),
        }


class OrderManager:
    """Manager for order lifecycle"""

    def __init__(self):
        self.orders: Dict[str, Order] = {}

    def create_order(
        self,
        market: str,
        side: str,
        size: float,
        price: float,
        order_type: OrderType = OrderType.LIMIT,
    ) -> Order:
        """Create a new order"""
        order_id = f"{market}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        order = Order(order_id, market, side, size, price, order_type)
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)

    def update_order_status(self, order_id: str, status: OrderStatus, filled_size: float = 0):
        """Update order status"""
        if order_id in self.orders:
            self.orders[order_id].status = status
            self.orders[order_id].filled_size = filled_size
            self.orders[order_id].updated_at = datetime.now()

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    def get_pending_orders(self, market: Optional[str] = None) -> List[Order]:
        """Get all pending orders"""
        orders = [o for o in self.orders.values() if o.status == OrderStatus.PENDING]
        if market:
            orders = [o for o in orders if o.market == market]
        return orders
