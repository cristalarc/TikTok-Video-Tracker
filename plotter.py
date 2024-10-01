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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

    def plot_metric(self, data, metric):
        import numpy as np  # Ensure numpy is imported at the top

        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()

        try:
            # Extract dates and values
            dates, values = zip(*data)
            # Convert date strings to datetime objects
            dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]

            # Convert values to floats and handle '--' as np.nan
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                # Remove '%' if present and convert to float
                values = [
                    float(str(v).strip('%')) / 100 if v != '--' else np.nan
                    for v in values
                ]
            else:
                values = [float(v) if v != '--' else np.nan for v in values]

            # Create a DataFrame to handle NaN values
            from pandas import DataFrame
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

            # Format the X-axis labels
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            # Rotate date labels for better visibility
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')

            # Format Y-axis for percentage metrics
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y)))

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
                index = sel.target.index
                date = dates.iloc[index].strftime('%Y-%m-%d')
                value = values.iloc[index]
                if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    value_str = f'{value:.2%}' if not np.isnan(value) else '--'
                else:
                    value_str = f'{value}' if not np.isnan(value) else '--'
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

    def plot_dual_metric(self, data1, metric1, data2, metric2):
        from datetime import timedelta
        import numpy as np
        from pandas import DataFrame

        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()

        try:
            # Function to process data
            def process_data(data, metric):
                dates, values = zip(*data)
                dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
                if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    values = [float(str(v).strip('%')) / 100 if v != '--' else np.nan for v in values]
                else:
                    values = [float(v) if v != '--' else np.nan for v in values]
                return dates, values

            # Process data for both metrics
            dates1, values1 = process_data(data1, metric1)
            dates2, values2 = process_data(data2, metric2)

            # Create DataFrames and join
            df1 = DataFrame({'Date': dates1, metric1: values1}).set_index('Date')
            df2 = DataFrame({'Date': dates2, metric2: values2}).set_index('Date')
            df = df1.join(df2, how='outer').sort_index()

            # Plot metric1
            self.ax.plot(df.index, df[metric1], color='blue', marker='o', label=metric1)
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel(metric1, color='blue')
            self.ax.tick_params(axis='y', labelcolor='blue')

            # Format y-axis for metric1 if it's a percentage
            if metric1 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y)))

            # Create a second y-axis
            ax2 = self.ax.twinx()
            ax2.plot(df.index, df[metric2], color='red', marker='s', label=metric2)
            ax2.set_ylabel(metric2, color='red')
            ax2.tick_params(axis='y', labelcolor='red')

            # Format y-axis for metric2 if it's a percentage
            if metric2 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y)))

            # Set X-axis formatter
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')

            # Add legends
            self.fig.legend(loc='upper left')

            # Adjust layout to prevent overlap
            self.fig.tight_layout()

            # Add interactive cursor
            scatter1 = self.ax.scatter(df.index, df[metric1], color='blue', marker='o')
            scatter2 = ax2.scatter(df.index, df[metric2], color='red', marker='s')
            cursor = mplcursors.cursor([scatter1, scatter2], hover=True)

            @cursor.connect("add")
            def on_add(sel):
                index = sel.index
                date = df.index[index].strftime("%Y-%m-%d")
                value1 = df[metric1].iloc[index]
                value2 = df[metric2].iloc[index]
                
                if metric1 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    value1_str = f'{value1:.2%}' if not np.isnan(value1) else '--'
                else:
                    value1_str = f'{value1:.2f}' if not np.isnan(value1) else '--'
                
                if metric2 in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                    value2_str = f'{value2:.2%}' if not np.isnan(value2) else '--'
                else:
                    value2_str = f'{value2:.2f}' if not np.isnan(value2) else '--'
                
                sel.annotation.set_text(f'Date: {date}\n{metric1}: {value1_str}\n{metric2}: {value2_str}')

        except Exception as e:
            logging.error(f"Error in plot_dual_metric: {str(e)}")
            raise
