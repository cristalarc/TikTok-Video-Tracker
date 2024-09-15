import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import logging
import mplcursors

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Plotter:
    def __init__(self):
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = None

    def plot_metric(self, data, metric):
        self.ax.clear()
        dates, values = zip(*data)
        scatter = self.ax.scatter(dates, values, marker='o')
        self.ax.plot(dates, values)
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel(metric)
        self.ax.set_title(f'{metric} Over Time')
        self.ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()

        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f'Date: {dates[sel.index]}\n{metric}: {values[sel.index]}'))

    def embed_plot(self, parent):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
