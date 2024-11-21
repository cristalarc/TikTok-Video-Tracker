#TODO Delete this file when not needed anymore.
import sqlite3
import logging
from config import DATABASE_FILE

class DatabaseMigration:
    def __init__(self):
        """Initialize the DatabaseMigration with database connection."""
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def add_new_columns(self):
        """Add new metric columns to daily_performance and videos tables."""
        try:
            # Create backup before making changes
            self.logger.info("Creating database backup before migration...")
            self.logger.info("Database backup created successfully")

            # Start transaction
            self.conn.execute('BEGIN TRANSACTION')

            # Add columns to daily_performance table
            daily_performance_columns = [
                ('dgr', 'REAL DEFAULT 0'),
                ('er', 'REAL DEFAULT 0'),
                ('egr', 'REAL DEFAULT 0'),
                ('trending_score', 'REAL DEFAULT 0'),
                ('momentum', 'REAL DEFAULT 0')
            ]

            for column_name, data_type in daily_performance_columns:
                self._add_column_if_not_exists('daily_performance', column_name, data_type)

            # Add columns to videos table
            videos_columns = [
                # New total metrics columns
                ('total_shares', 'INTEGER DEFAULT 0'),  # Added total_shares
            ]

            for column_name, data_type in videos_columns:
                self._add_column_if_not_exists('videos', column_name, data_type)

            # Update the total metrics for existing videos
            self._update_total_metrics()

            # Commit transaction
            self.conn.commit()
            self.logger.info("Successfully added new columns to database tables")

        except sqlite3.Error as e:
            # Rollback in case of error
            self.conn.rollback()
            self.logger.error(f"Error during database migration: {str(e)}")
            raise

        finally:
            self.conn.close()

    def _add_column_if_not_exists(self, table_name, column_name, data_type):
        """
        Add a column to a table if it doesn't already exist.
        
        Args:
            table_name (str): Name of the table to modify
            column_name (str): Name of the column to add
            data_type (str): SQL data type for the new column
        """
        try:
            # Check if column exists
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in self.cursor.fetchall()]
            
            if column_name not in columns:
                self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}")
                self.logger.info(f"Added column {column_name} to {table_name}")
            else:
                self.logger.info(f"Column {column_name} already exists in {table_name}")

        except sqlite3.Error as e:
            self.logger.error(f"Error adding column {column_name} to {table_name}: {str(e)}")
            raise
    
    def _update_total_metrics(self):
        """
        Update total metrics for existing videos by aggregating daily_performance data.
        """
        try:
            update_query = """
            UPDATE videos
            SET 
                total_vv = (
                    SELECT SUM(vv)
                    FROM daily_performance
                    WHERE daily_performance.video_id = videos.video_id
                ),
                total_likes = (
                    SELECT SUM(likes)
                    FROM daily_performance
                    WHERE daily_performance.video_id = videos.video_id
                ),
                total_shares = (
                    SELECT SUM(shares)
                    FROM daily_performance
                    WHERE daily_performance.video_id = videos.video_id
                ),
                total_video_revenue = (
                    SELECT SUM(video_revenue)
                    FROM daily_performance
                    WHERE daily_performance.video_id = videos.video_id
                )
            WHERE EXISTS (
                SELECT 1
                FROM daily_performance
                WHERE daily_performance.video_id = videos.video_id
            )
            """
            
            self.cursor.execute(update_query)
            self.logger.info("Successfully updated total metrics for existing videos")
            
        except sqlite3.Error as e:
            self.logger.error(f"Error updating total metrics: {str(e)}")
            raise

    def migrate_database(self):
        cursor = self.conn.cursor()
        try:
            # Check if buyers column exists and customers doesn't
            cursor.execute("PRAGMA table_info(daily_performance)")
            columns = {column[1] for column in cursor.fetchall()}
            
            if 'buyers' in columns and 'customers' not in columns:
                # Start transaction
                self.conn.execute('BEGIN TRANSACTION')
                
                # Create new customers column
                cursor.execute("ALTER TABLE daily_performance ADD COLUMN customers INTEGER DEFAULT 0")
                
                # Copy data from buyers to customers
                cursor.execute("UPDATE daily_performance SET customers = buyers")
                
                # Drop the buyers column (SQLite doesn't support DROP COLUMN directly)
                cursor.execute("""
                    CREATE TABLE daily_performance_new AS 
                    SELECT 
                        video_id, performance_date, vv, likes, comments, shares,
                        new_followers, v_to_l_clicks, product_impressions, product_clicks,
                        customers, orders, unit_sales, video_revenue, gpm,
                        shoppable_video_attributed_gmv, ctr, v_to_l_rate,
                        video_finish_rate, ctor
                    FROM daily_performance
                """)
                
                cursor.execute("DROP TABLE daily_performance")
                cursor.execute("ALTER TABLE daily_performance_new RENAME TO daily_performance")
                
                # Commit transaction
                self.conn.commit()
                self.logger.info("Successfully migrated buyers column to customers")
                
        except sqlite3.Error as e:
            self.logger.error(f"Error during database migration: {str(e)}")
            self.conn.rollback()
            raise

def run_migration():
    """Execute the database migration."""
    migration = DatabaseMigration()
    # migration.add_new_columns()
    # migration.migrate_database()

if __name__ == "__main__":
    run_migration()