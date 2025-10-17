"""
Watchlist Management Module

Provides functionality to:
- Save screening results as watchlists
- Track changes over time
- Set up alerts when stocks enter/exit screens
- Compare historical snapshots
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
import pandas as pd

from ..data.database import DatabaseManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class WatchlistItem:
    """Single stock in a watchlist"""
    ticker: str
    added_date: date
    price_when_added: Optional[float] = None
    score_when_added: Optional[float] = None
    reason: Optional[str] = None  # Why it was added
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class WatchlistSnapshot:
    """Snapshot of watchlist at a point in time"""
    watchlist_id: str
    snapshot_date: date
    tickers: List[str]
    metrics: Dict[str, Any]  # price, scores, etc.


class WatchlistManager:
    """
    Manage stock watchlists and track changes over time

    Features:
    - Create/update/delete watchlists
    - Save screening results as watchlists
    - Track historical changes
    - Alert configuration
    - Export/import watchlists
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize watchlist manager

        Args:
            db: Database manager
        """
        self.db = db
        self._ensure_tables_exist()
        logger.info("✓ Watchlist manager initialized")

    def _ensure_tables_exist(self):
        """Create watchlist tables if they don't exist"""
        # Watchlists table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR,
                created_date TIMESTAMP NOT NULL,
                last_updated TIMESTAMP NOT NULL,
                tags VARCHAR,  -- JSON array
                auto_update BOOLEAN DEFAULT FALSE,
                screen_criteria VARCHAR  -- JSON, for auto-updating watchlists
            )
        """)

        # Watchlist items table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id BIGINT PRIMARY KEY,
                watchlist_id VARCHAR NOT NULL,
                ticker VARCHAR NOT NULL,
                added_date TIMESTAMP NOT NULL,
                price_when_added DOUBLE,
                score_when_added DOUBLE,
                reason VARCHAR,
                notes VARCHAR,
                tags VARCHAR,  -- JSON array
                removed_date TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
            )
        """)

        # Watchlist snapshots (for tracking changes)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_snapshots (
                id BIGINT PRIMARY KEY,
                watchlist_id VARCHAR NOT NULL,
                snapshot_date TIMESTAMP NOT NULL,
                tickers VARCHAR NOT NULL,  -- JSON array
                metrics VARCHAR,  -- JSON object
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
            )
        """)

        # Watchlist alerts
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_alerts (
                id BIGINT PRIMARY KEY,
                watchlist_id VARCHAR NOT NULL,
                alert_type VARCHAR NOT NULL,  -- 'enters_screen', 'price_change', 'volume_spike'
                criteria VARCHAR NOT NULL,  -- JSON
                enabled BOOLEAN DEFAULT TRUE,
                last_triggered TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
            )
        """)

    def create_watchlist(
        self,
        watchlist_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_update: bool = False,
        screen_criteria: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new watchlist

        Args:
            watchlist_id: Unique identifier
            name: Display name
            description: Optional description
            tags: Optional tags for organization
            auto_update: Whether to auto-update from screening criteria
            screen_criteria: Optional criteria for auto-updating

        Returns:
            True if successful
        """
        try:
            now = datetime.now()

            self.db.execute(
                """
                INSERT INTO watchlists
                (id, name, description, created_date, last_updated, tags, auto_update, screen_criteria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    watchlist_id,
                    name,
                    description,
                    now,
                    now,
                    json.dumps(tags) if tags else None,
                    auto_update,
                    json.dumps(screen_criteria) if screen_criteria else None
                ]
            )

            logger.info(f"✓ Created watchlist: {watchlist_id} ({name})")
            return True

        except Exception as e:
            logger.error(f"Failed to create watchlist: {e}")
            return False

    def add_from_screen_results(
        self,
        watchlist_id: str,
        screen_results: pd.DataFrame,
        reason: str = "Screening result",
        merge: bool = False
    ) -> int:
        """
        Add stocks from screening results to watchlist

        Args:
            watchlist_id: Watchlist identifier
            screen_results: DataFrame from screener.screen()
            reason: Why these stocks were added
            merge: If True, merge with existing items. If False, replace all.

        Returns:
            Number of stocks added
        """
        try:
            import uuid

            # Check if watchlist exists
            watchlist = self.db.execute(
                "SELECT * FROM watchlists WHERE id = ?",
                [watchlist_id]
            ).fetchone()

            if not watchlist:
                logger.error(f"Watchlist not found: {watchlist_id}")
                return 0

            # Remove existing items if not merging
            if not merge:
                self.db.execute(
                    "DELETE FROM watchlist_items WHERE watchlist_id = ? AND removed_date IS NULL",
                    [watchlist_id]
                )

            # Add new items
            now = datetime.now()
            added_count = 0

            for _, row in screen_results.iterrows():
                item_id = int(uuid.uuid4().int & (1 << 63) - 1)

                self.db.execute(
                    """
                    INSERT INTO watchlist_items
                    (id, watchlist_id, ticker, added_date, price_when_added, score_when_added, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        item_id,
                        watchlist_id,
                        row['ticker'],
                        now,
                        float(row['price']) if 'price' in row and pd.notna(row['price']) else None,
                        float(row['score']) if 'score' in row and pd.notna(row['score']) else None,
                        reason
                    ]
                )
                added_count += 1

            # Update watchlist timestamp
            self.db.execute(
                "UPDATE watchlists SET last_updated = ? WHERE id = ?",
                [now, watchlist_id]
            )

            # Create snapshot
            self._create_snapshot(watchlist_id, screen_results)

            logger.info(f"✓ Added {added_count} stocks to watchlist: {watchlist_id}")
            return added_count

        except Exception as e:
            logger.error(f"Failed to add screen results to watchlist: {e}")
            return 0

    def get_watchlist(self, watchlist_id: str) -> Optional[pd.DataFrame]:
        """
        Get current watchlist items

        Args:
            watchlist_id: Watchlist identifier

        Returns:
            DataFrame with watchlist items
        """
        try:
            result = self.db.execute(
                """
                SELECT ticker, added_date, price_when_added, score_when_added, reason, notes
                FROM watchlist_items
                WHERE watchlist_id = ? AND removed_date IS NULL
                ORDER BY added_date DESC
                """,
                [watchlist_id]
            ).fetchall()

            if not result:
                return pd.DataFrame()

            df = pd.DataFrame(result, columns=[
                'ticker', 'added_date', 'price_when_added',
                'score_when_added', 'reason', 'notes'
            ])

            return df

        except Exception as e:
            logger.error(f"Failed to get watchlist: {e}")
            return None

    def list_watchlists(self) -> pd.DataFrame:
        """
        List all watchlists

        Returns:
            DataFrame with watchlist metadata
        """
        try:
            result = self.db.execute(
                """
                SELECT w.id, w.name, w.description, w.created_date, w.last_updated,
                       w.tags, COUNT(wi.ticker) as num_stocks
                FROM watchlists w
                LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id AND wi.removed_date IS NULL
                GROUP BY w.id, w.name, w.description, w.created_date, w.last_updated, w.tags
                ORDER BY w.last_updated DESC
                """
            ).fetchall()

            if not result:
                return pd.DataFrame()

            df = pd.DataFrame(result, columns=[
                'id', 'name', 'description', 'created_date',
                'last_updated', 'tags', 'num_stocks'
            ])

            # Parse tags JSON
            df['tags'] = df['tags'].apply(lambda x: json.loads(x) if x else [])

            return df

        except Exception as e:
            logger.error(f"Failed to list watchlists: {e}")
            return pd.DataFrame()

    def delete_watchlist(self, watchlist_id: str) -> bool:
        """
        Delete a watchlist and all its items

        Args:
            watchlist_id: Watchlist identifier

        Returns:
            True if successful
        """
        try:
            # Delete snapshots
            self.db.execute(
                "DELETE FROM watchlist_snapshots WHERE watchlist_id = ?",
                [watchlist_id]
            )

            # Delete alerts
            self.db.execute(
                "DELETE FROM watchlist_alerts WHERE watchlist_id = ?",
                [watchlist_id]
            )

            # Delete items
            self.db.execute(
                "DELETE FROM watchlist_items WHERE watchlist_id = ?",
                [watchlist_id]
            )

            # Delete watchlist
            self.db.execute(
                "DELETE FROM watchlists WHERE id = ?",
                [watchlist_id]
            )

            logger.info(f"✓ Deleted watchlist: {watchlist_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete watchlist: {e}")
            return False

    def _create_snapshot(self, watchlist_id: str, data: pd.DataFrame):
        """Create a snapshot of watchlist at current time"""
        try:
            import uuid

            now = datetime.now()
            snapshot_id = int(uuid.uuid4().int & (1 << 63) - 1)

            # Get tickers
            tickers = data['ticker'].tolist()

            # Get metrics (prices, scores, etc.)
            metrics = {}
            if 'price' in data.columns:
                metrics['prices'] = dict(zip(data['ticker'], data['price']))
            if 'score' in data.columns:
                metrics['scores'] = dict(zip(data['ticker'], data['score']))

            self.db.execute(
                """
                INSERT INTO watchlist_snapshots
                (id, watchlist_id, snapshot_date, tickers, metrics)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    snapshot_id,
                    watchlist_id,
                    now,
                    json.dumps(tickers),
                    json.dumps(metrics)
                ]
            )

        except Exception as e:
            logger.debug(f"Failed to create snapshot: {e}")

    def compare_snapshots(
        self,
        watchlist_id: str,
        date1: Optional[date] = None,
        date2: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Compare two snapshots of a watchlist

        Args:
            watchlist_id: Watchlist identifier
            date1: First date (default: oldest snapshot)
            date2: Second date (default: latest snapshot)

        Returns:
            Dictionary with comparison data
        """
        try:
            # Get snapshots
            query = """
                SELECT snapshot_date, tickers, metrics
                FROM watchlist_snapshots
                WHERE watchlist_id = ?
            """
            params = [watchlist_id]

            if date1:
                query += " AND snapshot_date >= ?"
                params.append(date1)

            query += " ORDER BY snapshot_date"

            snapshots = self.db.execute(query, params).fetchall()

            if len(snapshots) < 2:
                logger.warning("Need at least 2 snapshots to compare")
                return {}

            # Get first and last snapshot
            snap1 = snapshots[0]
            snap2 = snapshots[-1]

            tickers1 = set(json.loads(snap1[1]))
            tickers2 = set(json.loads(snap2[1]))

            added = tickers2 - tickers1
            removed = tickers1 - tickers2
            unchanged = tickers1 & tickers2

            # Price changes for unchanged tickers
            metrics1 = json.loads(snap1[2]) if snap1[2] else {}
            metrics2 = json.loads(snap2[2]) if snap2[2] else {}

            price_changes = {}
            if 'prices' in metrics1 and 'prices' in metrics2:
                for ticker in unchanged:
                    if ticker in metrics1['prices'] and ticker in metrics2['prices']:
                        old_price = metrics1['prices'][ticker]
                        new_price = metrics2['prices'][ticker]
                        if old_price and new_price:
                            change_pct = ((new_price - old_price) / old_price) * 100
                            price_changes[ticker] = {
                                'old': old_price,
                                'new': new_price,
                                'change_pct': round(change_pct, 2)
                            }

            comparison = {
                'date1': snap1[0],
                'date2': snap2[0],
                'added': sorted(list(added)),
                'removed': sorted(list(removed)),
                'unchanged': sorted(list(unchanged)),
                'price_changes': price_changes,
                'total_change': len(added) + len(removed)
            }

            logger.info(f"Snapshot comparison: +{len(added)} -{len(removed)} ={len(unchanged)}")
            return comparison

        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return {}

    def create_alert(
        self,
        watchlist_id: str,
        alert_type: str,
        criteria: Dict[str, Any]
    ) -> bool:
        """
        Create an alert for a watchlist

        Args:
            watchlist_id: Watchlist identifier
            alert_type: Type of alert ('enters_screen', 'price_change', 'volume_spike')
            criteria: Alert criteria (depends on type)

        Returns:
            True if successful

        Example:
            >>> manager.create_alert(
            ...     "my_watchlist",
            ...     "price_change",
            ...     {"change_pct": 10.0, "direction": "up"}
            ... )
        """
        try:
            import uuid

            alert_id = int(uuid.uuid4().int & (1 << 63) - 1)

            self.db.execute(
                """
                INSERT INTO watchlist_alerts
                (id, watchlist_id, alert_type, criteria, enabled)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    alert_id,
                    watchlist_id,
                    alert_type,
                    json.dumps(criteria),
                    True
                ]
            )

            logger.info(f"✓ Created alert for watchlist: {watchlist_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return False

    def export_watchlist(self, watchlist_id: str, output_path: str) -> bool:
        """
        Export watchlist to JSON file

        Args:
            watchlist_id: Watchlist identifier
            output_path: Path to save JSON file

        Returns:
            True if successful
        """
        try:
            # Get watchlist metadata
            watchlist = self.db.execute(
                "SELECT * FROM watchlists WHERE id = ?",
                [watchlist_id]
            ).fetchone()

            if not watchlist:
                logger.error(f"Watchlist not found: {watchlist_id}")
                return False

            # Get items
            items_df = self.get_watchlist(watchlist_id)

            # Convert to dict
            export_data = {
                'watchlist_id': watchlist_id,
                'name': watchlist[1],
                'description': watchlist[2],
                'created_date': str(watchlist[3]),
                'last_updated': str(watchlist[4]),
                'tags': json.loads(watchlist[5]) if watchlist[5] else [],
                'items': items_df.to_dict('records') if not items_df.empty else []
            }

            # Write to file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"✓ Exported watchlist to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export watchlist: {e}")
            return False
