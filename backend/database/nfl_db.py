"""
NFL Database Manager
Handles all database operations for NFL team stats, games, odds, and trends
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NFLDatabase:
    """
    SQLite database manager for NFL data
    Stores: team stats, games, betting odds, trends, predictions
    """

    def __init__(self, db_path='backend/data/nfl_stats.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self.create_tables()
        logger.info(f"NFL Database initialized at {db_path}")

    def create_tables(self):
        """Create all NFL tables if they don't exist"""
        cursor = self.conn.cursor()

        # Table 1: NFL Team Stats (Historical snapshots)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_team_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name VARCHAR(100) NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Record
                wins INTEGER,
                losses INTEGER,
                ties INTEGER,

                -- TIER 1: Critical Offensive Stats
                points_per_game REAL,
                yards_per_play REAL,
                red_zone_scoring_pct REAL,
                turnovers_per_game REAL,

                -- TIER 2: Important Offensive Stats
                total_yards_per_game REAL,
                passing_yards_per_game REAL,
                rushing_yards_per_game REAL,
                completion_pct REAL,
                fourth_down_conversion_pct REAL,
                interceptions_thrown_per_game REAL,
                fumbles_lost_per_game REAL,
                offensive_touchdowns_per_game REAL,

                -- TIER 3: Detail Offensive Stats
                passing_touchdowns_per_game REAL,
                rushing_touchdowns_per_game REAL,
                total_touchdowns_per_game REAL,
                pass_attempts_per_game REAL,
                rush_attempts_per_game REAL,
                plays_per_game REAL,
                penalty_yards_per_game REAL,
                two_point_conversion_pct REAL,
                qb_sacked_per_game REAL,

                -- TIER 1: Critical Defensive Stats
                opponent_points_per_game REAL,
                opponent_yards_per_play REAL,
                opponent_red_zone_scoring_pct REAL,

                -- TIER 2: Important Defensive Stats
                opponent_total_yards_per_game REAL,
                opponent_passing_yards_per_game REAL,
                opponent_rushing_yards_per_game REAL,
                opponent_completion_pct REAL,
                opponent_fourth_down_conversion_pct REAL,
                sacks_per_game REAL,
                interceptions_per_game REAL,
                defensive_touchdowns_per_game REAL,

                -- TIER 3: Detail Defensive Stats
                opponent_passing_touchdowns_per_game REAL,
                opponent_rushing_touchdowns_per_game REAL,
                opponent_pass_attempts_per_game REAL,
                opponent_rush_attempts_per_game REAL,
                opponent_plays_per_game REAL,
                opponent_first_downs_per_game REAL,

                -- ESPN FPI Ratings (Efficiency)
                fpi_rating REAL,
                fpi_offensive_rating REAL,
                fpi_defensive_rating REAL,
                fpi_special_teams_rating REAL,

                -- Rankings (1-32)
                points_per_game_rank INTEGER,
                yards_per_play_rank INTEGER,
                red_zone_scoring_pct_rank INTEGER,
                completion_pct_rank INTEGER,
                fourth_down_conversion_pct_rank INTEGER,
                interceptions_thrown_per_game_rank INTEGER,
                fumbles_lost_per_game_rank INTEGER,
                offensive_touchdowns_per_game_rank INTEGER,
                passing_touchdowns_per_game_rank INTEGER,
                rushing_touchdowns_per_game_rank INTEGER,
                total_touchdowns_per_game_rank INTEGER,
                pass_attempts_per_game_rank INTEGER,
                rush_attempts_per_game_rank INTEGER,
                plays_per_game_rank INTEGER,
                penalty_yards_per_game_rank INTEGER,
                qb_sacked_per_game_rank INTEGER,
                opponent_points_per_game_rank INTEGER,
                opponent_yards_per_play_rank INTEGER,
                opponent_red_zone_scoring_pct_rank INTEGER,
                opponent_completion_pct_rank INTEGER,
                opponent_fourth_down_conversion_pct_rank INTEGER,
                sacks_per_game_rank INTEGER,
                interceptions_per_game_rank INTEGER,
                defensive_touchdowns_per_game_rank INTEGER,
                opponent_passing_touchdowns_per_game_rank INTEGER,
                opponent_rushing_touchdowns_per_game_rank INTEGER,
                opponent_first_downs_per_game_rank INTEGER
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_team_season
            ON nfl_team_stats(team_name, season)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scraped_at
            ON nfl_team_stats(scraped_at DESC)
        ''')

        # Table 2: NFL Games
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id VARCHAR(100) UNIQUE NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER,

                -- Teams
                home_team VARCHAR(100) NOT NULL,
                away_team VARCHAR(100) NOT NULL,

                -- Game Info
                commence_time TIMESTAMP,
                status VARCHAR(50),

                -- Score (NULL until game completes)
                home_score INTEGER,
                away_score INTEGER,

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_date
            ON nfl_games(commence_time)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_teams
            ON nfl_games(home_team, away_team)
        ''')

        # Table 3: Betting Odds (Historical tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_betting_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id VARCHAR(100) NOT NULL,
                bookmaker VARCHAR(100) NOT NULL,
                market_type VARCHAR(50) NOT NULL,

                -- Moneyline
                home_price REAL,
                away_price REAL,

                -- Spread
                home_spread REAL,
                home_spread_price REAL,
                away_spread REAL,
                away_spread_price REAL,

                -- Totals
                over_under_point REAL,
                over_price REAL,
                under_price REAL,

                -- Metadata
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_odds_game
            ON nfl_betting_odds(game_id, fetched_at DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_odds_bookmaker
            ON nfl_betting_odds(bookmaker)
        ''')

        # Table 4: Betting Trends
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_betting_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name VARCHAR(100) NOT NULL,
                season INTEGER NOT NULL,

                -- Win Trends (keep for compatibility)
                win_pct REAL,
                home_win_pct REAL,
                away_win_pct REAL,
                favorite_win_pct REAL,
                underdog_win_pct REAL,
                win_streak INTEGER,
                loss_streak INTEGER,

                -- ATS Trends (Granular from Calculator)
                ats_wins INTEGER DEFAULT 0,
                ats_losses INTEGER DEFAULT 0,
                ats_pushes INTEGER DEFAULT 0,
                ats_win_pct REAL,

                home_ats_wins INTEGER DEFAULT 0,
                home_ats_losses INTEGER DEFAULT 0,
                home_ats_pushes INTEGER DEFAULT 0,

                away_ats_wins INTEGER DEFAULT 0,
                away_ats_losses INTEGER DEFAULT 0,
                away_ats_pushes INTEGER DEFAULT 0,

                ats_last_5 TEXT,  -- JSON array: [1, 0, 1, 1, 0]
                ats_last_10 TEXT, -- JSON array

                -- O/U Trends (Granular from Calculator)
                ou_overs INTEGER DEFAULT 0,
                ou_unders INTEGER DEFAULT 0,
                ou_pushes INTEGER DEFAULT 0,
                ou_over_pct REAL,

                home_ou_overs INTEGER DEFAULT 0,
                home_ou_unders INTEGER DEFAULT 0,
                home_ou_pushes INTEGER DEFAULT 0,

                away_ou_overs INTEGER DEFAULT 0,
                away_ou_unders INTEGER DEFAULT 0,
                away_ou_pushes INTEGER DEFAULT 0,

                ou_last_5 TEXT,   -- JSON array: [1, 0, 1, 1, 0]
                ou_last_10 TEXT,  -- JSON array

                -- Legacy fields (keep for compatibility)
                ats_record VARCHAR(20),
                ats_pct REAL,
                home_ats_pct REAL,
                away_ats_pct REAL,
                favorite_ats_pct REAL,
                underdog_ats_pct REAL,
                ats_margin REAL,
                over_under_record VARCHAR(20),
                over_pct REAL,
                home_over_pct REAL,
                away_over_pct REAL,
                average_total REAL,
                average_team_total REAL,

                -- Analytics
                games_analyzed INTEGER DEFAULT 0,

                -- Metadata
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated VARCHAR(20)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trends_team
            ON nfl_betting_trends(team_name, season)
        ''')

        # Table 5: Predictions (Future ML models)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfl_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id VARCHAR(100) NOT NULL,
                model_name VARCHAR(100) NOT NULL,

                -- Predictions
                predicted_home_score REAL,
                predicted_away_score REAL,
                predicted_total REAL,
                predicted_spread REAL,
                confidence_level VARCHAR(20),

                -- Edge Calculations
                predicted_total_vs_line REAL,
                edge_size REAL,
                bet_recommendation VARCHAR(20),

                -- Metadata
                predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_game
            ON nfl_predictions(game_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_model
            ON nfl_predictions(model_name, predicted_at DESC)
        ''')

        self.conn.commit()
        logger.info("All NFL database tables created successfully")

    # ==================== TEAM STATS METHODS ====================

    def insert_team_stats_simple(self, team_name: str, season: int, scraper_stats: Dict) -> int:
        """
        Simplified insert that works directly with TeamRankings scraper output
        Maps scraper field names to database field names automatically
        """
        cursor = self.conn.cursor()

        try:
            # Map scraper output to database fields
            db_stats = {
                'team_name': team_name,
                'season': season,
                'week': None,
                'wins': scraper_stats.get('wins'),
                'losses': scraper_stats.get('losses'),
                'ties': 0,  # NFL rarely has ties
                # Offensive
                'points_per_game': scraper_stats.get('pts_per_game'),
                'yards_per_play': scraper_stats.get('yards_per_play'),
                'red_zone_scoring_pct': scraper_stats.get('red_zone_scoring_pct'),
                'turnovers_per_game': scraper_stats.get('turnovers_lost'),
                'total_yards_per_game': scraper_stats.get('yards_per_game'),
                'passing_yards_per_game': scraper_stats.get('passing_yards_per_game'),
                'rushing_yards_per_game': scraper_stats.get('rushing_yards_per_game'),
                'completion_pct': scraper_stats.get('completion_pct'),
                'fourth_down_conversion_pct': scraper_stats.get('fourth_down_conversion_pct'),
                'interceptions_thrown_per_game': scraper_stats.get('interceptions_thrown_per_game'),
                'fumbles_lost_per_game': scraper_stats.get('fumbles_lost_per_game'),
                'offensive_touchdowns_per_game': scraper_stats.get('offensive_touchdowns_per_game'),
                'passing_touchdowns_per_game': scraper_stats.get('passing_touchdowns_per_game'),
                'rushing_touchdowns_per_game': scraper_stats.get('rushing_touchdowns_per_game'),
                'total_touchdowns_per_game': scraper_stats.get('touchdowns_per_game'),
                'pass_attempts_per_game': scraper_stats.get('pass_attempts_per_game'),
                'rush_attempts_per_game': scraper_stats.get('rushing_attempts_per_game'),
                'plays_per_game': scraper_stats.get('plays_per_game'),
                'penalty_yards_per_game': scraper_stats.get('penalty_yards_per_game'),
                'two_point_conversion_pct': scraper_stats.get('two_point_conversion_pct'),
                'qb_sacked_per_game': scraper_stats.get('qb_sacked_per_game'),
                # Defensive
                'opponent_points_per_game': scraper_stats.get('pts_allowed'),
                'opponent_yards_per_play': scraper_stats.get('opponent_yards_per_play'),
                'opponent_red_zone_scoring_pct': scraper_stats.get('opponent_red_zone_scoring_pct'),
                'opponent_total_yards_per_game': scraper_stats.get('yards_allowed'),
                'opponent_passing_yards_per_game': scraper_stats.get('opponent_passing_yards_per_game'),
                'opponent_rushing_yards_per_game': scraper_stats.get('opponent_rushing_yards_per_game'),
                'opponent_completion_pct': scraper_stats.get('opponent_completion_pct'),
                'opponent_fourth_down_conversion_pct': scraper_stats.get('opponent_fourth_down_conversion_pct'),
                'sacks_per_game': scraper_stats.get('sacks_per_game'),
                'interceptions_per_game': scraper_stats.get('interceptions_per_game'),
                'defensive_touchdowns_per_game': scraper_stats.get('defensive_touchdowns_per_game'),
                'opponent_passing_touchdowns_per_game': scraper_stats.get('opponent_passing_touchdowns_per_game'),
                'opponent_rushing_touchdowns_per_game': scraper_stats.get('opponent_rushing_touchdowns_per_game'),
                'opponent_pass_attempts_per_game': scraper_stats.get('opponent_pass_attempts_per_game'),
                'opponent_rush_attempts_per_game': scraper_stats.get('opponent_rushing_attempts_per_game'),
                'opponent_plays_per_game': scraper_stats.get('opponent_plays_per_game'),
                'opponent_first_downs_per_game': scraper_stats.get('opponent_first_downs_per_game'),
                # FPI (None for now)
                'fpi_rating': None,
                'fpi_offensive_rating': None,
                'fpi_defensive_rating': None,
                'fpi_special_teams_rating': None,
                # Rankings (all are in scraper output)
                'points_per_game_rank': scraper_stats.get('points_per_game_rank'),
                'yards_per_play_rank': scraper_stats.get('yards_per_play_rank'),
                'red_zone_scoring_pct_rank': scraper_stats.get('red_zone_scoring_pct_rank'),
                'completion_pct_rank': scraper_stats.get('completion_pct_rank'),
                'fourth_down_conversion_pct_rank': scraper_stats.get('fourth_down_conversion_pct_rank'),
                'interceptions_thrown_per_game_rank': scraper_stats.get('interceptions_thrown_per_game_rank'),
                'fumbles_lost_per_game_rank': scraper_stats.get('fumbles_lost_per_game_rank'),
                'offensive_touchdowns_per_game_rank': scraper_stats.get('offensive_touchdowns_per_game_rank'),
                'passing_touchdowns_per_game_rank': scraper_stats.get('passing_touchdowns_per_game_rank'),
                'rushing_touchdowns_per_game_rank': scraper_stats.get('rushing_touchdowns_per_game_rank'),
                'total_touchdowns_per_game_rank': scraper_stats.get('touchdowns_per_game_rank'),
                'pass_attempts_per_game_rank': scraper_stats.get('pass_attempts_per_game_rank'),
                'rush_attempts_per_game_rank': scraper_stats.get('rushing_attempts_per_game_rank'),
                'plays_per_game_rank': scraper_stats.get('plays_per_game_rank'),
                'penalty_yards_per_game_rank': scraper_stats.get('penalty_yards_per_game_rank'),
                'qb_sacked_per_game_rank': scraper_stats.get('qb_sacked_per_game_rank'),
                'opponent_points_per_game_rank': scraper_stats.get('opponent_points_per_game_rank'),
                'opponent_yards_per_play_rank': scraper_stats.get('opponent_yards_per_play_rank'),
                'opponent_red_zone_scoring_pct_rank': scraper_stats.get('opponent_red_zone_scoring_pct_rank'),
                'opponent_completion_pct_rank': scraper_stats.get('opponent_completion_pct_rank'),
                'opponent_fourth_down_conversion_pct_rank': scraper_stats.get('opponent_fourth_down_conversion_pct_rank'),
                'sacks_per_game_rank': scraper_stats.get('sacks_per_game_rank'),
                'interceptions_per_game_rank': scraper_stats.get('interceptions_per_game_rank'),
                'defensive_touchdowns_per_game_rank': scraper_stats.get('defensive_touchdowns_per_game_rank'),
                'opponent_passing_touchdowns_per_game_rank': scraper_stats.get('opponent_passing_touchdowns_per_game_rank'),
                'opponent_rushing_touchdowns_per_game_rank': scraper_stats.get('opponent_rushing_touchdowns_per_game_rank'),
                'opponent_first_downs_per_game_rank': scraper_stats.get('opponent_first_downs_per_game_rank'),
                # NEW ranking columns (matching scraper field names)
                'passing_yards_per_game_rank': scraper_stats.get('passing_yards_per_game_rank'),
                'rushing_yards_per_game_rank': scraper_stats.get('rushing_yards_per_game_rank'),
                'first_downs_rank': scraper_stats.get('first_downs_rank'),
                'third_down_pct_rank': scraper_stats.get('third_down_pct_rank'),
                'red_zone_pct_rank': scraper_stats.get('red_zone_pct_rank'),
                'turnover_differential_rank': scraper_stats.get('turnover_differential_rank'),
                'total_yards_per_game_rank': scraper_stats.get('total_yards_per_game_rank'),
                'sacks_rank': scraper_stats.get('sacks_rank'),
                'points_allowed_per_game_rank': scraper_stats.get('points_allowed_per_game_rank'),
                'yards_allowed_per_game_rank': scraper_stats.get('yards_allowed_per_game_rank'),
                'passing_yards_allowed_rank': scraper_stats.get('passing_yards_allowed_rank'),
                'rushing_yards_allowed_rank': scraper_stats.get('rushing_yards_allowed_rank'),
                'opponent_third_down_pct_rank': scraper_stats.get('opponent_third_down_pct_rank'),
                'opponent_red_zone_pct_rank': scraper_stats.get('opponent_red_zone_pct_rank'),
                'penalties_rank': scraper_stats.get('penalties_rank'),
                'touchdowns_per_game_rank': scraper_stats.get('touchdowns_per_game_rank'),
            }

            # Use the full insert method
            return self.insert_team_stats(db_stats)

        except Exception as e:
            logger.error(f"Error in simplified insert for {team_name}: {str(e)}")
            raise

    def insert_team_stats(self, stats: Dict) -> int:
        """
        Insert new team stats snapshot using dynamic SQL
        Builds INSERT based on what fields are actually provided
        """
        cursor = self.conn.cursor()

        try:
            # Build column list and values from provided stats
            columns = []
            values = []

            for key, value in stats.items():
                columns.append(key)
                values.append(value)

            # Build SQL dynamically
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['?' for _ in values])

            sql = f'INSERT INTO nfl_team_stats ({columns_str}) VALUES ({placeholders})'

            cursor.execute(sql, tuple(values))
            self.conn.commit()

            logger.info(f"Inserted stats for {stats.get('team_name')}")
            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Error inserting team stats: {str(e)}")
            self.conn.rollback()
            raise

    def get_latest_team_stats(self, team_name: str, season: int = 2024) -> Optional[Dict]:
        """Get most recent stats for a team"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_team_stats
            WHERE team_name = ? AND season = ?
            ORDER BY scraped_at DESC
            LIMIT 1
        ''', (team_name, season))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_latest_team_stats(self, season: int = 2024) -> List[Dict]:
        """Get most recent stats for all teams"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_team_stats t1
            WHERE season = ? AND scraped_at = (
                SELECT MAX(scraped_at) FROM nfl_team_stats t2
                WHERE t2.team_name = t1.team_name AND t2.season = ?
            )
            ORDER BY team_name
        ''', (season, season))

        return [dict(row) for row in cursor.fetchall()]

    def get_team_stats_history(self, team_name: str, season: int = 2024) -> List[Dict]:
        """Get all historical stats for a team (for trend analysis)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_team_stats
            WHERE team_name = ? AND season = ?
            ORDER BY scraped_at ASC
        ''', (team_name, season))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== GAME METHODS ====================

    def insert_or_update_game(self, game: Dict) -> str:
        """Insert new game or update existing"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO nfl_games (
                    game_id, season, week, home_team, away_team,
                    commence_time, status, home_score, away_score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                game.get('game_id'),
                game.get('season', 2024),
                game.get('week'),
                game.get('home_team'),
                game.get('away_team'),
                game.get('commence_time'),
                game.get('status', 'scheduled'),
                game.get('home_score'),
                game.get('away_score')
            ))

            self.conn.commit()
            logger.info(f"Inserted/updated game: {game.get('game_id')}")
            return game.get('game_id')

        except Exception as e:
            logger.error(f"Error inserting game: {str(e)}")
            self.conn.rollback()
            raise

    def get_upcoming_games(self, limit: int = 50) -> List[Dict]:
        """Get upcoming games"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_games
            WHERE commence_time > CURRENT_TIMESTAMP
            ORDER BY commence_time ASC
            LIMIT ?
        ''', (limit,))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== ODDS METHODS ====================

    def insert_odds(self, odds: Dict) -> int:
        """Insert odds snapshot"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO nfl_betting_odds (
                    game_id, bookmaker, market_type,
                    home_price, away_price,
                    home_spread, home_spread_price, away_spread, away_spread_price,
                    over_under_point, over_price, under_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                odds.get('game_id'),
                odds.get('bookmaker'),
                odds.get('market_type'),
                odds.get('home_price'),
                odds.get('away_price'),
                odds.get('home_spread'),
                odds.get('home_spread_price'),
                odds.get('away_spread'),
                odds.get('away_spread_price'),
                odds.get('over_under_point'),
                odds.get('over_price'),
                odds.get('under_price')
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Error inserting odds: {str(e)}")
            self.conn.rollback()
            raise

    def get_latest_odds(self, game_id: str) -> List[Dict]:
        """Get most recent odds for a game across all bookmakers"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_betting_odds
            WHERE game_id = ? AND fetched_at = (
                SELECT MAX(fetched_at) FROM nfl_betting_odds
                WHERE game_id = ?
            )
        ''', (game_id, game_id))

        return [dict(row) for row in cursor.fetchall()]

    def get_odds_history(self, game_id: str, bookmaker: str = None) -> List[Dict]:
        """Get historical odds for line movement analysis"""
        cursor = self.conn.cursor()

        if bookmaker:
            cursor.execute('''
                SELECT * FROM nfl_betting_odds
                WHERE game_id = ? AND bookmaker = ?
                ORDER BY fetched_at ASC
            ''', (game_id, bookmaker))
        else:
            cursor.execute('''
                SELECT * FROM nfl_betting_odds
                WHERE game_id = ?
                ORDER BY fetched_at ASC
            ''', (game_id,))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== TRENDS METHODS ====================

    def insert_betting_trends_from_calculator(self, team_name: str, season: int, calc_trends: Dict) -> int:
        """
        Insert betting trends from NFLBettingTrendsCalculator output
        Maps calculator output format to database fields
        """
        import json
        cursor = self.conn.cursor()

        try:
            # Extract data from calculator output
            ats_record = calc_trends.get('ats_record', {})
            ats_home = calc_trends.get('ats_home', {})
            ats_away = calc_trends.get('ats_away', {})
            ou_record = calc_trends.get('ou_record', {})
            ou_home = calc_trends.get('ou_home', {})
            ou_away = calc_trends.get('ou_away', {})

            # Format legacy record strings
            ats_record_str = f"{ats_record.get('wins', 0)}-{ats_record.get('losses', 0)}-{ats_record.get('pushes', 0)}"
            ou_record_str = f"{ou_record.get('overs', 0)}-{ou_record.get('unders', 0)}-{ou_record.get('pushes', 0)}"

            cursor.execute('''
                INSERT INTO nfl_betting_trends (
                    team_name, season,
                    -- ATS Granular
                    ats_wins, ats_losses, ats_pushes, ats_win_pct,
                    home_ats_wins, home_ats_losses, home_ats_pushes,
                    away_ats_wins, away_ats_losses, away_ats_pushes,
                    ats_last_5, ats_last_10,
                    -- O/U Granular
                    ou_overs, ou_unders, ou_pushes, ou_over_pct,
                    home_ou_overs, home_ou_unders, home_ou_pushes,
                    away_ou_overs, away_ou_unders, away_ou_pushes,
                    ou_last_5, ou_last_10,
                    -- Analytics
                    games_analyzed, last_updated,
                    -- Legacy fields (for compatibility)
                    ats_record, over_under_record
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team_name,
                season,
                # ATS Granular
                ats_record.get('wins', 0),
                ats_record.get('losses', 0),
                ats_record.get('pushes', 0),
                calc_trends.get('ats_win_pct', 0.0),
                ats_home.get('wins', 0),
                ats_home.get('losses', 0),
                ats_home.get('pushes', 0),
                ats_away.get('wins', 0),
                ats_away.get('losses', 0),
                ats_away.get('pushes', 0),
                json.dumps(calc_trends.get('ats_last_5', [])),
                json.dumps(calc_trends.get('ats_last_10', [])),
                # O/U Granular
                ou_record.get('overs', 0),
                ou_record.get('unders', 0),
                ou_record.get('pushes', 0),
                calc_trends.get('ou_win_pct', 0.0),
                ou_home.get('overs', 0),
                ou_home.get('unders', 0),
                ou_home.get('pushes', 0),
                ou_away.get('overs', 0),
                ou_away.get('unders', 0),
                ou_away.get('pushes', 0),
                json.dumps(calc_trends.get('ou_last_5', [])),
                json.dumps(calc_trends.get('ou_last_10', [])),
                # Analytics
                calc_trends.get('games_analyzed', 0),
                calc_trends.get('last_updated', ''),
                # Legacy
                ats_record_str,
                ou_record_str
            ))

            self.conn.commit()
            logger.info(f"Inserted betting trends for {team_name} ({calc_trends.get('games_analyzed', 0)} games)")
            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Error inserting calculator trends for {team_name}: {str(e)}")
            self.conn.rollback()
            raise

    def insert_betting_trends(self, trends: Dict) -> int:
        """Insert betting trends snapshot (legacy method)"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO nfl_betting_trends (
                    team_name, season,
                    win_pct, home_win_pct, away_win_pct, favorite_win_pct, underdog_win_pct,
                    win_streak, loss_streak,
                    ats_record, ats_pct, home_ats_pct, away_ats_pct,
                    favorite_ats_pct, underdog_ats_pct, ats_margin,
                    over_under_record, over_pct, home_over_pct, away_over_pct,
                    average_total, average_team_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trends.get('team_name'),
                trends.get('season', 2024),
                trends.get('win_pct'),
                trends.get('home_win_pct'),
                trends.get('away_win_pct'),
                trends.get('favorite_win_pct'),
                trends.get('underdog_win_pct'),
                trends.get('win_streak'),
                trends.get('loss_streak'),
                trends.get('ats_record'),
                trends.get('ats_pct'),
                trends.get('home_ats_pct'),
                trends.get('away_ats_pct'),
                trends.get('favorite_ats_pct'),
                trends.get('underdog_ats_pct'),
                trends.get('ats_margin'),
                trends.get('over_under_record'),
                trends.get('over_pct'),
                trends.get('home_over_pct'),
                trends.get('away_over_pct'),
                trends.get('average_total'),
                trends.get('average_team_total')
            ))

            self.conn.commit()
            logger.info(f"Inserted trends for {trends.get('team_name')}")
            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Error inserting trends: {str(e)}")
            self.conn.rollback()
            raise

    def get_team_trends(self, team_name: str, season: int = 2024) -> Optional[Dict]:
        """Get most recent trends for a team"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM nfl_betting_trends
            WHERE team_name = ? AND season = ?
            ORDER BY scraped_at DESC
            LIMIT 1
        ''', (team_name, season))

        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== UTILITY METHODS ====================

    def get_database_stats(self) -> Dict:
        """Get database statistics for monitoring"""
        cursor = self.conn.cursor()

        stats = {}

        # Count records in each table
        tables = ['nfl_team_stats', 'nfl_games', 'nfl_betting_odds', 'nfl_betting_trends', 'nfl_predictions']

        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = cursor.fetchone()[0]

        # Get latest scrape time
        cursor.execute('SELECT MAX(scraped_at) FROM nfl_team_stats')
        stats['latest_team_stats_scrape'] = cursor.fetchone()[0]

        cursor.execute('SELECT MAX(fetched_at) FROM nfl_betting_odds')
        stats['latest_odds_fetch'] = cursor.fetchone()[0]

        cursor.execute('SELECT MAX(scraped_at) FROM nfl_betting_trends')
        stats['latest_trends_scrape'] = cursor.fetchone()[0]

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("NFL Database connection closed")


if __name__ == '__main__':
    # Test database creation
    print("Testing NFL Database...")
    db = NFLDatabase()

    # Print database stats
    stats = db.get_database_stats()
    print("\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nDatabase initialized successfully!")
    print(f"Location: {db.db_path}")

    db.close()
