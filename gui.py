import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
from data_manager import DataManager
from plotter import Plotter
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TikTokTrackerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("TikTok Video Tracker")
        self.master.geometry("1000x700")
        self.data_manager = DataManager()
        self.plotter = Plotter()

        self.create_widgets()

    def create_widgets(self):
        # File upload button
        self.upload_button = ttk.Button(self.master, text="Upload Excel File", command=self.upload_file)
        self.upload_button.pack(pady=10, side=tk.LEFT, padx=5)

        # Clear video performance button
        self.clear_data_button = ttk.Button(self.master, text="Clear Video Performance", command=self.clear_video_performance)
        self.clear_data_button.pack(pady=10, side=tk.LEFT, padx=5)

        # Search bar
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.master, textvariable=self.search_var, width=50)
        self.search_entry.pack(pady=5)
        self.search_button = ttk.Button(self.master, text="Search", command=self.search_videos)
        self.search_button.pack(pady=5)

        # Search results
        self.results_frame = ttk.Frame(self.master)
        self.results_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        self.results_tree = ttk.Treeview(self.results_frame, columns=("Video ID", "Video Info", "Date", "Creator", "Products", "Views"), show="headings")
        self.results_tree.heading("Video ID", text="Video ID")
        self.results_tree.heading("Video Info", text="Video Info")
        self.results_tree.heading("Date", text="Date")
        self.results_tree.heading("Creator", text="Creator")
        self.results_tree.heading("Products", text="Products")
        self.results_tree.heading("Views", text="Views")
        self.results_tree.column("Video ID", width=100)
        self.results_tree.column("Video Info", width=200)
        self.results_tree.column("Date", width=100)
        self.results_tree.column("Creator", width=150)
        self.results_tree.column("Products", width=200)
        self.results_tree.column("Views", width=100)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=self.results_scrollbar.set)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_video_select)

        # Video details
        self.details_frame = ttk.LabelFrame(self.master, text="Video Details")
        self.details_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.details_text = tk.Text(self.details_frame, height=10, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Metric selection for plotting
        self.metric_var = tk.StringVar()
        self.metric_combobox = ttk.Combobox(self.master, textvariable=self.metric_var)
        self.metric_combobox['values'] = ('VV', 'Likes', 'Comments', 'Shares', 'New followers', 'V-to-L clicks',
                                          'Product Impressions', 'Product Clicks', 'Buyers', 'Orders', 'Unit Sales',
                                          'Video Revenue ($)', 'GPM ($)', 'Shoppable video attributed GMV ($)',
                                          'CTR', 'V-to-L rate', 'Video Finish Rate', 'CTOR')
        self.metric_combobox.pack(pady=5)
        self.plot_button = ttk.Button(self.master, text="Plot Metric", command=self.plot_metric)
        self.plot_button.pack(pady=5)

    def upload_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                df = self.data_manager.read_excel(file_path)
                filtered_df = self.data_manager.filter_videos(df)
                self.data_manager.insert_or_update_records(filtered_df)
                messagebox.showinfo("Success", "File uploaded and processed successfully! Database backup created.")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            logging.error(f"Error in upload_file: {str(ve)}")
        except Exception as e:
            error_message = f"An error occurred while processing the file: {str(e)}\n\nPlease check the log for more details."
            messagebox.showerror("Error", error_message)
            logging.error(f"Error in upload_file: {str(e)}", exc_info=True)

    def search_videos(self):
        query = self.search_var.get()
        results = self.data_manager.search_videos(query)
        self.results_tree.delete(*self.results_tree.get_children())
        for result in results:
            self.results_tree.insert("", "end", values=result)

    def on_video_select(self, event):
        selected_item = self.results_tree.selection()[0]
        video_id = self.results_tree.item(selected_item)['values'][0]
        self.display_video_details(video_id)

    def display_video_details(self, video_id):
        details = self.data_manager.get_video_details(video_id)
        if details:
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"Video ID: {details[0]}\n")
            self.details_text.insert(tk.END, f"Video Info: {details[1]}\n")
            self.details_text.insert(tk.END, f"Creation Date: {details[2]}\n")
            self.details_text.insert(tk.END, f"Creator: {details[3]}\n")
            self.details_text.insert(tk.END, f"Products: {details[4]}\n")
            self.details_text.insert(tk.END, f"Latest Performance Date: {details[6]}\n")
            self.details_text.insert(tk.END, f"Views: {details[7]}\n")
            self.details_text.insert(tk.END, f"Likes: {details[8]}\n")
            self.details_text.insert(tk.END, f"Comments: {details[9]}\n")
            self.details_text.insert(tk.END, f"Shares: {details[10]}\n")
            self.details_text.insert(tk.END, f"New Followers: {details[11]}\n")
            # Add more details as needed

    def plot_metric(self):
        selected_items = self.results_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a video to plot.")
            return
        
        video_id = self.results_tree.item(selected_items[0])['values'][0]
        metric = self.metric_var.get()
        if not metric:
            messagebox.showwarning("Warning", "Please select a metric to plot.")
            return
        
        data = self.data_manager.get_time_series_data(video_id, metric)
        self.plotter.plot_metric(data, metric)
        self.plotter.embed_plot(self.master)

    def clear_video_performance(self):
        # Create a simple dialog to get the date
        date = simpledialog.askstring("Clear Video Performance", "Enter date to clear (YYYY-MM-DD):")
        if not date:
            return

        try:
            # Validate date format
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        try:
            result = self.data_manager.clear_data_for_date(date)
            if result:
                messagebox.showinfo("Success", f"Data for {date} has been cleared. A backup was created before clearing.")
            else:
                messagebox.showinfo("Info", f"No data found for {date}.")
        except Exception as e:
            error_message = f"An error occurred while clearing data: {str(e)}\n\nPlease check the log for more details."
            messagebox.showerror("Error", error_message)
            logging.error(f"Error in clear_video_performance: {str(e)}", exc_info=True)