#context_menu.py is used to create a context menu in any relevant page of the app.
import tkinter as tk
from tkinter import messagebox
import webbrowser

class ContextMenuManager:
    def __init__(self, master, data_manager, plotter, results_tree):
        self.master = master
        self.data_manager = data_manager
        self.plotter = plotter
        self.results_tree = results_tree
        self.context_menu = None

    ## Home View Context Menu
    def create_home_view_context_menu(self):
        """
        Create a context menu with options such as copying Video ID and plotting metrics.
        """
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Copy Video ID", command=self.copy_selected_video_id)
        self.context_menu.add_command(label="Open Video in Browser", command=self.open_selected_video_in_browser)
        
        # Add plot options
        plot_menu = tk.Menu(self.context_menu, tearoff=0)
        metrics = ['VV', 'Likes', 'Comments', 'Shares', 'Product Impressions', 'Product Clicks', 
                   'Orders', 'Unit Sales', 'Video Revenue ($)', 'CTR', 'V-to-L rate', 
                   'Video Finish Rate', 'CTOR']
        for metric in metrics:
            plot_menu.add_command(label=metric, command=lambda m=metric: self.plot_metric_from_context_home_view(m))
        self.context_menu.add_cascade(label="Plot Metric", menu=plot_menu)

    def plot_metric_from_context_home_view(self, metric):
        """
        Plot a selected metric from the context menu for the selected video on the Home View.

        Args:
            metric (str): The metric to plot.
        """
        selected_items = self.results_tree.selection()
        if selected_items:
            video_id = self.results_tree.item(selected_items[0])['values'][0]
            
            # Convert display metric name to database column name
            metric_mapping = {
                'VV': 'vv',
                'Likes': 'likes',
                'Comments': 'comments',
                'Shares': 'shares',
                'Product Impressions': 'product_impressions',
                'Product Clicks': 'product_clicks',
                'Orders': 'orders',
                'Unit Sales': 'unit_sales',
                'Video Revenue ($)': 'video_revenue',
                'CTR': 'ctr',
                'V-to-L rate': 'v_to_l_rate',
                'Video Finish Rate': 'video_finish_rate',
                'CTOR': 'ctor'
            }
            db_metric = metric_mapping.get(metric)
            if not db_metric:
                tk.messagebox.showwarning("Warning", "Invalid metric selected.")
                return
            
            # Clear existing plot and widgets
            self.plotter.clear_plot()
            data = self.data_manager.get_time_series_data(video_id, db_metric)
            self.plotter.plot_metric(data, metric)
            self.plotter.embed_plot(self.master)

    def show_context_menu_home_view(self, event):
        """
        Display the context menu at the cursor's position if a treeview item is clicked.

        Args:
            event (tk.Event): The event object containing event data.
        """
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.results_tree.focus(item)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    ## Utility Functions
    def copy_selected_video_id(self):
        """
        Copy the Video ID of the selected video to the clipboard.
        """
        selected_item = self.results_tree.selection()[0]
        video_id = self.results_tree.item(selected_item)['values'][0]
        self.master.clipboard_clear()
        self.master.clipboard_append(video_id)

    def open_selected_video_in_browser(self):
        """
        Open the selected video in the default web browser using the video ID and creator name.
        """
        selected_item = self.results_tree.selection()[0]
        video_id = self.results_tree.item(selected_item)['values'][0]
        
        # Get video details from database to find creator name
        video_details = self.data_manager.get_video_details(video_id)
        if video_details and video_details[3]:  # Index 3 contains creator_name in get_video_details
            creator_name = str(video_details[3]).lstrip('@')
            url = f"https://www.tiktok.com/@{creator_name}/video/{video_id}"
            webbrowser.open(url)
        else:
            messagebox.showerror("Error", "Could not find creator information for this video.")

    def create_trending_view_context_menu(self):
        """
        Create a context menu for the trending view with basic options (no plotting).
        """
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Copy Video ID", command=self.copy_selected_video_id)
        self.context_menu.add_command(label="Open Video in Browser", command=self.open_selected_video_in_browser)

    def show_context_menu_trending_view(self, event):
        """
        Display the context menu at the cursor's position if a treeview item is clicked.
        
        Args:
            event (tk.Event): The event object containing event data.
        """
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.results_tree.focus(item)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()