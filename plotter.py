#plotter.py is the file that handles the plotting of the data.
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import logging
import mplcursors
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import numpy as np
from pandas import DataFrame
import pandas as pd

# logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Supress unnecesary logging from matplotlib and PIL
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

class Plotter:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.canvas = None
        self.toolbar = None

    def clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        plt.close('all')
        self.fig = None
        self.ax = None

    def plot_metric(self, data, metric, timeframe='Daily'):
        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()

        try:
            # Extract dates and values
            dates, values = zip(*data)

            # Ensure dates are datetime objects
            if isinstance(dates[0], str):
                # If dates are strings, parse them
                dates = [pd.to_datetime(date) for date in dates]
            else:
                # If dates are already Timestamps, just convert to list
                dates = list(dates)

            # Convert values to floats and handle '--' as np.nan
            values = [v if v is not None else np.nan for v in values]

            # Create a DataFrame to handle NaN values
            df = DataFrame({'Date': dates, 'Value': values}).dropna()
            dates = df['Date']
            values = df['Value']

            # Check if there's data to plot after dropping NaNs
            if df.empty:
                messagebox.showwarning("Warning", "No valid data to plot.")
                return

            # Plot the data points
            scatter = self.ax.scatter(dates, values, marker='o', color='blue')

            # Plot a line if there's more than one data point
            if len(dates) > 1:
                self.ax.plot(dates, values, color='blue')
                # Set X-axis ticks to the data dates
                self.ax.set_xticks(dates)
            else:
                # Set X-axis limits narrowly around the single date
                single_date = dates.iloc[0]
                self.ax.set_xlim(single_date - timedelta(days=1), single_date + timedelta(days=1))
                # Set X-axis ticks to the single date
                self.ax.set_xticks([single_date])

            # Set labels and title
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel(metric)
            self.ax.set_title(f'{metric} Over Time')

            # Adjust X-axis formatter based on timeframe
            if timeframe == 'Daily':
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            elif timeframe == 'Weekly':
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('Week of %Y-%m-%d'))
            elif timeframe == 'Monthly':
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            # Rotate date labels for better visibility
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')

            # Format Y-axis for percentage metrics
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                # Since values are between 0 and 100, format without multiplying
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2f}%'.format(y)))
            else:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2f}'))

            # Set Y-axis limits with some padding
            y_min = 0
            y_max = max(values) * 1.1
            self.ax.set_ylim(y_min, y_max)

            # Tight layout to prevent clipping
            self.fig.tight_layout()

            # Add interactive cursor
            cursor = mplcursors.cursor(scatter, hover=True)

            # Function to format annotations
            def format_annotation(sel):
                index = sel.index
                date = dates.iloc[index].strftime('%Y-%m-%d')
                value = values.iloc[index]
                if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    value_str = f'{value:.2f}%' if not np.isnan(value) else '--'
                else:
                    value_str = f'{value:.2f}' if not np.isnan(value) else '--'
                return f'Date: {date}\n{metric}: {value_str}'

            cursor.connect("add", lambda sel: sel.annotation.set_text(format_annotation(sel)))

        except Exception as e:
            logging.error(f"Error in plot_metric: {str(e)}")
            raise

    def embed_plot(self, parent):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def plot_dual_metric(self, data1, metric1, data2, metric2, timeframe='Daily'):
        # Initialize figure and axis
        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()
        
        try:
            # Function to process data
            def process_data(data):
                dates, values = zip(*data)
                # Ensure dates are datetime objects
                if isinstance(dates[0], str):
                    dates = [pd.to_datetime(date) for date in dates]
                else:
                    dates = list(dates)  # Convert to list if already Timestamps
                # Handle None or NaN values in values
                values = [v if v is not None else np.nan for v in values]
                return dates, values

            # Process data for both metrics
            dates1, values1 = process_data(data1)
            dates2, values2 = process_data(data2)

            # Create DataFrames and join on dates
            df1 = DataFrame({'Date': dates1, metric1: values1}).set_index('Date')
            df2 = DataFrame({'Date': dates2, metric2: values2}).set_index('Date')
            df = df1.join(df2, how='outer').sort_index()

            # Drop rows where both metrics are NaN
            df.dropna(how='all', inplace=True)

            # Check if there's data to plot after dropping NaNs
            if df.empty:
                messagebox.showwarning("Warning", "No valid data to plot.")
                return

            # Plot metric1
            self.ax.plot(df.index, df[metric1], color='blue', marker='o', label=metric1)
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel(metric1, color='blue')
            self.ax.tick_params(axis='y', labelcolor='blue')

            # Format y-axis for metric1
            if metric1 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2f}%'.format(y)))
            else:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2f}'))

            # Create a second y-axis for metric2
            ax2 = self.ax.twinx()
            ax2.plot(df.index, df[metric2], color='red', marker='s', label=metric2)
            ax2.set_ylabel(metric2, color='red')
            ax2.tick_params(axis='y', labelcolor='red')

            # Format y-axis for metric2
            if metric2 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2f}%'.format(y)))
            else:
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2f}'))

            # Set x-axis ticks to the dates in your data
            self.ax.set_xticks(df.index)

            # Format x-axis labels based on timeframe
            if timeframe == 'Daily':
                date_format = '%Y-%m-%d'
            elif timeframe == 'Weekly':
                date_format = 'Week of %Y-%m-%d'
            elif timeframe == 'Monthly':
                date_format = '%Y-%m'
            else:
                date_format = '%Y-%m-%d'  # Default format

            self.ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

            # Rotate date labels for better visibility
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')

            # Adjust layout to prevent overlap
            self.fig.tight_layout()

            # Add legends
            self.fig.legend(loc='upper left')

            # Add interactive cursor
            scatter1 = self.ax.scatter(df.index, df[metric1], color='blue', marker='o', label=metric1)
            scatter2 = ax2.scatter(df.index, df[metric2], color='red', marker='s', label=metric2)
            cursor = mplcursors.cursor([scatter1, scatter2], hover=True)

            # Function to format annotations
            def format_annotation(sel):
                index = sel.target.index
                date = df.index[index].strftime('%Y-%m-%d')
                metric_name = sel.artist.get_label()
                value = df.iloc[index][metric_name]

                # Format values
                if metric_name in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    value_str = f'{value:.2f}%' if not np.isnan(value) else '--'
                else:
                    value_str = f'{value:.2f}' if not np.isnan(value) else '--'

                return f'Date: {date}\n{metric_name}: {value_str}'

            cursor.connect("add", lambda sel: sel.annotation.set_text(format_annotation(sel)))

        except Exception as e:
            logging.error(f"Error in plot_dual_metric: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while plotting dual metrics: {str(e)}")