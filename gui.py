#gui.py is the main file that handles the GUI and the interaction between the different components of the app.
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
from data_manager import DataManager
from plotter import Plotter
from datetime import datetime
from settings_manager import SettingsManager
from settings_window import SettingsWindow 
from trending_page import TrendingPage
from file_handler import FileHandler
import os
import webbrowser

# logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress unnecessary logging from matplotlib and PIL
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

class TikTokTrackerGUI:
    def __init__(self, master):
        """
        Initialize the TikTokTrackerGUI.

        Args:
            master (tk.Tk): The root window of the Tkinter application.
        """
        self.master = master
        self.master.title("TikTok Video Tracker")
        self.master.geometry("1000x700")
        self.data_manager = DataManager()
        self.plotter = Plotter()
        self.settings_manager = SettingsManager(self.data_manager)
        self.trending_page = TrendingPage(self.master, self.clear_page)
        self.file_handler = FileHandler(self.data_manager)
        self.create_menu()
        self.create_widgets()
        self.load_and_display_all_videos()
        self.show_home()

    def create_menu(self): #STAYS
        """
        Create the menu bar with Home, Trending, and Settings menus.
        """
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # Home menu
        menubar.add_command(label="Home", command=self.show_home)

        # Trending menu
        menubar.add_command(label="Trending", command=self.trending_page.show_trending)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Open Settings", command=self.open_settings_window)

    def open_settings_window(self): #STAYS
        """
        Open the settings window.
        """
        SettingsWindow(self.master, self.data_manager, self.settings_manager)

    def create_widgets(self):
        """
        Create the main widgets for the GUI.
        """
        # Create Frames for better layout management
        self.top_frame = ttk.Frame(self.master)
        self.top_frame.pack(pady=10, padx=10, fill=tk.X)

        self.middle_frame = ttk.Frame(self.master)
        self.middle_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.bottom_frame = ttk.Frame(self.master)
        self.bottom_frame.pack(pady=10, padx=10, fill=tk.X)

        # Top Frame Widgets
        self.upload_button = ttk.Button(self.top_frame, text="Upload Excel File", command=self.update_video_performance)
        self.upload_button.pack(side=tk.LEFT, padx=5)

        self.clear_data_button = ttk.Button(self.top_frame, text="Clear Video Performance", command=lambda: self.file_handler.clear_video_performance(self.master))
        self.clear_data_button.pack(side=tk.LEFT, padx=5)

        self.restore_button = ttk.Button(self.top_frame, text="Restore Database", command=self.update_restore_database)
        self.restore_button.pack(side=tk.LEFT, padx=5)

        # Search Bar
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.top_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(self.top_frame, text="Search", command=self.search_videos)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Last Performance Date
        self.last_performance_date = tk.StringVar()
        self.last_performance_date_label = ttk.Label(self.top_frame, textvariable=self.last_performance_date)
        self.last_performance_date_label.pack(side=tk.RIGHT, padx=5)

        # Middle Frame Widgets
        # Results Frame
        self.results_frame = ttk.LabelFrame(self.middle_frame, text="Video Database Records")
        self.results_frame.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.BOTH, expand=True)

        columns = ("Video ID", "Video Info", "Date", "Creator", "Products", "Views", "Shares", "Video Revenue ($)")
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, show="headings")

        for col in columns:
            self.results_tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(self.results_tree, _col, False))
            self.results_tree.column(col, width=100)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=self.results_scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_video_select)
        self.create_context_menu()
        self.results_tree.bind("<Button-3>", self.show_context_menu)

        # Details Frame
        self.details_frame = ttk.LabelFrame(self.middle_frame, text="Video Details")
        self.details_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.details_text = tk.Text(self.details_frame, height=10, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Bottom Frame Widgets
        # Timeframe Selection
        self.timeframe_var = tk.StringVar(value='Daily')
        self.timeframe_options = ['Daily', 'Weekly', 'Monthly']
        ttk.Label(self.bottom_frame, text="Select Timeframe:").pack(side=tk.LEFT, padx=5)
        self.timeframe_menu = ttk.Combobox(self.bottom_frame, textvariable=self.timeframe_var, values=self.timeframe_options, state='readonly')
        self.timeframe_menu.pack(side=tk.LEFT, padx=5)

        # Metric Selection
        self.metric_var = tk.StringVar()
        self.metric_options = [
            'VV', 'Likes', 'Comments', 'Shares', 'Product Impressions', 
            'Product Clicks', 'Orders', 'Unit Sales', 'Video Revenue ($)', 
            'CTR', 'V-to-L rate', 'Video Finish Rate', 'CTOR'
        ]
        ttk.Label(self.bottom_frame, text="Select Metric:").pack(side=tk.LEFT, padx=5)
        self.metric_menu = ttk.Combobox(self.bottom_frame, textvariable=self.metric_var, values=self.metric_options, state='readonly')
        self.metric_menu.pack(side=tk.LEFT, padx=5)
        self.plot_button = ttk.Button(self.bottom_frame, text="Plot Metric", command=self.create_selected_video_metric_plot)
        self.plot_button.pack(side=tk.LEFT, padx=5)

        # Second Metric Selection for Dual Plotting
        self.metric_var2 = tk.StringVar()
        ttk.Label(self.bottom_frame, text="Select Second Metric:").pack(side=tk.LEFT, padx=5)
        self.metric_menu2 = ttk.Combobox(self.bottom_frame, textvariable=self.metric_var2, values=self.metric_options, state='readonly')
        self.metric_menu2.pack(side=tk.LEFT, padx=5)
        self.plot_dual_button = ttk.Button(self.bottom_frame, text="Plot Dual Metrics", command=self.create_selected_video_dual_metric_plot)
        self.plot_dual_button.pack(side=tk.LEFT, padx=5)

        # Initialize the last performance date
        latest_date = self.data_manager.get_latest_performance_date()
        self.last_performance_date.set(f"Last Performance Date: {latest_date}")

    def show_home(self): #STAYS
        """
        Display the Home page by arranging the relevant frames and widgets.
        """
        # Clear any widgets from other pages
        self.clear_page()

        # Show all widgets related to the home page
        self.top_frame.pack(pady=10, padx=10, fill=tk.X)
        self.middle_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.bottom_frame.pack(pady=10, padx=10, fill=tk.X)

    def create_context_menu(self): #CONTEXT MENU FILE. The page needs to know which context menu to call
        """
        Create a context menu with options such as copying Video ID and plotting metrics.
        """
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Copy Video ID", command=self.copy_selected_video_id)
        self.context_menu.add_command(label="Open Video in Browser", command=self.open_selected_video_in_browser)
        
        # Create a submenu for Plot Metric
        self.plot_submenu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Plot Metric", menu=self.plot_submenu)
        
        # Add metric options to the submenu
        metrics = ('VV', 'Likes', 'Comments', 'Shares', 'Product Impressions', 
                'Product Clicks', 'Orders', 'Unit Sales', 'Video Revenue ($)', 
                'CTR', 'V-to-L rate', 'Video Finish Rate', 'CTOR')
        for metric in metrics:
            self.plot_submenu.add_command(label=metric, command=lambda m=metric: self.plot_metric_from_context(m))

    def show_context_menu(self, event): #STAYS
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

    def copy_selected_video_id(self): #CONTEXT MENU FILE
        """
        Copy the Video ID of the selected video to the clipboard.
        """
        selected_item = self.results_tree.selection()[0]
        video_id = self.results_tree.item(selected_item)['values'][0]
        self.master.clipboard_clear()
        self.master.clipboard_append(video_id)

    def open_selected_video_in_browser(self): #CONTEXT MENU FILE
        """
        Open the selected video in the default web browser using the video ID and creator name.
        """
        selected_item = self.results_tree.selection()[0]
        video_id = self.results_tree.item(selected_item)['values'][0]
        creator_name = self.results_tree.item(selected_item)['values'][3]  # Assuming 'Creator' is the 4th column
        
        # Remove '@' symbol if it's already in the creator_name
        creator_name = creator_name.lstrip('@')
        
        url = f"https://www.tiktok.com/@{creator_name}/video/{video_id}"
        webbrowser.open(url)

    def update_video_performance(self): #HOME PAGE FILE
        """
        Calls the file handler to upload one or more Excel files containing video performance data.
        Updates the last performance date.
        Updates the UI upon completion.

        """
        success = self.file_handler.upload_video_performance_file(self.master)
        if success:
            # Update the last performance date
            latest_date = self.data_manager.get_latest_performance_date()
            self.last_performance_date.set(f"Last Performance Date: {latest_date}")
            # Refresh the video list
            self.load_and_display_all_videos()
        else:
            # The file handler will display an error message if the upload fails.
            pass
    
    def update_restore_database(self): #HOME PAGE FILE
        """
        Calls the file handler to restore the database from a selected backup file.
        Updates the last performance date.
        """
        success = self.file_handler.restore_database()
        if success:
            latest_date = self.data_manager.get_latest_performance_date()
            self.last_performance_date.set(f"Last Performance Date: {latest_date}")
        else:
            # The file handler will display an error message if the upload fails.
            pass


    def search_videos(self): #HOME PAGE FILE
        """
        Search for videos based on the user's query and display the results in the treeview.
        """
        query = self.search_var.get()
        results = self.data_manager.search_videos(query)
        self.results_tree.delete(*self.results_tree.get_children())
        for result in results:
            self.results_tree.insert("", "end", values=result)

    def on_video_select(self, event): #HOME PAGE FILE
        """
        Event handler for when a video is selected in the Treeview.
        Retrieves the selected video's ID and displays its details.

        Parameters:
        event (tkinter.Event): The event object containing information about the selection event.
        """
        selected_items = self.results_tree.selection()
        if not selected_items:
            # Selection is empty; no action needed
            return
        selected_item = selected_items[0]
        
        # Retrieve the video ID from the selected item
        video_id = self.results_tree.item(selected_item)['values'][0]
        
        # Display the video details
        self.display_video_details(video_id)

    def display_video_details(self, video_id): #HOME PAGE FILE
        """
        Display the details of a specific video in the details text widget.

        Args:
            video_id (str): The ID of the video to display details for.
        """
        details = self.data_manager.get_video_details(video_id)
        if details:
            self.details_text.delete(1.0, tk.END)
            
            # Create a clickable link for the Video ID
            self.details_text.tag_configure("link", foreground="blue", underline=1)
            self.details_text.insert(tk.END, "Video ID: ")
            self.details_text.insert(tk.END, details[0], "link")
            self.details_text.insert(tk.END, "\n")
            
            # Bind the click event to the Video ID
            self.details_text.tag_bind("link", "<Button-1>", lambda e: self.open_video_from_details(details[0], details[3]))
            
            # Change cursor to hand when hovering over the link
            self.details_text.tag_bind("link", "<Enter>", lambda e: self.details_text.config(cursor="hand2"))
            self.details_text.tag_bind("link", "<Leave>", lambda e: self.details_text.config(cursor=""))
            
            # Insert the rest of the details
            self.details_text.insert(tk.END, f"Video Info: {details[1]}\n")
            self.details_text.insert(tk.END, f"Creation Date: {details[2]}\n")
            self.details_text.insert(tk.END, f"Creator: {details[3]}\n")
            self.details_text.insert(tk.END, f"Products: {details[4]}\n")
            self.details_text.insert(tk.END, f"Total Views: {details[5]}\n")
            self.details_text.insert(tk.END, f"Total Likes: {details[6]}\n")
            self.details_text.insert(tk.END, f"Total Comments: {details[7]}\n")
            self.details_text.insert(tk.END, f"Total Shares: {details[8]}\n")
            self.details_text.insert(tk.END, f"Total New Followers: {details[9]}\n")
            self.details_text.insert(tk.END, f"Total Video Revenue: ${details[10]:.2f}\n")
            self.details_text.insert(tk.END, f"Latest Performance Date: {details[11]}\n")
        else:
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, "No details found for this video.")

    def open_video_from_details(self, video_id, creator_name): #HOME PAGE FILE
        """
        Open the selected video in the web browser based on the video ID and creator name.

        Args:
            video_id (str): The ID of the video to open.
            creator_name (str): The name of the video creator.
        """
        # Remove '@' symbol if it's already in the creator_name
        creator_name = creator_name.lstrip('@')
        
        url = f"https://www.tiktok.com/@{creator_name}/video/{video_id}"
        webbrowser.open(url)

    def create_selected_video_metric_plot(self): #HOME PAGE FILE
        """
        Create and display a plot for the selected metric of a selected video based on the chosen timeframe.
        """
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a video to plot.")
            return
        
        video_id = self.results_tree.item(selected_items[0])['values'][0]
        metric = self.metric_var.get()
        if not metric:
            messagebox.showwarning("Warning", "Please select a metric to plot.")
            return
        
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
            messagebox.showwarning("Warning", "Invalid metric selected.")
            return
        
        # Clear existing plot and widgets
        self.plotter.clear_plot()

        # Get the selected timeframe
        timeframe = self.timeframe_var.get()

        # Get week start setting from data_manager
        week_start = self.data_manager.week_start

        # Fetch data with the selected timeframe
        data = self.data_manager.get_time_series_data(video_id, db_metric, timeframe=timeframe, week_start=week_start)
        logging.info(f"Data retrieved for plotting: {data}")
        if not data:
            messagebox.showwarning("Warning", "No data available for the selected metric and timeframe.")
            return
        
        # Plot the data with the selected timeframe
        self.plotter.plot_metric(data, metric, timeframe=timeframe)
        self.plotter.embed_plot(self.master)

    def create_selected_video_dual_metric_plot(self): #HOME PAGE FILE
        """
        Create and display a dual metric plot for the selected video based on the chosen timeframe.
        """
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a video to plot.")
            return

        video_id = self.results_tree.item(selected_items[0])['values'][0]
        metric1 = self.metric_var.get()
        metric2 = self.metric_var2.get()

        if not metric1 or not metric2:
            messagebox.showwarning("Warning", "Please select both metrics to plot.")
            return

        if metric1 == metric2:
            messagebox.showwarning("Warning", "Please select two different metrics to plot.")
            return

        # Convert display metric names to database column names
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

        db_metric1 = metric_mapping.get(metric1)
        db_metric2 = metric_mapping.get(metric2)

        if not db_metric1 or not db_metric2:
            messagebox.showwarning("Warning", "Invalid metrics selected.")
            return

        # Clear existing plot and widgets
        self.plotter.clear_plot()

        # Get the selected timeframe
        timeframe = self.timeframe_var.get()

        # Get week start setting from data_manager
        week_start = self.data_manager.week_start

        # Fetch data with the selected timeframe
        data1 = self.data_manager.get_time_series_data(video_id, db_metric1, timeframe=timeframe, week_start=week_start)
        data2 = self.data_manager.get_time_series_data(video_id, db_metric2, timeframe=timeframe, week_start=week_start)
        logging.info(f"Data retrieved for plotting: data1={data1}, data2={data2}")
        if not data1 or not data2:
            messagebox.showwarning("Warning", "No data available for the selected metrics and timeframe.")
            return
        
        # Plot the data with the selected timeframe
        self.plotter.plot_dual_metric(data1, metric1, data2, metric2, timeframe=timeframe)
        self.plotter.embed_plot(self.master)

    def plot_metric_from_context(self, metric): #HOME PAGE FILE
        """
        Plot a selected metric from the context menu for the selected video.

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
                messagebox.showwarning("Warning", "Invalid metric selected.")
                return
            
            # Clear existing plot and widgets
            self.plotter.clear_plot()
            data = self.data_manager.get_time_series_data(video_id, db_metric)
            self.plotter.plot_metric(data, metric)
            self.plotter.embed_plot(self.master)

    def load_and_display_all_videos(self): #HOME PAGE FILE
        """
        Load all videos from the database and display them in the treeview.
        """
        self.results_tree.delete(*self.results_tree.get_children())
        videos = self.data_manager.get_all_videos()
        for video in videos:
            self.results_tree.insert("", "end", values=video)

    def treeview_sort_column(self, tv, col, reverse): #HOME PAGE FILE
        """
        Sort the treeview based on a specified column.

        Args:
            tv (ttk.Treeview): The treeview widget to sort.
            col (str): The column to sort by.
            reverse (bool): Whether to sort in reverse order.
        """
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def clear_page(self): #STAYS
        """
        Clear all widgets from the main window and reset the Trending label if present.
        Meant to be a main utility function to clear the page.
        """
        # Hide all widgets
        for widget in self.master.winfo_children():
            widget.pack_forget()