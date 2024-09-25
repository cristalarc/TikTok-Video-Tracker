import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import shutil
import json
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    def __init__(self, db_path='tiktok_tracker.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self.migrate_database()
        self.vv_threshold = self.load_vv_threshold()  # Load threshold from file

    def set_vv_threshold(self, threshold):
        self.vv_threshold = threshold
        self.save_vv_threshold()  # Save threshold to file

    def save_vv_threshold(self):
        with open('settings.json', 'w') as f:
            json.dump({'vv_threshold': self.vv_threshold}, f)

    def load_vv_threshold(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get('vv_threshold', 4000)
        except FileNotFoundError:
            return 4000

    def backup_database(self):
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_backup')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"tiktok_tracker_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Create a new connection to the backup database
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                self.conn.backup(backup_conn)
            backup_conn.close()
            logging.info(f"Database backed up to {backup_path}")
        except Exception as e:
            logging.error(f"Error backing up database: {str(e)}")
            raise

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                video_info TEXT,
                time TEXT,
                creator_name TEXT,
                products TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_performance (
                video_id TEXT,
                performance_date TEXT,
                vv INTEGER,
                likes INTEGER,
                comments INTEGER,
                shares INTEGER,
                new_followers INTEGER,
                v_to_l_clicks INTEGER,
                product_impressions INTEGER,
                product_clicks INTEGER,
                buyers INTEGER,
                orders INTEGER,
                unit_sales INTEGER,
                video_revenue REAL,
                gpm REAL,
                shoppable_video_attributed_gmv REAL,
                ctr REAL,
                v_to_l_rate REAL,
                video_finish_rate REAL,
                ctor REAL,
                PRIMARY KEY (video_id, performance_date),
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        ''')
        self.conn.commit()

    def migrate_database(self):
        cursor = self.conn.cursor()
        try:
            # Check if video_info column exists
            cursor.execute("PRAGMA table_info(videos)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'video_info' not in columns:
                # Add video_info column
                cursor.execute("ALTER TABLE videos ADD COLUMN video_info TEXT")
                logging.info("Added video_info column to videos table")
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error migrating database: {str(e)}")
            self.conn.rollback()

    def read_video_performance_excel(self, file_path):
        try:
            # Read the date range from cell A1
            date_range = pd.read_excel(file_path, header=None, nrows=1).iloc[0, 0]
            performance_date = self.extract_date_from_range(date_range)

            # Read the actual data starting from row 3
            df = pd.read_excel(file_path, header=2)
            df['performance_date'] = performance_date
            logging.info(f"Successfully read Excel file: {file_path}")
            logging.debug(f"Columns in the Excel file: {df.columns.tolist()}")
            return df
        except ValueError as ve:
            logging.error(f"Error processing Excel file: {str(ve)}")
            raise
        except Exception as e:
            logging.error(f"Error reading Excel file: {str(e)}")
            raise

    def extract_date_from_range(self, date_range):
        import re
        match = re.search(r'\[Date Range\]: (\d{4}-\d{2}-\d{2}) ~ (\d{4}-\d{2}-\d{2})', date_range)
        if match:
            start_date, end_date = match.groups()
            if start_date != end_date:
                raise ValueError("Data spans more than one day. Please provide data for a single day only.")
            return start_date
        else:
            raise ValueError("Could not extract date from range string")

    def filter_videos(self, df):
        logging.debug(f"Data Types:\n{df.dtypes}") # Remove this later
        logging.debug(f"Specific Video ID in DataFrame: {df[df['Video ID'] == '7309583706706971946']}") # Remove this later
        # Ensure 'Video ID's in df are strings and stripped of whitespace

        df['Video ID'] = df['Video ID'].astype(str).str.strip()

        # Get all existing video IDs from the database as strings and strip whitespace
        existing_video_ids = [str(vid).strip() for vid in self.get_existing_video_ids()]

        # Filter videos based on VV threshold or if they already exist in the database
        filtered_df = df[
            (df['VV'] >= self.vv_threshold) | (df['Video ID'].isin(existing_video_ids))
        ]

        # Log the filtered video IDs
        logging.debug(f"Filtered Video IDs: {filtered_df['Video ID'].tolist()}")

        return filtered_df

    def get_existing_video_ids(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT video_id FROM videos")
            video_ids = [str(row[0]).strip() for row in cursor.fetchall()]
            return video_ids
        except Exception as e:
            logging.error(f"Error getting existing video IDs: {str(e)}")
            return []

    def insert_or_update_records(self, df):
        cursor = self.conn.cursor()
        try:
            for _, row in df.iterrows():
                # Check if the video already exists
                cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (row['Video ID'],))
                video_exists = cursor.fetchone() is not None

                if video_exists:
                    # Update existing video
                    cursor.execute('''
                        UPDATE videos 
                        SET video_info = ?, time = ?, creator_name = ?, products = ?
                        WHERE video_id = ?
                    ''', (row['Video Info'], row['Time'], row['Creator name'], row['Products'], row['Video ID']))
                else:
                    # Insert new video only if VV >= 4000
                    if row['VV'] >= self.vv_threshold:
                        cursor.execute('''
                            INSERT INTO videos (video_id, video_info, time, creator_name, products)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (row['Video ID'], row['Video Info'], row['Time'], row['Creator name'], row['Products']))
                    else:
                        continue  # Skip this video if it's new and has less than 4000 VV

                # Always insert or update daily performance for existing videos
                if video_exists or row['VV'] >= self.vv_threshold:
                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_performance 
                        (video_id, performance_date, vv, likes, comments, shares, new_followers, 
                        v_to_l_clicks, product_impressions, product_clicks, buyers, orders, 
                        unit_sales, video_revenue, gpm, shoppable_video_attributed_gmv, ctr, 
                        v_to_l_rate, video_finish_rate, ctor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (row['Video ID'], row['performance_date'], row['VV'], row['Likes'], 
                          row['Comments'], row['Shares'], row['New followers'], row['V-to-L clicks'],
                          row['Product Impressions'], row['Product Clicks'], row['Buyers'], 
                          row['Orders'], row['Unit Sales'], row['Video Revenue ($)'], 
                          row['GPM ($)'], row['Shoppable video attributed GMV ($)'], 
                          row['CTR'], row['V-to-L rate'], row['Video Finish Rate'], row['CTOR']))

            self.conn.commit()
            logging.info(f"Successfully inserted or updated {len(df)} records")
            self.backup_database()
            logging.info("Data backed up successfully")
        except Exception as e:
            logging.error(f"Error inserting or updating records: {str(e)}")
            self.conn.rollback()
            raise

    def search_videos(self, query):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT v.video_id, v.video_info, v.time, v.creator_name, v.products, 
                    SUM(dp.vv) as total_vv, SUM(dp.shares) as total_shares, 
                    ROUND(SUM(dp.video_revenue), 2) as total_video_revenue
                FROM videos v
                LEFT JOIN daily_performance dp ON v.video_id = dp.video_id
                WHERE v.video_info LIKE ? OR v.video_id LIKE ? OR v.creator_name LIKE ? OR v.products LIKE ?
                GROUP BY v.video_id
                ORDER BY total_vv DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error searching videos: {str(e)}")
            raise

    def get_video_details(self, video_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT v.video_id, v.video_info, v.time, v.creator_name, v.products, 
                    SUM(dp.vv) as total_vv, SUM(dp.likes) as total_likes, 
                    SUM(dp.comments) as total_comments, SUM(dp.shares) as total_shares, 
                    SUM(dp.new_followers) as total_new_followers, 
                    SUM(dp.video_revenue) as total_video_revenue,
                    MAX(dp.performance_date) as latest_performance_date
                FROM videos v
                LEFT JOIN daily_performance dp ON v.video_id = dp.video_id
                WHERE v.video_id = ?
                GROUP BY v.video_id
            ''', (video_id,))
            return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting video details: {str(e)}")
            raise

    def get_time_series_data(self, video_id, metric):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f'''
                SELECT performance_date, {metric}
                FROM daily_performance
                WHERE video_id = ?
                ORDER BY performance_date
            ''', (video_id,))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting time series data: {str(e)}")
            raise

    def clear_data_for_date(self, date):
        self.ensure_connection()
        cursor = None
        try:
            cursor = self.conn.cursor()
            # Check if there's data for the given date
            cursor.execute("SELECT COUNT(*) FROM daily_performance WHERE performance_date = ?", (date,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                return False  # No data for this date
            
            # Perform backup before clearing data
            self.backup_database()
            
            # Clear data for the given date
            cursor.execute("DELETE FROM daily_performance WHERE performance_date = ?", (date,))
            self.conn.commit()
            logging.info(f"Cleared data for date: {date}")
            return True
        except sqlite3.Error as e:
            logging.error(f"SQLite error in clear_data_for_date: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise
        except Exception as e:
            logging.error(f"Unexpected error in clear_data_for_date: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.ensure_connection()

    def ensure_connection(self):
        try:
            # Try executing a simple query to check if the connection is open
            self.conn.execute('SELECT 1')
        except (AttributeError, sqlite3.ProgrammingError):
            # If self.conn is None or closed, create a new connection
            self.conn = sqlite3.connect('tiktok_tracker.db')

    def restore_database(self, backup_path):
        try:
            # Close the current connection
            self.conn.close()
            
            # Replace the current database with the backup
            shutil.copy2(backup_path, 'tiktok_tracker.db')
            
            # Reopen the connection
            self.conn = sqlite3.connect('tiktok_tracker.db')
            
            logging.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Error restoring database: {str(e)}")
            return False

    def check_existing_data(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_performance WHERE performance_date = ?", (date,))
        count = cursor.fetchone()[0]
        return count > 0

    def replace_data_for_date(self, df, date):
        cursor = self.conn.cursor()
        try:
            # Delete existing data for the given date
            cursor.execute("DELETE FROM daily_performance WHERE performance_date = ?", (date,))
            
            # Insert new data
            self.insert_or_update_records(df)
            
            self.conn.commit()
            logging.info(f"Successfully replaced data for {date}")
        except Exception as e:
            logging.error(f"Error replacing data for {date}: {str(e)}")
            self.conn.rollback()
            raise

    def get_all_videos(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT v.video_id, v.video_info, v.time, v.creator_name, v.products, 
                    SUM(dp.vv) as total_vv, SUM(dp.shares) as total_shares, 
                    ROUND(SUM(dp.video_revenue), 2) as total_video_revenue
                FROM videos v
                LEFT JOIN daily_performance dp ON v.video_id = dp.video_id
                GROUP BY v.video_id
                ORDER BY v.time DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting all videos: {str(e)}")
            raise
    
    def get_latest_performance_date(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT MAX(performance_date) FROM daily_performance")
            latest_date = cursor.fetchone()[0]
            return latest_date if latest_date else "N/A"
        except Exception as e:
            logging.error(f"Error getting latest performance date: {str(e)}")
            return "N/A"

