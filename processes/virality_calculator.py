import pandas as pd
import numpy as np
import logging

# logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ViralityCalculator:
    def __init__(self, data_manager):
        """
        Initialize the ViralityCalculator with a reference to the DataManager.

        Args:
            data_manager (DataManager): Instance for data retrieval.
        """
        self.data_manager = data_manager

    def get_video_metrics(self, start_date=None, end_date=None):
        """
        Retrieve necessary metrics for all videos within the specified date range.

        Args:
            start_date (str): Optional start date in 'YYYY-MM-DD' format.
            end_date (str): Optional end date in 'YYYY-MM-DD' format.

        Returns:
            DataFrame: Contains video_id, performance_date, daily views, likes, comments, shares.
        """
        # SQL query to retrieve daily metrics
        query = '''
            SELECT 
                dp.video_id,
                dp.performance_date,
                dp.vv AS daily_views,
                dp.likes,
                dp.comments,
                dp.shares
            FROM daily_performance dp
        '''
        params = ()
        if start_date and end_date:
            query += ' WHERE dp.performance_date BETWEEN ? AND ?'
            params = (start_date, end_date)
        query += ' ORDER BY dp.video_id, dp.performance_date'

        # Fetch data using DataManager's connection
        cursor = self.data_manager.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Create DataFrame from fetched data
        df = pd.DataFrame(rows, columns=['video_id', 'performance_date', 'daily_views', 'likes', 'comments', 'shares'])
        df['performance_date'] = pd.to_datetime(df['performance_date'])

        return df

    def calculate_metrics(self, df):
        """
        Calculate required metrics such as Total Views, DGR, and ER.

        Args:
            df (DataFrame): DataFrame containing daily video metrics.

        Returns:
            DataFrame: DataFrame with additional calculated metrics.
        """
        # Sort values to ensure correct calculations
        df = df.sort_values(['video_id', 'performance_date'])

        # Calculate Total Views (TV) per video over time
        df['total_views'] = df.groupby('video_id')['daily_views'].cumsum()

        # Calculate previous day's views for DGR computation
        df['prev_daily_views'] = df.groupby('video_id')['daily_views'].shift(1).fillna(0)
        epsilon = 1e-6  # Small constant to prevent division by zero

        # Calculate Daily Growth Rate (DGR)
        df['dgr'] = ((df['daily_views'] - df['prev_daily_views']) / (df['prev_daily_views'] + epsilon)) * 100

        # Calculate Total Engagements per day
        df['daily_engagements'] = df['likes'] + df['comments'] + df['shares']
        df['total_engagements'] = df.groupby('video_id')['daily_engagements'].cumsum()

        # Calculate Engagement Rate (ER)
        df['er'] = (df['total_engagements'] / df['total_views']) * 100
        df['er'] = df['er'].replace([np.inf, -np.inf], 0).fillna(0)  # Handle infinite and NaN values

        return df

    def normalize_metrics(self, df):
        """
        Normalize metrics to a 0-1 scale for comparability.

        Args:
            df (DataFrame): DataFrame with calculated metrics.

        Returns:
            DataFrame: DataFrame with normalized metrics.
        """
        metrics_to_normalize = ['total_views', 'daily_views', 'dgr', 'er']
        for metric in metrics_to_normalize:
            min_value = df[metric].min()
            max_value = df[metric].max()
            df[f'norm_{metric}'] = (df[metric] - min_value) / (max_value - min_value + 1e-6)
        return df

    def calculate_trending_score(self, df, weights=None):
        """
        Calculate the composite Trending Score (TS) for each video.

        Args:
            df (DataFrame): DataFrame with normalized metrics.
            weights (dict): Weights for each metric in the TS calculation.

        Returns:
            DataFrame: DataFrame with the trending score.
        """
        # Default weights if none are provided
        if weights is None:
            weights = {
                'norm_total_views': 0.3,
                'norm_daily_views': 0.2,
                'norm_dgr': 0.3,
                'norm_er': 0.2
            }
        #TODO Slider for weights
        # Calculate Trending Score
        df['trending_score'] = (
            df['norm_total_views'] * weights['norm_total_views'] +
            df['norm_daily_views'] * weights['norm_daily_views'] +
            df['norm_dgr'] * weights['norm_dgr'] +
            df['norm_er'] * weights['norm_er']
        )
        return df
    
    def store_calculated_metrics(self, df):
        """
        Store calculated metrics in the database.

        Args:
            df (DataFrame): DataFrame containing calculated metrics
        """
        try:
            # Create backup before storing new metrics
            self.data_manager.backup_database()
            logging.info("Database backup created before storing new metrics")
            
            # Start a transaction
            self.data_manager.conn.execute('BEGIN TRANSACTION')
            
            try:
                # Group by video_id to get latest metrics for videos table
                latest_metrics = df.sort_values('performance_date').groupby('video_id').last()
                
                # Update metrics for each video
                for video_id, row in latest_metrics.iterrows():
                    video_metrics = {
                        'dgr': float(row['dgr']),
                        'egr': float(row['egr']),
                        'trending_score': float(row['trending_score']),
                        'momentum': float(row['momentum'])
                    }
                    self.data_manager.update_video_metrics(video_id, video_metrics)
                
                # Update daily_performance table
                for _, row in df.iterrows():
                    daily_metrics = {
                        'dgr': float(row['dgr']),
                        'er': float(row['er']),
                        'egr': float(row['egr']),
                        'trending_score': float(row['trending_score']),
                        'momentum': float(row['momentum'])
                    }
                    self.data_manager.update_daily_metrics(
                        row['video_id'],
                        row['performance_date'].strftime('%Y-%m-%d'),
                        daily_metrics
                    )
                
                # Commit the transaction
                self.data_manager.conn.commit()
                logging.info("Successfully stored calculated metrics in database")
                
            except Exception as e:
                # Rollback the transaction if there's an error
                self.data_manager.conn.rollback()
                raise e
                
        except Exception as e:
            logging.error(f"Error storing calculated metrics: {str(e)}")
            raise

    def identify_trending_videos(self, df, ts_threshold=0.7):
        """
        Identify videos exceeding the trending score threshold.

        Args:
            df (DataFrame): DataFrame with calculated trending scores.
            ts_threshold (float): Threshold above which a video is considered trending.

        Returns:
            DataFrame: DataFrame of videos that are trending.
        """
        # Filter videos based on the trending score threshold
        trending_videos = df[df['trending_score'] >= ts_threshold]
        return trending_videos

    def get_trending_videos(self, start_date=None, end_date=None, ts_threshold=0.7):
        """
        Full pipeline to retrieve and identify trending videos.

        Args:
            start_date (str): Optional start date for data retrieval.
            end_date (str): Optional end date for data retrieval.
            ts_threshold (float): Trending Score threshold.

        Returns:
            DataFrame: DataFrame of trending videos with relevant metrics.
        """
        df = self.get_video_metrics(start_date, end_date)
        df = self.calculate_metrics(df)
        df = self.normalize_metrics(df)
        df = self.calculate_trending_score(df)
        # Store the calculated metrics in the database
        self.store_calculated_metrics(df)
        trending_videos = self.identify_trending_videos(df, ts_threshold)
        # Keep latest entry per video
        trending_videos = trending_videos.sort_values('performance_date').groupby('video_id').tail(1)
        return trending_videos