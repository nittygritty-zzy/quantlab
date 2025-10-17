"""
Screen Watcher Module

Real-time monitoring of screening criteria with alerts when stocks enter/exit screens.
Supports scheduled execution and multiple notification channels.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import json

import pandas as pd

from ..data.database import DatabaseManager
from .screener import ScreenCriteria, StockScreener
from .saved_screens import SavedScreenManager

logger = logging.getLogger(__name__)


@dataclass
class WatchAlert:
    """Alert from watch session"""
    ticker: str
    alert_type: str  # 'entry', 'exit', 'price_change', 'volume_spike'
    alert_time: datetime
    details: Dict[str, Any]
    screen_name: str


class ScreenWatcher:
    """Monitor screening criteria with real-time alerts"""

    def __init__(
        self,
        db: DatabaseManager,
        screener: StockScreener,
        saved_mgr: SavedScreenManager
    ):
        """
        Initialize screen watcher

        Args:
            db: Database manager
            screener: Stock screener instance
            saved_mgr: Saved screen manager
        """
        self.db = db
        self.screener = screener
        self.saved_mgr = saved_mgr
        self._create_tables()

        logger.info("✓ Screen watcher initialized")

    def _create_tables(self):
        """Create watch-related database tables"""
        try:
            # Watch sessions table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS screen_watch_sessions (
                    id VARCHAR PRIMARY KEY,
                    screen_id VARCHAR NOT NULL,
                    screen_name VARCHAR NOT NULL,
                    interval_seconds INTEGER NOT NULL,
                    alert_on JSON NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    status VARCHAR NOT NULL,
                    alert_count INTEGER DEFAULT 0,
                    run_count INTEGER DEFAULT 0
                )
            """)

            # Watch alerts table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS screen_watch_alerts (
                    id INTEGER PRIMARY KEY,
                    session_id VARCHAR NOT NULL,
                    ticker VARCHAR NOT NULL,
                    alert_type VARCHAR NOT NULL,
                    alert_time TIMESTAMP NOT NULL,
                    details JSON,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            """)

            # Watch state table (tracks last known screen results)
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS screen_watch_state (
                    session_id VARCHAR NOT NULL,
                    ticker VARCHAR NOT NULL,
                    last_seen TIMESTAMP NOT NULL,
                    last_price DOUBLE,
                    last_volume BIGINT,
                    metadata JSON,
                    PRIMARY KEY (session_id, ticker)
                )
            """)

            logger.info("Watch tables initialized")

        except Exception as e:
            logger.error(f"Error creating watch tables: {e}")

    def start_watch(
        self,
        screen_id: str,
        interval: str = '1h',
        alert_on: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Start monitoring a saved screen

        Args:
            screen_id: ID of saved screen to monitor
            interval: Check interval ('15m', '1h', '4h', '1d')
            alert_on: Alert types ['entry', 'exit', 'price_change', 'volume_spike']
            session_id: Optional custom session ID

        Returns:
            Session ID if successful, None otherwise
        """
        try:
            # Validate screen exists
            criteria = self.saved_mgr.load_screen(screen_id)
            if not criteria:
                logger.error(f"Screen not found: {screen_id}")
                return None

            screen_info = self.saved_mgr.get_screen_info(screen_id)
            screen_name = screen_info['name']

            # Parse interval
            interval_seconds = self._parse_interval(interval)
            if not interval_seconds:
                logger.error(f"Invalid interval: {interval}")
                return None

            # Default alert types
            if not alert_on:
                alert_on = ['entry', 'exit']

            # Generate session ID
            if not session_id:
                session_id = f"{screen_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Create watch session
            now = datetime.now()
            next_run = now + timedelta(seconds=interval_seconds)

            self.db.execute("""
                INSERT INTO screen_watch_sessions (
                    id, screen_id, screen_name, interval_seconds, alert_on,
                    started_at, next_run, status, alert_count, run_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 0, 0)
            """, (
                session_id,
                screen_id,
                screen_name,
                interval_seconds,
                json.dumps(alert_on),
                now,
                next_run
            ))

            # Run initial screen to establish baseline
            self._run_watch_check(session_id, screen_id, criteria, alert_on, initial=True)

            logger.info(f"Started watch session: {session_id}")
            logger.info(f"  Screen: {screen_name}")
            logger.info(f"  Interval: {interval}")
            logger.info(f"  Next run: {next_run}")

            return session_id

        except Exception as e:
            logger.error(f"Failed to start watch: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def stop_watch(self, session_id: str) -> bool:
        """
        Stop a watch session

        Args:
            session_id: Session ID to stop

        Returns:
            True if successful
        """
        try:
            self.db.execute("""
                UPDATE screen_watch_sessions
                SET status = 'stopped'
                WHERE id = ?
            """, (session_id,))

            logger.info(f"Stopped watch session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop watch: {e}")
            return False

    def run_watch_cycle(self, max_runs: Optional[int] = None) -> int:
        """
        Run one cycle of watch checks (check all active sessions)

        Args:
            max_runs: Maximum number of sessions to check (None = all)

        Returns:
            Number of sessions checked
        """
        try:
            # Get active sessions due for checking
            result = self.db.execute("""
                SELECT
                    id, screen_id, interval_seconds, alert_on
                FROM screen_watch_sessions
                WHERE status = 'active'
                AND (next_run IS NULL OR next_run <= ?)
                ORDER BY next_run
            """, (datetime.now(),)).fetchall()

            if not result:
                return 0

            sessions_checked = 0

            for row in result:
                if max_runs and sessions_checked >= max_runs:
                    break

                session_id = row[0]
                screen_id = row[1]
                interval_seconds = row[2]
                alert_on = json.loads(row[3]) if row[3] else ['entry', 'exit']

                # Load criteria
                criteria = self.saved_mgr.load_screen(screen_id)
                if not criteria:
                    logger.warning(f"Screen not found for session {session_id}, skipping")
                    continue

                # Run check
                self._run_watch_check(session_id, screen_id, criteria, alert_on)

                # Update next run time
                next_run = datetime.now() + timedelta(seconds=interval_seconds)
                self.db.execute("""
                    UPDATE screen_watch_sessions
                    SET last_run = ?,
                        next_run = ?,
                        run_count = run_count + 1
                    WHERE id = ?
                """, (datetime.now(), next_run, session_id))

                sessions_checked += 1

            logger.info(f"Checked {sessions_checked} watch sessions")
            return sessions_checked

        except Exception as e:
            logger.error(f"Error running watch cycle: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0

    def _run_watch_check(
        self,
        session_id: str,
        screen_id: str,
        criteria: ScreenCriteria,
        alert_on: List[str],
        initial: bool = False
    ):
        """Run screening and compare to previous state"""
        try:
            # Run screen
            results = self.screener.screen(criteria, limit=100, workers=2)

            if results.empty:
                logger.debug(f"No results for session {session_id}")
                current_tickers = set()
            else:
                current_tickers = set(results['ticker'].tolist())

            # Get previous state
            if not initial:
                prev_state = self._get_watch_state(session_id)
                prev_tickers = set(prev_state.keys())

                # Detect entry/exit
                if 'entry' in alert_on:
                    new_tickers = current_tickers - prev_tickers
                    for ticker in new_tickers:
                        self._create_alert(
                            session_id,
                            ticker,
                            'entry',
                            {'message': f"{ticker} entered screen"}
                        )

                if 'exit' in alert_on:
                    removed_tickers = prev_tickers - current_tickers
                    for ticker in removed_tickers:
                        self._create_alert(
                            session_id,
                            ticker,
                            'exit',
                            {'message': f"{ticker} exited screen"}
                        )

                # Detect price/volume changes
                if 'price_change' in alert_on or 'volume_spike' in alert_on:
                    for ticker in current_tickers & prev_tickers:
                        if ticker not in results['ticker'].values:
                            continue

                        current_data = results[results['ticker'] == ticker].iloc[0]
                        prev_data = prev_state[ticker]

                        if 'price_change' in alert_on:
                            self._check_price_change(
                                session_id, ticker, current_data, prev_data
                            )

                        if 'volume_spike' in alert_on:
                            self._check_volume_spike(
                                session_id, ticker, current_data, prev_data
                            )

            # Update state
            self._update_watch_state(session_id, results)

        except Exception as e:
            logger.error(f"Error in watch check for {session_id}: {e}")

    def _get_watch_state(self, session_id: str) -> Dict[str, Dict]:
        """Get previous watch state"""
        try:
            result = self.db.execute("""
                SELECT ticker, last_price, last_volume, metadata
                FROM screen_watch_state
                WHERE session_id = ?
            """, (session_id,)).fetchall()

            state = {}
            for row in result:
                state[row[0]] = {
                    'price': row[1],
                    'volume': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                }

            return state

        except Exception as e:
            logger.error(f"Error getting watch state: {e}")
            return {}

    def _update_watch_state(self, session_id: str, results: pd.DataFrame):
        """Update watch state with current results"""
        try:
            # Clear previous state
            self.db.execute(
                "DELETE FROM screen_watch_state WHERE session_id = ?",
                (session_id,)
            )

            # Insert new state
            if not results.empty:
                now = datetime.now()
                for _, row in results.iterrows():
                    metadata = {
                        'name': row.get('name', ''),
                        'sector': row.get('sector', ''),
                        'score': float(row.get('composite_score', 0)) if 'composite_score' in row else None
                    }

                    self.db.execute("""
                        INSERT INTO screen_watch_state (
                            session_id, ticker, last_seen, last_price, last_volume, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        row['ticker'],
                        now,
                        float(row.get('price', 0)) if 'price' in row else None,
                        int(row.get('volume', 0)) if 'volume' in row else None,
                        json.dumps(metadata)
                    ))

        except Exception as e:
            logger.error(f"Error updating watch state: {e}")

    def _check_price_change(
        self,
        session_id: str,
        ticker: str,
        current_data: pd.Series,
        prev_data: Dict
    ):
        """Check for significant price changes"""
        try:
            current_price = current_data.get('price')
            prev_price = prev_data.get('price')

            if current_price and prev_price:
                change_pct = ((current_price - prev_price) / prev_price) * 100

                # Alert if > 5% change
                if abs(change_pct) >= 5:
                    self._create_alert(
                        session_id,
                        ticker,
                        'price_change',
                        {
                            'old_price': prev_price,
                            'new_price': current_price,
                            'change_pct': change_pct,
                            'message': f"{ticker} price changed {change_pct:+.1f}%"
                        }
                    )

        except Exception as e:
            logger.debug(f"Error checking price change: {e}")

    def _check_volume_spike(
        self,
        session_id: str,
        ticker: str,
        current_data: pd.Series,
        prev_data: Dict
    ):
        """Check for volume spikes"""
        try:
            current_volume = current_data.get('volume')
            prev_volume = prev_data.get('volume')

            if current_volume and prev_volume and prev_volume > 0:
                volume_ratio = current_volume / prev_volume

                # Alert if volume > 2x previous
                if volume_ratio >= 2.0:
                    self._create_alert(
                        session_id,
                        ticker,
                        'volume_spike',
                        {
                            'old_volume': prev_volume,
                            'new_volume': current_volume,
                            'ratio': volume_ratio,
                            'message': f"{ticker} volume spike: {volume_ratio:.1f}x"
                        }
                    )

        except Exception as e:
            logger.debug(f"Error checking volume spike: {e}")

    def _create_alert(
        self,
        session_id: str,
        ticker: str,
        alert_type: str,
        details: Dict
    ):
        """Create an alert record"""
        try:
            self.db.execute("""
                INSERT INTO screen_watch_alerts (
                    session_id, ticker, alert_type, alert_time, details, acknowledged
                ) VALUES (?, ?, ?, ?, ?, FALSE)
            """, (
                session_id,
                ticker,
                alert_type,
                datetime.now(),
                json.dumps(details)
            ))

            # Update alert count
            self.db.execute("""
                UPDATE screen_watch_sessions
                SET alert_count = alert_count + 1
                WHERE id = ?
            """, (session_id,))

            logger.info(f"Alert: {details.get('message', f'{ticker} {alert_type}')}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    def get_active_watches(self) -> pd.DataFrame:
        """Get all active watch sessions"""
        try:
            result = self.db.execute("""
                SELECT
                    id,
                    screen_name,
                    interval_seconds,
                    started_at,
                    last_run,
                    next_run,
                    alert_count,
                    run_count,
                    status
                FROM screen_watch_sessions
                WHERE status = 'active'
                ORDER BY started_at DESC
            """).fetchall()

            if not result:
                return pd.DataFrame()

            data = []
            for row in result:
                data.append({
                    'session_id': row[0],
                    'screen_name': row[1],
                    'interval': self._format_interval(row[2]),
                    'started': row[3],
                    'last_run': row[4],
                    'next_run': row[5],
                    'alerts': row[6],
                    'runs': row[7],
                    'status': row[8]
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error getting active watches: {e}")
            return pd.DataFrame()

    def get_alerts(
        self,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        unacknowledged_only: bool = False
    ) -> pd.DataFrame:
        """
        Get alerts from watch sessions

        Args:
            session_id: Filter by session ID (None = all sessions)
            since: Get alerts since this datetime (None = all)
            unacknowledged_only: Only show unacknowledged alerts

        Returns:
            DataFrame with alerts
        """
        try:
            query = """
                SELECT
                    a.id,
                    a.session_id,
                    s.screen_name,
                    a.ticker,
                    a.alert_type,
                    a.alert_time,
                    a.details,
                    a.acknowledged
                FROM screen_watch_alerts a
                JOIN screen_watch_sessions s ON a.session_id = s.id
                WHERE 1=1
            """
            params = []

            if session_id:
                query += " AND a.session_id = ?"
                params.append(session_id)

            if since:
                query += " AND a.alert_time >= ?"
                params.append(since)

            if unacknowledged_only:
                query += " AND a.acknowledged = FALSE"

            query += " ORDER BY a.alert_time DESC"

            result = self.db.execute(query, tuple(params)).fetchall()

            if not result:
                return pd.DataFrame()

            data = []
            for row in result:
                details = json.loads(row[6]) if row[6] else {}

                data.append({
                    'alert_id': row[0],
                    'session_id': row[1],
                    'screen_name': row[2],
                    'ticker': row[3],
                    'alert_type': row[4],
                    'alert_time': row[5],
                    'message': details.get('message', ''),
                    'acknowledged': row[7]
                })

            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return pd.DataFrame()

    def acknowledge_alerts(self, alert_ids: Optional[List[int]] = None, session_id: Optional[str] = None):
        """Mark alerts as acknowledged"""
        try:
            if alert_ids:
                placeholders = ','.join('?' * len(alert_ids))
                self.db.execute(f"""
                    UPDATE screen_watch_alerts
                    SET acknowledged = TRUE
                    WHERE id IN ({placeholders})
                """, tuple(alert_ids))

            elif session_id:
                self.db.execute("""
                    UPDATE screen_watch_alerts
                    SET acknowledged = TRUE
                    WHERE session_id = ?
                """, (session_id,))

        except Exception as e:
            logger.error(f"Error acknowledging alerts: {e}")

    def _parse_interval(self, interval: str) -> Optional[int]:
        """Parse interval string to seconds"""
        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400
        }

        try:
            value = int(interval[:-1])
            unit = interval[-1]
            return value * multipliers.get(unit, 0)
        except:
            return None

    def _format_interval(self, seconds: int) -> str:
        """Format seconds as interval string"""
        if seconds >= 86400:
            return f"{seconds // 86400}d"
        elif seconds >= 3600:
            return f"{seconds // 3600}h"
        elif seconds >= 60:
            return f"{seconds // 60}m"
        else:
            return f"{seconds}s"
