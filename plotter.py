import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import logging
import mplcursors
from datetime import datetime
import matplotlib.dates as mdates

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
        from datetime import timedelta
        import numpy as np  # Import numpy for array operations

        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()

        try:
            # Extract dates and values
            dates, values = zip(*data)
            # Convert date strings to datetime objects
            dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]

            # Convert values to floats
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                # Remove '%' if present and convert to float
                values = [float(str(v).strip('%')) / 100 for v in values]
            else:
                values = [float(v) for v in values]

            # Sort the data by date
            sorted_data = sorted(zip(dates, values))
            dates, values = zip(*sorted_data)

            # Plot the data points
            scatter = self.ax.scatter(dates, values, marker='o', color='blue')

            # Plot a line if there's more than one data point
            if len(dates) > 1:
                self.ax.plot(dates, values, color='blue')

                # Set X-axis ticks to the data dates
                self.ax.set_xticks(dates)
            else:
                # Set X-axis limits narrowly around the single date
                single_date = dates[0]
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
                self.ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y))
                )

            # Set Y-axis limits with some padding
            y_min = 0
            y_max = max(values) * 1.1
            self.ax.set_ylim(y_min, y_max)

            # Tight layout to prevent clipping
            self.fig.tight_layout()

            # Add interactive cursor
            cursor = mplcursors.cursor(scatter, hover=True)
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                cursor.connect(
                    "add",
                    lambda sel: sel.annotation.set_text(
                        f'Date: {dates[sel.index].strftime("%Y-%m-%d")}\n'
                        f'{metric}: {values[sel.index]:.2%}'
                    )
                )
            else:
                cursor.connect(
                    "add",
                    lambda sel: sel.annotation.set_text(
                        f'Date: {dates[sel.index].strftime("%Y-%m-%d")}\n'
                        f'{metric}: {values[sel.index]}'
                    )
                )

        except Exception as e:
            logging.error(f"Error in plot_metric: {str(e)}")
            raise

    def embed_plot(self, parent):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
