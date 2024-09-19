import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
from data_manager import DataManager
from plotter import Plotter
from datetime import datetime
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TikTokTrackerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("TikTok Video Tracker")
        self.master.geometry("1000x700")
        self.data_manager = DataManager()
        self.plotter = Plotter()

        self.create_widgets()
        self.load_all_videos()

    def create_widgets(self):
        # File upload button
        self.upload_button = ttk.Button(self.master, text="Upload Excel File", command=self.upload_file)
        self.upload_button.pack(pady=10, side=tk.LEFT, padx=5)

        # Clear video performance button
        self.clear_data_button = ttk.Button(self.master, text="Clear Video Performance", command=self.clear_video_performance)
        self.clear_data_button.pack(pady=10, side=tk.LEFT, padx=5)

        # Restore Database button
        self.restore_button = ttk.Button(self.master, text="Restore Database", command=self.restore_database)
        self.restore_button.pack(pady=10, side=tk.LEFT, padx=5)

        # Search bar
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.master, textvariable=self.search_var, width=50)
        self.search_entry.pack(pady=5)
        self.search_button = ttk.Button(self.master, text="Search", command=self.search_videos)
        self.search_button.pack(pady=5)

        # Last Performance Date label
        self.last_performance_date = tk.StringVar()
        self.last_performance_date_label = ttk.Label(self.master, textvariable=self.last_performance_date)
        self.last_performance_date_label.pack(anchor='ne', padx=10, pady=5)

        # Search results
        self.results_frame = ttk.LabelFrame(self.master, text="Video Database Records")
        self.results_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
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

        # Initialize the last performance date
        latest_date = self.data_manager.get_latest_performance_date()
        self.last_performance_date.set(f"Last Performance Date: {latest_date}")

    def upload_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                df = self.data_manager.read_excel(file_path)
                filtered_df = self.data_manager.filter_videos(df)
                
                # Check if data already exists for this date
                date = filtered_df['performance_date'].iloc[0]
                if self.data_manager.check_existing_data(date):
                    response = messagebox.askyesno("Data Already Exists", 
                        f"Data for {date} already exists in the database. Do you want to replace it?")
                    if response:
                        self.data_manager.replace_data_for_date(filtered_df, date)
                        messagebox.showinfo("Success", f"Data for {date} has been replaced successfully!")
                    else:
                        messagebox.showinfo("Info", "Upload cancelled.")
                        self.last_performance_date.set(f"Last Performance Date: {date}") ## Is this correct?
                        return
                else:
                    self.data_manager.insert_or_update_records(filtered_df)
                    messagebox.showinfo("Success", "File uploaded and processed successfully! Database backup created.")
                    self.last_performance_date.set(f"Last Performance Date: {date}")
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
            self.details_text.insert(tk.END, f"Latest Performance Date: {details[5]}\n")
            self.details_text.insert(tk.END, f"Views: {details[6]}\n")
            self.details_text.insert(tk.END, f"Likes: {details[7]}\n")
            self.details_text.insert(tk.END, f"Comments: {details[8]}\n")
            self.details_text.insert(tk.END, f"Shares: {details[9]}\n")
            self.details_text.insert(tk.END, f"New Followers: {details[10]}\n")
            self.details_text.insert(tk.END, f"Video Revenue ($): {details[11]}\n")
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

    def restore_database(self):
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Set the initial directory to the db_backup folder
        initial_dir = os.path.join(current_dir, 'db_backup')
        
        # Open file dialog
        backup_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Database Backup",
            filetypes=[("Database files", "*.db")]
        )
        
        if backup_path:
            result = self.data_manager.restore_database(backup_path)
            if result:
                messagebox.showinfo("Success", "Database restored successfully.")
                latest_date = self.data_manager.get_latest_performance_date()
                self.last_performance_date.set(f"Last Performance Date: {latest_date}")
            else:
                messagebox.showerror("Error", "Failed to restore database. Check the log for details.")

    def load_all_videos(self):
        self.results_tree.delete(*self.results_tree.get_children())
        videos = self.data_manager.get_all_videos()
        for video in videos:
            self.results_tree.insert("", "end", values=video)

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))