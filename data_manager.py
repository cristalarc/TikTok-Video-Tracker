import pandas as pd
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    def __init__(self, db_path='tiktok_tracker.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self.migrate_database()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                video_info TEXT,
                date TEXT,
                creator_name TEXT,
                products TEXT,
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
                ctor REAL
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

    def read_excel(self, file_path):
        try:
            df = pd.read_excel(file_path, parse_dates=['Time'])
            logging.info(f"Successfully read Excel file: {file_path}")
            logging.debug(f"Columns in the Excel file: {df.columns.tolist()}")
            return df
        except Exception as e:
            logging.error(f"Error reading Excel file: {str(e)}")
            raise

    def filter_videos(self, df):
        try:
            if 'VV' not in df.columns:
                logging.error("'VV' column not found in the DataFrame")
                raise ValueError("'VV' column not found in the DataFrame")
            filtered_df = df[df['VV'] > 4000]
            logging.info(f"Filtered {len(filtered_df)} videos with more than 4000 views")
            return filtered_df
        except Exception as e:
            logging.error(f"Error filtering videos: {str(e)}")
            raise

    def insert_or_update_records(self, df):
        cursor = self.conn.cursor()
        try:
            for _, row in df.iterrows():
                # Extract date from the timestamp
                full_date = row.get('Time')
                date = full_date.strftime("%Y/%m/%d") if pd.notnull(full_date) else None

                cursor.execute('''
                    INSERT OR REPLACE INTO videos
                    (video_id, video_info, date, creator_name, products, vv, likes, comments, shares, new_followers,
                    v_to_l_clicks, product_impressions, product_clicks, buyers, orders,
                    unit_sales, video_revenue, gpm, shoppable_video_attributed_gmv,
                    ctr, v_to_l_rate, video_finish_rate, ctor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('Video ID'), row.get('Video Info'), date, row.get('Creator name'), row.get('Products'),
                    row.get('VV'), row.get('Likes'), row.get('Comments'), row.get('Shares'), row.get('New followers'),
                    row.get('V-to-L clicks'), row.get('Product Impressions'), row.get('Product Clicks'),
                    row.get('Buyers'), row.get('Orders'), row.get('Unit Sales'), row.get('Video Revenue ($)'),
                    row.get('GPM ($)'), row.get('Shoppable video attributed GMV ($)'), row.get('CTR'),
                    row.get('V-to-L rate'), row.get('Video Finish Rate'), row.get('CTOR')
                ))
            self.conn.commit()
            logging.info(f"Successfully inserted or updated {len(df)} records")
        except Exception as e:
            logging.error(f"Error inserting or updating records: {str(e)}")
            self.conn.rollback()
            raise

    def search_videos(self, query):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT video_id, video_info, date, creator_name, products, vv
                FROM videos
                WHERE video_info LIKE ? OR video_id LIKE ? OR creator_name LIKE ? OR products LIKE ?
                ORDER BY vv DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error searching videos: {str(e)}")
            raise

    def get_video_details(self, video_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
            return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting video details: {str(e)}")
            raise

    def get_time_series_data(self, video_id, metric):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f'''
                SELECT date, {metric}
                FROM videos
                WHERE video_id = ?
                ORDER BY date
            ''', (video_id,))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting time series data: {str(e)}")
            raise

