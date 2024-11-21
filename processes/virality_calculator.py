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
        Calculate all required metrics for trending detection.
        """
        try:
            # Sort DataFrame by video_id and date for accurate calculations
            df = df.sort_values(['video_id', 'performance_date'])
            
            # Calculate Daily Growth Rate (DGR)
            df['previous_daily_views'] = df.groupby('video_id')['daily_views'].shift(1)
            epsilon = 1e-6  # Small constant to avoid division by zero
            df['dgr'] = ((df['daily_views'] - df['previous_daily_views']) / 
                        (df['previous_daily_views'] + epsilon)) * 100
            
            # Calculate Engagement Rate (ER)
            df['total_engagements'] = df['likes'] + df['comments'] + df['shares']
            df['er'] = (df['total_engagements'] / (df['daily_views'] + epsilon)) * 100
            
            # Calculate Engagement Growth Rate (EGR)
            df['previous_engagements'] = df.groupby('video_id')['total_engagements'].shift(1)
            df['egr'] = ((df['total_engagements'] - df['previous_engagements']) / 
                        (df['previous_engagements'] + epsilon)) * 100
            
            # Calculate Momentum (e.g., 3-day moving average of DGR)
            df['momentum'] = df.groupby('video_id')['dgr'].rolling(window=3, min_periods=1).mean().reset_index(0, drop=True)
            
            # Fill NaN values with 0
            df = df.fillna(0)
            
            # Ensure all metrics are present
            required_metrics = ['dgr', 'er', 'egr', 'momentum']
            for metric in required_metrics:
                if metric not in df.columns:
                    raise ValueError(f"Required metric '{metric}' is missing after calculation")
            
            return df
            
        except Exception as e:
            logging.error(f"Error calculating metrics: {str(e)}")
            raise

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
        """
        try:
            # Verify all required columns exist
            required_columns = ['dgr', 'er', 'egr', 'momentum', 'trending_score']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Create backup before storing new metrics
            self.data_manager.backup_database()
            logging.info("Database backup created before storing new metrics")
            
            # Start a transaction
            self.data_manager.conn.execute('BEGIN TRANSACTION')
            
            try:
                # Group by video_id to get latest metrics for videos table
                latest_metrics = df.sort_values('performance_date').groupby('video_id').last()
                
                # Update metrics for each video in the video table
                for video_id, row in latest_metrics.iterrows():
                    video_metrics = {
                        'dgr': float(row['dgr']),
                        'egr': float(row['egr']),
                        'trending_score': float(row['trending_score']),
                        'momentum': float(row['momentum'])
                    }
                    self.data_manager.update_video_table_virality_metrics(video_id, video_metrics)
                
                # Update daily_performance table
                for _, row in df.iterrows():
                    daily_metrics = {
                        'dgr': float(row['dgr']),
                        'er': float(row['er']),
                        'egr': float(row['egr']),
                        'trending_score': float(row['trending_score']),
                        'momentum': float(row['momentum'])
                    }
                    self.data_manager.update_daily_table_virality_metrics(
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
                logging.error(f"Error during metric storage transaction: {str(e)}")
                raise
                
        except Exception as e:
            logging.error(f"Error in store_calculated_metrics: {str(e)}")
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