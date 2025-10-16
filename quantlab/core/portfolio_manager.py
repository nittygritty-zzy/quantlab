"""
Portfolio management operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..data.database import DatabaseManager
from ..models.portfolio import Portfolio, Position
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioManager:
    """
    Manage portfolios and positions

    Operations:
    - Create, read, update, delete portfolios
    - Add/remove positions
    - Update position weights
    - Query portfolio holdings
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize portfolio manager

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager

    def create_portfolio(
        self,
        portfolio_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Portfolio:
        """
        Create a new portfolio

        Args:
            portfolio_id: Unique portfolio identifier
            name: Portfolio display name
            description: Optional description

        Returns:
            Created Portfolio object
        """
        try:
            # Check if portfolio exists
            existing = self.get_portfolio(portfolio_id)
            if existing:
                raise ValueError(f"Portfolio '{portfolio_id}' already exists")

            # Insert portfolio
            self.db.execute(
                """
                INSERT INTO portfolios (portfolio_id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [portfolio_id, name, description, datetime.now(), datetime.now()]
            )

            logger.info(f"✓ Created portfolio: {portfolio_id} ({name})")

            return Portfolio(
                portfolio_id=portfolio_id,
                name=name,
                description=description,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to create portfolio: {e}")
            raise

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """
        Get portfolio by ID

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Portfolio object or None if not found
        """
        try:
            result = self.db.execute(
                "SELECT * FROM portfolios WHERE portfolio_id = ?",
                [portfolio_id]
            ).fetchone()

            if result:
                return Portfolio(
                    portfolio_id=result[0],
                    name=result[1],
                    description=result[2],
                    created_at=result[3],
                    updated_at=result[4]
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get portfolio: {e}")
            return None

    def list_portfolios(self) -> List[Portfolio]:
        """
        List all portfolios

        Returns:
            List of Portfolio objects
        """
        try:
            results = self.db.execute(
                "SELECT * FROM portfolios ORDER BY created_at DESC"
            ).fetchall()

            portfolios = [
                Portfolio(
                    portfolio_id=row[0],
                    name=row[1],
                    description=row[2],
                    created_at=row[3],
                    updated_at=row[4]
                )
                for row in results
            ]

            return portfolios

        except Exception as e:
            logger.error(f"Failed to list portfolios: {e}")
            return []

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        Delete a portfolio and all its positions

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Check if exists
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                logger.warning(f"Portfolio not found: {portfolio_id}")
                return False

            # Delete positions first
            self.db.execute(
                "DELETE FROM portfolio_positions WHERE portfolio_id = ?",
                [portfolio_id]
            )

            # Delete portfolio
            self.db.execute(
                "DELETE FROM portfolios WHERE portfolio_id = ?",
                [portfolio_id]
            )

            logger.info(f"✓ Deleted portfolio: {portfolio_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete portfolio: {e}")
            return False

    def add_position(
        self,
        portfolio_id: str,
        ticker: str,
        weight: Optional[float] = None,
        shares: Optional[int] = None,
        cost_basis: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Position:
        """
        Add a position to portfolio

        Args:
            portfolio_id: Portfolio identifier
            ticker: Stock ticker symbol
            weight: Optional position weight (0.0 - 1.0)
            shares: Optional number of shares
            cost_basis: Optional cost basis per share
            notes: Optional notes

        Returns:
            Created Position object
        """
        try:
            # Verify portfolio exists
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio not found: {portfolio_id}")

            # Check if position already exists
            existing = self.get_position(portfolio_id, ticker)
            if existing:
                raise ValueError(f"Position for {ticker} already exists in {portfolio_id}")

            # Validate weight
            if weight is not None and not (0.0 <= weight <= 1.0):
                raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

            # Generate ID
            position_id = int(uuid.uuid4().int & (1 << 63) - 1)

            # Insert position
            self.db.execute(
                """
                INSERT INTO portfolio_positions
                (id, portfolio_id, ticker, weight, shares, cost_basis, entry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [position_id, portfolio_id, ticker.upper(), weight, shares, cost_basis, datetime.now().date(), notes]
            )

            # Update portfolio timestamp
            self.db.execute(
                "UPDATE portfolios SET updated_at = ? WHERE portfolio_id = ?",
                [datetime.now(), portfolio_id]
            )

            logger.info(f"✓ Added {ticker} to portfolio {portfolio_id}")

            return Position(
                id=position_id,
                portfolio_id=portfolio_id,
                ticker=ticker.upper(),
                weight=weight,
                shares=shares,
                cost_basis=cost_basis,
                entry_date=datetime.now().date(),
                notes=notes
            )

        except Exception as e:
            logger.error(f"Failed to add position: {e}")
            raise

    def get_position(self, portfolio_id: str, ticker: str) -> Optional[Position]:
        """
        Get a specific position

        Args:
            portfolio_id: Portfolio identifier
            ticker: Stock ticker

        Returns:
            Position object or None
        """
        try:
            result = self.db.execute(
                """
                SELECT * FROM portfolio_positions
                WHERE portfolio_id = ? AND ticker = ?
                """,
                [portfolio_id, ticker.upper()]
            ).fetchone()

            if result:
                return Position(
                    id=result[0],
                    portfolio_id=result[1],
                    ticker=result[2],
                    weight=result[3],
                    shares=result[4],
                    cost_basis=result[5],
                    entry_date=result[6],
                    notes=result[7]
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return None

    def list_positions(self, portfolio_id: str) -> List[Position]:
        """
        List all positions in a portfolio

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            List of Position objects
        """
        try:
            results = self.db.execute(
                """
                SELECT * FROM portfolio_positions
                WHERE portfolio_id = ?
                ORDER BY ticker
                """,
                [portfolio_id]
            ).fetchall()

            positions = [
                Position(
                    id=row[0],
                    portfolio_id=row[1],
                    ticker=row[2],
                    weight=row[3],
                    shares=row[4],
                    cost_basis=row[5],
                    entry_date=row[6],
                    notes=row[7]
                )
                for row in results
            ]

            return positions

        except Exception as e:
            logger.error(f"Failed to list positions: {e}")
            return []

    def remove_position(self, portfolio_id: str, ticker: str) -> bool:
        """
        Remove a position from portfolio

        Args:
            portfolio_id: Portfolio identifier
            ticker: Stock ticker

        Returns:
            True if removed, False otherwise
        """
        try:
            # Check if exists
            position = self.get_position(portfolio_id, ticker)
            if not position:
                logger.warning(f"Position not found: {ticker} in {portfolio_id}")
                return False

            # Delete position
            self.db.execute(
                """
                DELETE FROM portfolio_positions
                WHERE portfolio_id = ? AND ticker = ?
                """,
                [portfolio_id, ticker.upper()]
            )

            # Update portfolio timestamp
            self.db.execute(
                "UPDATE portfolios SET updated_at = ? WHERE portfolio_id = ?",
                [datetime.now(), portfolio_id]
            )

            logger.info(f"✓ Removed {ticker} from portfolio {portfolio_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove position: {e}")
            return False

    def update_position(
        self,
        portfolio_id: str,
        ticker: str,
        weight: Optional[float] = None,
        shares: Optional[int] = None,
        cost_basis: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update a position's attributes

        Args:
            portfolio_id: Portfolio identifier
            ticker: Stock ticker
            weight: Optional new weight
            shares: Optional new shares
            cost_basis: Optional new cost basis
            notes: Optional new notes

        Returns:
            True if updated, False otherwise
        """
        try:
            # Check if exists
            position = self.get_position(portfolio_id, ticker)
            if not position:
                logger.warning(f"Position not found: {ticker} in {portfolio_id}")
                return False

            # Build update query dynamically
            updates = []
            params = []

            if weight is not None:
                if not (0.0 <= weight <= 1.0):
                    raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")
                updates.append("weight = ?")
                params.append(weight)

            if shares is not None:
                updates.append("shares = ?")
                params.append(shares)

            if cost_basis is not None:
                updates.append("cost_basis = ?")
                params.append(cost_basis)

            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                logger.warning("No updates specified")
                return False

            # Add WHERE parameters
            params.extend([portfolio_id, ticker.upper()])

            # Execute update
            query = f"""
                UPDATE portfolio_positions
                SET {', '.join(updates)}
                WHERE portfolio_id = ? AND ticker = ?
            """

            self.db.execute(query, params)

            # Update portfolio timestamp
            self.db.execute(
                "UPDATE portfolios SET updated_at = ? WHERE portfolio_id = ?",
                [datetime.now(), portfolio_id]
            )

            logger.info(f"✓ Updated {ticker} in portfolio {portfolio_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update position: {e}")
            return False

    def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """
        Get portfolio summary with statistics

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Dictionary with portfolio summary
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return {}

            positions = self.list_positions(portfolio_id)

            summary = {
                "portfolio_id": portfolio.portfolio_id,
                "name": portfolio.name,
                "description": portfolio.description,
                "created_at": portfolio.created_at,
                "updated_at": portfolio.updated_at,
                "num_positions": len(positions),
                "tickers": [p.ticker for p in positions],
                "total_weight": sum(p.weight for p in positions if p.weight),
                "total_shares": sum(p.shares for p in positions if p.shares),
                "positions": positions
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {}
