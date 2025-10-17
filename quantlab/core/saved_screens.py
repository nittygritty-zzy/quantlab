"""
Saved Screens Manager

Allows saving, loading, and managing screening criteria as named templates.
Users can save frequently-used screens and reuse them quickly.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import pandas as pd

from ..data.database import DatabaseManager
from .screener import ScreenCriteria


logger = logging.getLogger(__name__)


class SavedScreenManager:
    """Manager for saved screening criteria"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._create_tables()

    def _create_tables(self):
        """Create saved_screens table if it doesn't exist"""
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS saved_screens (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    criteria JSON NOT NULL,
                    tags JSON,
                    created_date TIMESTAMP NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    last_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0
                )
            """)
            logger.info("Saved screens table initialized")
        except Exception as e:
            logger.error(f"Error creating saved_screens table: {e}")

    def save_screen(
        self,
        screen_id: str,
        name: str,
        criteria: ScreenCriteria,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Save screening criteria as a named template

        Args:
            screen_id: Unique identifier for the screen
            name: Display name
            criteria: ScreenCriteria object to save
            description: Optional description
            tags: Optional list of tags for categorization

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert ScreenCriteria to dict
            criteria_dict = self._criteria_to_dict(criteria)

            # Convert to JSON
            criteria_json = json.dumps(criteria_dict)
            tags_json = json.dumps(tags if tags else [])

            now = datetime.now()

            # Check if screen already exists
            existing = self.db.execute(
                "SELECT id FROM saved_screens WHERE id = ?",
                (screen_id,)
            ).fetchone()

            if existing:
                # Update existing screen
                self.db.execute("""
                    UPDATE saved_screens
                    SET name = ?,
                        description = ?,
                        criteria = ?,
                        tags = ?,
                        last_modified = ?
                    WHERE id = ?
                """, (name, description, criteria_json, tags_json, now, screen_id))
                logger.info(f"Updated saved screen: {screen_id}")
            else:
                # Insert new screen
                self.db.execute("""
                    INSERT INTO saved_screens (
                        id, name, description, criteria, tags,
                        created_date, last_modified, run_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """, (screen_id, name, description, criteria_json, tags_json, now, now))
                logger.info(f"Saved new screen: {screen_id}")

            return True

        except Exception as e:
            logger.error(f"Error saving screen {screen_id}: {e}")
            return False

    def load_screen(self, screen_id: str) -> Optional[ScreenCriteria]:
        """
        Load saved screening criteria

        Args:
            screen_id: ID of saved screen

        Returns:
            ScreenCriteria object if found, None otherwise
        """
        try:
            result = self.db.execute(
                "SELECT criteria FROM saved_screens WHERE id = ?",
                (screen_id,)
            ).fetchone()

            if not result:
                logger.warning(f"Screen not found: {screen_id}")
                return None

            criteria_dict = json.loads(result['criteria'])
            criteria = self._dict_to_criteria(criteria_dict)

            logger.info(f"Loaded screen: {screen_id}")
            return criteria

        except Exception as e:
            logger.error(f"Error loading screen {screen_id}: {e}")
            return None

    def list_screens(self) -> pd.DataFrame:
        """
        List all saved screens

        Returns:
            DataFrame with screen metadata
        """
        try:
            result = self.db.execute("""
                SELECT
                    id,
                    name,
                    description,
                    tags,
                    created_date,
                    last_modified,
                    last_run,
                    run_count
                FROM saved_screens
                ORDER BY last_modified DESC
            """).fetchall()

            if not result:
                return pd.DataFrame(columns=[
                    'id', 'name', 'description', 'tags', 'created_date',
                    'last_modified', 'last_run', 'run_count'
                ])

            # Convert to DataFrame - handle DuckDB rows
            data = []
            for row in result:
                # Convert row to dict using tuple unpacking
                data.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'tags': row[3],
                    'created_date': row[4],
                    'last_modified': row[5],
                    'last_run': row[6],
                    'run_count': row[7]
                })

            df = pd.DataFrame(data)

            # Parse JSON tags
            df['tags'] = df['tags'].apply(lambda x: json.loads(x) if x else [])

            return df

        except Exception as e:
            logger.error(f"Error listing screens: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def get_screen_info(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full information about a saved screen

        Args:
            screen_id: ID of saved screen

        Returns:
            Dict with screen metadata and criteria
        """
        try:
            result = self.db.execute("""
                SELECT
                    id, name, description, criteria, tags,
                    created_date, last_modified, last_run, run_count
                FROM saved_screens
                WHERE id = ?
            """, (screen_id,)).fetchone()

            if not result:
                return None

            # Convert DuckDB row to dict using tuple indexing
            info = {
                'id': result[0],
                'name': result[1],
                'description': result[2],
                'criteria': json.loads(result[3]) if result[3] else {},
                'tags': json.loads(result[4]) if result[4] else [],
                'created_date': result[5],
                'last_modified': result[6],
                'last_run': result[7],
                'run_count': result[8]
            }

            return info

        except Exception as e:
            logger.error(f"Error getting screen info for {screen_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def delete_screen(self, screen_id: str) -> bool:
        """
        Delete a saved screen

        Args:
            screen_id: ID of screen to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.db.execute("DELETE FROM saved_screens WHERE id = ?", (screen_id,))
            logger.info(f"Deleted screen: {screen_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting screen {screen_id}: {e}")
            return False

    def update_run_stats(self, screen_id: str):
        """
        Update run statistics when a screen is executed

        Args:
            screen_id: ID of screen that was run
        """
        try:
            now = datetime.now()
            self.db.execute("""
                UPDATE saved_screens
                SET last_run = ?,
                    run_count = run_count + 1
                WHERE id = ?
            """, (now, screen_id))

        except Exception as e:
            logger.error(f"Error updating run stats for {screen_id}: {e}")

    def export_screen(self, screen_id: str, output_path: str) -> bool:
        """
        Export a saved screen to JSON file

        Args:
            screen_id: ID of screen to export
            output_path: Path to save JSON file

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            info = self.get_screen_info(screen_id)

            if not info:
                logger.error(f"Screen not found: {screen_id}")
                return False

            # Create output directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(output_path, 'w') as f:
                json.dump(info, f, indent=2, default=str)

            logger.info(f"Exported screen {screen_id} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting screen {screen_id}: {e}")
            return False

    def import_screen(self, input_path: str, screen_id: Optional[str] = None) -> bool:
        """
        Import a screen from JSON file

        Args:
            input_path: Path to JSON file
            screen_id: Optional new ID (uses file's ID if not provided)

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(input_path, 'r') as f:
                info = json.load(f)

            # Use provided ID or file's ID
            new_id = screen_id or info['id']

            # Convert criteria dict to ScreenCriteria
            criteria = self._dict_to_criteria(info['criteria'])

            # Save screen
            return self.save_screen(
                screen_id=new_id,
                name=info['name'],
                criteria=criteria,
                description=info.get('description'),
                tags=info.get('tags')
            )

        except Exception as e:
            logger.error(f"Error importing screen from {input_path}: {e}")
            return False

    def _criteria_to_dict(self, criteria: ScreenCriteria) -> Dict[str, Any]:
        """Convert ScreenCriteria to dictionary for JSON storage"""
        return {
            'rsi_min': criteria.rsi_min,
            'rsi_max': criteria.rsi_max,
            'macd_signal': criteria.macd_signal,
            'sma_crossover': criteria.sma_crossover,
            'price_above_sma20': criteria.price_above_sma20,
            'price_above_sma50': criteria.price_above_sma50,
            'bb_position': criteria.bb_position,
            'adx_min': criteria.adx_min,
            'adx_max': criteria.adx_max,
            'volume_min': criteria.volume_min,
            'volume_max': criteria.volume_max,
            'price_min': criteria.price_min,
            'price_max': criteria.price_max,
            'pe_min': criteria.pe_min,
            'pe_max': criteria.pe_max,
            'forward_pe_min': criteria.forward_pe_min,
            'forward_pe_max': criteria.forward_pe_max,
            'peg_ratio_max': criteria.peg_ratio_max,
            'revenue_growth_min': criteria.revenue_growth_min,
            'revenue_growth_max': criteria.revenue_growth_max,
            'earnings_growth_min': criteria.earnings_growth_min,
            'earnings_growth_max': criteria.earnings_growth_max,
            'profit_margin_min': criteria.profit_margin_min,
            'profit_margin_max': criteria.profit_margin_max,
            'roe_min': criteria.roe_min,
            'roe_max': criteria.roe_max,
            'debt_equity_min': criteria.debt_equity_min,
            'debt_equity_max': criteria.debt_equity_max,
            'current_ratio_min': criteria.current_ratio_min,
            'market_cap_min': criteria.market_cap_min,
            'market_cap_max': criteria.market_cap_max,
            'min_analysts': criteria.min_analysts,
            'recommendation': criteria.recommendation,
            'sentiment_min': criteria.sentiment_min,
            'sentiment_max': criteria.sentiment_max,
            'articles_min': criteria.articles_min,
            'avg_volume_min': criteria.avg_volume_min,
            'sectors': criteria.sectors,
            'industries': criteria.industries,
            'exclude_sectors': criteria.exclude_sectors,
            'exclude_industries': criteria.exclude_industries
        }

    def _dict_to_criteria(self, data: Dict[str, Any]) -> ScreenCriteria:
        """Convert dictionary to ScreenCriteria object"""
        return ScreenCriteria(
            rsi_min=data.get('rsi_min'),
            rsi_max=data.get('rsi_max'),
            macd_signal=data.get('macd_signal'),
            sma_crossover=data.get('sma_crossover'),
            price_above_sma20=data.get('price_above_sma20'),
            price_above_sma50=data.get('price_above_sma50'),
            bb_position=data.get('bb_position'),
            adx_min=data.get('adx_min'),
            adx_max=data.get('adx_max'),
            volume_min=data.get('volume_min'),
            volume_max=data.get('volume_max'),
            price_min=data.get('price_min'),
            price_max=data.get('price_max'),
            pe_min=data.get('pe_min'),
            pe_max=data.get('pe_max'),
            forward_pe_min=data.get('forward_pe_min'),
            forward_pe_max=data.get('forward_pe_max'),
            peg_ratio_max=data.get('peg_ratio_max'),
            revenue_growth_min=data.get('revenue_growth_min'),
            revenue_growth_max=data.get('revenue_growth_max'),
            earnings_growth_min=data.get('earnings_growth_min'),
            earnings_growth_max=data.get('earnings_growth_max'),
            profit_margin_min=data.get('profit_margin_min'),
            profit_margin_max=data.get('profit_margin_max'),
            roe_min=data.get('roe_min'),
            roe_max=data.get('roe_max'),
            debt_equity_min=data.get('debt_equity_min'),
            debt_equity_max=data.get('debt_equity_max'),
            current_ratio_min=data.get('current_ratio_min'),
            market_cap_min=data.get('market_cap_min'),
            market_cap_max=data.get('market_cap_max'),
            min_analysts=data.get('min_analysts'),
            recommendation=data.get('recommendation'),
            sentiment_min=data.get('sentiment_min'),
            sentiment_max=data.get('sentiment_max'),
            articles_min=data.get('articles_min'),
            avg_volume_min=data.get('avg_volume_min'),
            sectors=data.get('sectors'),
            industries=data.get('industries'),
            exclude_sectors=data.get('exclude_sectors'),
            exclude_industries=data.get('exclude_industries')
        )
