"""
Portfolio data models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Portfolio:
    """Portfolio data model"""
    portfolio_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Position:
    """Portfolio position data model"""
    id: Optional[int] = None
    portfolio_id: Optional[str] = None
    ticker: Optional[str] = None
    weight: Optional[float] = None  # Percentage weight (0.0 - 1.0)
    shares: Optional[int] = None
    cost_basis: Optional[float] = None
    entry_date: Optional[datetime] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate position data"""
        if self.weight is not None and not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")
        if self.shares is not None and self.shares < 0:
            raise ValueError(f"Shares must be non-negative, got {self.shares}")
        if self.cost_basis is not None and self.cost_basis < 0:
            raise ValueError(f"Cost basis must be non-negative, got {self.cost_basis}")
