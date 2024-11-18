#data_manager.py is the file that handles the data ingestion, processing, and storage.
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import shutil
import json
import re
import numpy as np
import tkinter as tk
from tkinter import messagebox
from config import DATABASE_FILE, SETTINGS_FILE, DB_BACKUP_DIR


# logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.create_tables()
        self.migrate_database()
        self.load_settings() # Load all settings

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.vv_threshold = settings.get('vv_threshold', 4000)
                self.week_start = settings.get('week_start', 'Sunday')
        except FileNotFoundError:
            # If the file doesn't exist, return default settings
            self.vv_threshold = 4000
            self.week_start = 'Sunday'

    def save_settings(self):
        settings = {
            'vv_threshold': self.vv_threshold,
            'week_start': self.week_start
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)

    def set_vv_threshold(self, threshold):
        self.vv_threshold = threshold
        self.save_settings()

    def set_week_start(self, week_start):
        if week_start not in ['Sunday', 'Monday']:
            raise ValueError("Week start day must be 'Sunday' or 'Monday'")
        self.week_start = week_start
        self.save_settings()

    def backup_database(self):
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"tiktok_tracker_backup_{timestamp}.db"
        backup_path = os.path.join(DB_BACKUP_DIR, backup_filename)

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
        match = re.search(r'\[Date Range\]: (\d{4}-\d{2}-\d{2}) ~ (\d{4}-\d{2}-\d{2})', date_range)
        if match:
            start_date, end_date = match.groups()
            if start_date != end_date:
                raise ValueError("Data spans more than one day. Please provide data for a single day only.")
            return start_date
        else:
            raise ValueError("Could not extract date from range string")

    def filter_videos(self, df):
        # Ensure 'Video ID's in df are strings and stripped of whitespace
        df['Video ID'] = df['Video ID'].astype(str).str.strip()

        # Get all existing video IDs from the database as strings and strip whitespace
        existing_video_ids = [str(vid).strip() for vid in self.get_existing_video_ids()]

        # Filter videos based on VV threshold or if they already exist in the database
        filtered_df = df[
            (df['VV'] >= self.vv_threshold) | (df['Video ID'].isin(existing_video_ids))
        ]

        # Log the filtered video IDs
        logging.info(f"Filtered Video IDs: {filtered_df['Video ID'].tolist()}")

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
            # Clean the percentage fields
            df = self.clean_percentage_fields(df)

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

    def get_time_series_data(self, video_id, metric, timeframe='Daily', week_start='Sunday'):
        cursor = self.conn.cursor()
        try:
            # Check if the metric is one that requires custom aggregation
            if metric == 'ctr':
                return self.aggregate_ctr(video_id, timeframe, week_start)
            elif metric == 'ctor':
                return self.aggregate_ctor(video_id, timeframe, week_start)
            elif metric in ['v_to_l_rate', 'video_finish_rate']:
                return self.aggregate_simple_average(video_id, metric, timeframe, week_start)
            
            # For non-percentage metrics, proceed with standard aggregation
            df = self.get_aggregation_data(video_id, [metric], timeframe, week_start)
            
            # Group by period and sum the metric
            result = df.groupby('period')[metric].sum().reset_index()
            return list(result.itertuples(index=False, name=None))
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
            self.conn = sqlite3.connect(DATABASE_FILE)

    def restore_database(self, backup_path):
        try:
            # Close the current connection
            self.conn.close()
            
            # Replace the current database with the backup
            shutil.copy2(backup_path, DATABASE_FILE)
            
            # Reopen the connection
            self.conn = sqlite3.connect(DATABASE_FILE)
            
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
        
    def clean_percentage_fields(self, df):
        """
        Converts percentage strings to floats in the DataFrame.
        """
        percentage_fields = ['CTR', 'CTOR', 'V-to-L rate', 'Video Finish Rate']
        for field in percentage_fields:
            df[field] = df[field].replace('--', np.nan)
            df[field] = df[field].str.rstrip('%').astype('float')
        return df

    def aggregate_ctr(self, video_id, timeframe, week_start):
        """
        Calculates CTR as (Sum of Product Clicks) / (Sum of VV) * 100 over the specified timeframe.
        """
        data = self.get_aggregation_data(video_id, ['product_clicks', 'vv'], timeframe, week_start)
        result = []
        for period, group in data.groupby('period'):
            total_clicks = group['product_clicks'].sum()
            total_vv = group['vv'].sum()
            # Calculate CTR and multiply by 100 to get percentage
            ctr = (total_clicks / total_vv) * 100 if total_vv else np.nan
            result.append((period, ctr))
        return result

    def aggregate_ctor(self, video_id, timeframe, week_start):
        """
        Calculates CTOR as (Sum of Orders) / (Sum of Product Clicks) over the specified timeframe.
        """
        data = self.get_aggregation_data(video_id, ['orders', 'product_clicks'], timeframe, week_start)
        result = []
        for period, group in data.groupby('period'):
            total_orders = group['orders'].sum()
            total_clicks = group['product_clicks'].sum()
            # Calculate CTR and multiply by 100 to get percentage
            ctor = (total_orders / total_clicks) * 100 if total_clicks else np.nan
            result.append((period, ctor))
        return result

    def aggregate_simple_average(self, video_id, metric, timeframe, week_start):
        """
        Calculates the simple average of the given metric over the specified timeframe.
        """
        data = self.get_aggregation_data(video_id, [metric], timeframe, week_start)
        result = []
        for period, group in data.groupby('period'):
            # Convert values to decimals for calculation
            values_in_decimal = group[metric] / 100.0
            # Calculate the mean on decimal values
            avg_metric_decimal = values_in_decimal.mean()
            # Convert the mean back to percentage
            avg_metric = avg_metric_decimal * 100
            result.append((period, avg_metric))
            logging.info(f"Aggregated {metric} for {period}: {avg_metric}")
        return result

    def get_aggregation_data(self, video_id, columns, timeframe, week_start):
        """
        Retrieves data and prepares it for aggregation.
        """
        logging.info(f"Week start: {week_start}")
        cursor = self.conn.cursor()
        columns_str = ', '.join(columns)
        cursor.execute(f'''
            SELECT performance_date, {columns_str}
            FROM daily_performance
            WHERE video_id = ?
            ORDER BY performance_date
        ''', (video_id,))
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['performance_date'] + columns)
        df['performance_date'] = pd.to_datetime(df['performance_date'])

        if timeframe == 'Weekly':
            # Map week_start to numerical day of week (Monday=0, Sunday=6)
            day_map = {'Monday': 0, 'Sunday': 6}

            week_start_num = day_map.get(week_start, 0)  # Defaults to Monday if invalid

            # Compute the start of the week
            df['period'] = df['performance_date'] - pd.to_timedelta(
                (df['performance_date'].dt.dayofweek - week_start_num) % 7,
                unit='d'
            )
            df['period'] = df['period'].dt.normalize()  # Ensure time component is set to midnight
            
        elif timeframe == 'Monthly':
            df['period'] = df['performance_date'].values.astype('datetime64[M]')
            
        else:
            df['period'] = df['performance_date']

        return df
    
    def clear_video_performance(self, master):
        """
        Clear video performance data for a specified date after user confirmation.
        Ensures data integrity by creating a backup before deletion.
        """
        # Create a simple dialog to get the date, specifying the parent window
        date = tk.simpledialog.askstring("Clear Video Performance", "Enter date to clear (YYYY-MM-DD):", parent=master)
        if not date:
            return
        try:
            # Validate date format
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.", parent=master)
            return

        try:
            result = self.clear_data_for_date(date)
            if result:
                messagebox.showinfo("Success", f"Data for {date} has been cleared. A backup was created before clearing.", parent=master)
            else:
                messagebox.showinfo("Info", f"No data found for {date}.", parent=master)
        except Exception as e:
            error_message = f"An error occurred while clearing data: {str(e)}\n\nPlease check the log for more details."
            messagebox.showerror("Error", error_message, parent=master)
            logging.error(f"Error in clear_video_performance: {str(e)}", exc_info=True)
    
    def get_videos_by_date(self, date):
        """
        Retrieve video performance data for a specific date.
        
        Args:
            date (datetime): The date to fetch data for
        
        Returns:
            list: List of tuples containing video performance data
        """
        query = """
            SELECT 
                video_id,
                vv as views,
                shares,
                comments,
                video_revenue as gmv,
                ctr,
                ctor,
                video_finish_rate as finish_rate
            FROM daily_performance
            WHERE date(performance_date) = date(?)
            ORDER BY views DESC
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (date.strftime('%Y-%m-%d'),))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []
        
    # Virality metrics
    def update_daily_metrics(self, video_id, performance_date, metrics):
        """
        Update daily performance metrics for a video.

        Args:
            video_id (str): The video ID
            performance_date (str): The date of performance
            metrics (dict): Dictionary containing the metrics to update
        """
        try:
            cursor = self.conn.cursor()
            
            # Construct the UPDATE query dynamically based on provided metrics
            set_clause = ", ".join([f"{key} = ?" for key in metrics.keys()])
            values = list(metrics.values())
            values.extend([video_id, performance_date])  # Add WHERE clause parameters
            
            query = f"""
                UPDATE daily_performance 
                SET {set_clause}
                WHERE video_id = ? AND performance_date = ?
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Error updating daily metrics: {str(e)}")
            raise

    def update_video_metrics(self, video_id, metrics):
        """
        Update video metrics in the videos table.

        Args:
            video_id (str): The video ID
            metrics (dict): Dictionary containing the metrics to update
        """
        try:
            cursor = self.conn.cursor()
            
            # Construct the UPDATE query dynamically based on provided metrics
            set_clause = ", ".join([f"{key} = ?" for key in metrics.keys()])
            values = list(metrics.values())
            values.append(video_id)  # Add WHERE clause parameter
            
            query = f"""
                UPDATE videos 
                SET {set_clause}
                WHERE video_id = ?
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Error updating video metrics: {str(e)}")
            raise