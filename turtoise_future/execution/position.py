"""Position management"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class Position:
    """Position representation"""

    def __init__(
        self,
        market: str,
        side: PositionSide,
        size: float,
        entry_price: float,
        hedge_ratio: float = 1.0,
    ):
        self.market = market
        self.side = side
        self.size = size
        self.entry_price = entry_price
        self.current_price = entry_price
        self.hedge_ratio = hedge_ratio
        self.opened_at = datetime.now()
        self.updated_at = datetime.now()
        self.pnl = 0.0

    def update_price(self, price: float):
        """Update current price and recalculate PnL"""
        self.current_price = price
        self.updated_at = datetime.now()
        self.calculate_pnl()

    def calculate_pnl(self):
        """Calculate unrealized PnL"""
        if self.side == PositionSide.LONG:
            self.pnl = (self.current_price - self.entry_price) * self.size
        elif self.side == PositionSide.SHORT:
            self.pnl = (self.entry_price - self.current_price) * self.size
        else:
            self.pnl = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market": self.market,
            "side": self.side.value,
            "size": self.size,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "hedge_ratio": self.hedge_ratio,
            "pnl": self.pnl,
            "opened_at": self.opened_at.isoformat(),
        }


class PositionManager:
    """Manager for positions"""

    def __init__(self):
        self.positions: Dict[str, Position] = {}

    def open_position(
        self,
        market: str,
        side: str,
        size: float,
        price: float,
        hedge_ratio: float = 1.0,
    ) -> Position:
        """Open a new position"""
        position_side = PositionSide.LONG if side == "BUY" else PositionSide.SHORT
        position = Position(market, position_side, size, price, hedge_ratio)
        self.positions[market] = position
        return position

    def close_position(self, market: str) -> Optional[Position]:
        """Close a position"""
        if market in self.positions:
            position = self.positions[market]
            position.side = PositionSide.FLAT
            del self.positions[market]
            return position
        return None

    def get_position(self, market: str) -> Optional[Position]:
        """Get position for a market"""
        return self.positions.get(market)

    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())

    def update_position_price(self, market: str, price: float):
        """Update position price"""
        if market in self.positions:
            self.positions[market].update_price(price)

    def get_total_pnl(self) -> float:
        """Get total unrealized PnL"""
        return sum(p.pnl for p in self.positions.values())

    def has_position(self, market: str) -> bool:
        """Check if market has open position"""
        return market in self.positions and self.positions[market].side != PositionSide.FLAT
