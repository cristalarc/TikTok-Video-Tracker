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
        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
        else:
            self.ax.clear()

        try:
            dates, values = zip(*data)
            dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
            
            # Convert percentage strings to floats
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                values = [float(v.strip('%')) / 100 for v in values]
            else:
                values = [float(v) for v in values]

            scatter = self.ax.scatter(dates, values, marker='o')
            self.ax.plot(dates, values)
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel(metric)
            self.ax.set_title(f'{metric} Over Time')
            self.ax.tick_params(axis='x', rotation=45)

            # Format x-axis as dates
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.fig.autofmt_xdate()  # Rotate and align the tick labels

            # Handle percentage-based metrics
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y)))
            
            self.ax.set_ylim(0, max(values) * 1.1)  # Set y-axis limit to 110% of max value
            self.fig.tight_layout()

            cursor = mplcursors.cursor(scatter, hover=True)
            if metric in ['CTR', 'CTOR', 'Video Finish Rate', 'V-to-L rate']:
                cursor.connect("add", lambda sel: sel.annotation.set_text(f'Date: {dates[sel.index].strftime("%Y-%m-%d")}\n{metric}: {values[sel.index]:.2%}'))
            else:
                cursor.connect("add", lambda sel: sel.annotation.set_text(f'Date: {dates[sel.index].strftime("%Y-%m-%d")}\n{metric}: {values[sel.index]}'))
        except Exception as e:
            logging.error(f"Error in plot_metric: {str(e)}")
            raise

    def embed_plot(self, parent):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
