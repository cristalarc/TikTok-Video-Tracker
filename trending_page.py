import tkinter as tk
from tkinter import ttk

class TrendingPage:
    def __init__(self, master, clear_page_callback):
        """
        Initialize the TrendingPage.

        Args:
            master (tk.Tk or tk.Toplevel): The parent window.
            clear_page_callback (function): A callback function to clear the page.
        """
        self.master = master
        self.clear_page_callback = clear_page_callback
        self.trending_label = None

    def show_trending(self):
        """
        Display the Trending page, replacing current content with Trending-related widgets.
        """
        # Use the provided callback to clear any widgets from other pages
        self.clear_page_callback()

        # Show the Trending page content
        self.trending_label = ttk.Label(self.master, text="Trending Page (Under Construction)")
        self.trending_label.pack(pady=20)
