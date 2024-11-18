from tkinter import ttk
import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime
from .context_menu import ContextMenuManager
from processes.virality_calculator import ViralityCalculator
import logging

# logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TrendingPage:
    def __init__(self, master, clear_page_callback, data_manager):
        """
        Initialize the TrendingPage.

        Args:
            master (tk.Tk or tk.Toplevel): The parent window.
            clear_page_callback (function): A callback function to clear the page.
        """
        self.master = master
        self.clear_page_callback = clear_page_callback
        self.data_manager = data_manager
        self.virality_calculator = ViralityCalculator(self.data_manager)
        self.current_view = None
        self.notification_count = 0  # Track number of notifications
        
        # Create main containers
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, pady=0)
        
        # Create styles for widgets
        self.setup_styles()
        
        # Create the top bar (which now includes the submenu)
        self.create_top_bar()
        
        # Create the content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=0)
        
        # Create the table
        self.tree = None

        # Create context menu manager
        self.context_menu_manager = None

        # Create search bar
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_search)

    def setup_styles(self):
        """Setup custom styles for widgets."""
        style = ttk.Style()
        
        # Create styles for regular and active (bold) submenu buttons
        style.configure('Submenu.TButton', 
                    font=('Helvetica', 10))
        style.configure('Submenu.Active.TButton',
                    font=('Helvetica', 10, 'bold'))
        
        # Create style for header label
        style.configure('Header.TLabel', 
                    font=('Helvetica', 12, 'bold'),
                    padding=10)
        
        # Create style for notification button and label
        style.configure('Notification.TButton',
                    font=('Helvetica', 10))
        style.configure('Notification.TLabel',
                    font=('Helvetica', 10))

    def show_trending_trending_page(self):
        """Display the Trending page."""
        self.clear_page_callback()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create top bar with submenu and notifications
        self.create_top_bar()
        
        # Create header label
        self.header_label = ttk.Label(self.main_frame, style='Header.TLabel')
        self.header_label.pack(fill=tk.X, pady=(5, 10))
        
        # Create content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Show Top Videos by default
        self.show_top_videos()
    
    def create_top_bar(self):
        """Create the top bar containing submenu and notifications."""
        # Create top bar frame
        self.top_bar = ttk.Frame(self.main_frame)
        self.top_bar.pack(fill=tk.X, pady=(0, 0))
        
        # Create single frame for all top bar elements
        nav_frame = ttk.Frame(self.top_bar)
        nav_frame.pack(fill=tk.X)
        
        # Initialize submenu buttons dictionary
        self.submenu_buttons = {}
        
        # Create submenu buttons directly in nav_frame
        buttons = [
            ("Top Videos", self.show_top_videos),
            ("Outperforming Benchmark", self.show_outperforming),
            ("Trending Videos", self.show_trending_videos)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(
                nav_frame,
                text=text,
                style='Submenu.TButton',
                command=command
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.submenu_buttons[text.lower().replace(' ', '_')] = btn
        
        # Create a frame for right-side elements to ensure proper spacing
        right_frame = ttk.Frame(nav_frame)
        right_frame.pack(side=tk.RIGHT)
        
        # Create notification button first (rightmost element)
        self.notification_button = ttk.Button(
            right_frame,
            text=f"Notifications ({self.notification_count})",
            style='Notification.TButton',
            command=self.show_notifications
        )
        self.notification_button.pack(side=tk.RIGHT, padx=(0, 0))
        
        # Add Last Performance Date
        try:
            last_date = self.data_manager.get_latest_performance_date()
            if last_date:
                ttk.Label(
                    right_frame,
                    text=f"Last Performance Date: {last_date}"
                ).pack(side=tk.RIGHT, padx=(0, 10))
        except Exception as e:
            logging.error(f"Error displaying last performance date: {e}")

    def update_search(self, *args):
        """Filter the table to show only matching videos."""
        search_term = self.search_var.get().lower().strip()
        
        # Store current videos if not already stored
        if not hasattr(self, '_current_videos'):
            self._current_videos = []
            for item in self.tree.get_children():
                self._current_videos.append(self.tree.item(item)['values'])
        
        # Clear the current table
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # If search is empty, show all videos
        if not search_term:
            for video in self._current_videos:
                self.tree.insert('', tk.END, values=video)
            return
        
        # Show only matching videos
        for video in self._current_videos:
            if search_term in str(video[0]).lower():  # video[0] is Video ID
                self.tree.insert('', tk.END, values=video)

    def update_submenu_styling(self, active_view):
        """Update the styling of submenu buttons based on the active view."""
        for view, button in self.submenu_buttons.items():
            button.configure(style='Submenu.Active.TButton' if view == active_view else 'Submenu.TButton')

    def update_header(self, text):
        """Update the header text."""
        if self.header_label:
            self.header_label.configure(text=text)

    def show_top_videos(self):
        """Show the Top Videos view."""
        self.clear_content_frame()
        self.current_view = "top_videos"
        self.update_submenu_styling('top_videos')
        
        # Create date and search container
        controls_frame = ttk.Frame(self.content_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Add date picker
        date_frame = ttk.Frame(controls_frame)
        date_frame.pack(side=tk.LEFT)
        
        ttk.Label(date_frame, text="Select Date:").pack(side=tk.LEFT)
        self.date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.date_picker.pack(side=tk.LEFT, padx=(5, 20))
        self.date_picker.bind("<<DateEntrySelected>>", self.update_top_videos)
        
        # Add search bar
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(side=tk.LEFT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Create header label
        self.header_label = ttk.Label(self.content_frame, style='Header.TLabel')
        self.header_label.pack(fill=tk.X, pady=(5, 0))
        
        # Create and show the table
        self.create_video_table()
        self.update_top_videos()

    def show_outperforming(self):
        """Show the Outperforming Benchmark view."""
        self.clear_content_frame()
        self.current_view = "outperforming"
        self.update_submenu_styling('outperforming')
        
        # Create header label
        self.header_label = ttk.Label(self.content_frame, style='Header.TLabel')
        self.header_label.pack(fill=tk.X, pady=(5, 0))
        
        # Update header text
        self.update_header("Videos Outperforming Benchmark")
        
        # Add placeholder content
        ttk.Label(
            self.content_frame,
            text="Outperforming Benchmark (Under Construction)",
            padding=20
        ).pack(expand=True)

    def create_date_picker(self):
        """Create the date picker frame."""
        self.date_frame = ttk.Frame(self.content_frame)
        self.date_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Add date picker label
        ttk.Label(self.date_frame, text="Select Date:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Add date picker
        self.date_picker = DateEntry(
            self.date_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            maxdate=datetime.now()
        )
        self.date_picker.pack(side=tk.LEFT)
        self.date_picker.bind("<<DateEntrySelected>>", self.update_top_videos)

    def create_video_table(self):
        """Create the table for displaying video data."""
        self.table_frame = ttk.Frame(self.content_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview
        columns = ('Video ID', 'Views', 'Shares', 'Comments', 'GMV', 'CTR', 'CTOR', 'Finish Rate')
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        
        # Set column headings and formats
        column_formats = {
            'Video ID': {'width': 100, 'anchor': 'w'},
            'Views': {'width': 80, 'anchor': 'e'},
            'Shares': {'width': 80, 'anchor': 'e'},
            'Comments': {'width': 80, 'anchor': 'e'},
            'GMV': {'width': 100, 'anchor': 'e'},
            'CTR': {'width': 80, 'anchor': 'e'},
            'CTOR': {'width': 80, 'anchor': 'e'},
            'Finish Rate': {'width': 100, 'anchor': 'e'}
        }
        
        for col, format_info in column_formats.items():
            self.tree.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(c))
            self.tree.column(col, width=format_info['width'], anchor=format_info['anchor'])
        
        # Configure tag for search highlighting
        self.tree.tag_configure('match', background='yellow')

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack scrollbars and tree
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Add context menu
        self.context_menu_manager = ContextMenuManager(self.master, self.data_manager, None, self.tree)
        self.context_menu_manager.create_trending_view_context_menu()
        self.tree.bind("<Button-3>", self.context_menu_manager.show_context_menu_trending_view)

    def clear_content_frame(self):
        """Clear all widgets from the content frame."""
        if hasattr(self, 'content_frame') and self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        else:
            self.content_frame = ttk.Frame(self.main_frame)
            self.content_frame.pack(fill=tk.BOTH, expand=True, pady=0)

    def format_video_data(self, video_data):
        """
        Format video data for display, converting None values to appropriate zero formats.
        
        Args:
            video_data (tuple): Raw video data from database
            
        Returns:
            tuple: Formatted video data for display
        """
        return (
            video_data[0],  # Video ID (no formatting needed)
            f"{video_data[1]:,}" if video_data[1] is not None else "0",  # Views
            f"{video_data[2]:,}" if video_data[2] is not None else "0",  # Shares
            f"{video_data[3]:,}" if video_data[3] is not None else "0",  # Comments
            f"${video_data[4]:,.2f}" if video_data[4] is not None else "$0.00",  # GMV
            f"{video_data[5]}%" if video_data[5] is not None else "0%",  # CTR
            f"{video_data[6]}%" if video_data[6] is not None else "0%",  # CTOR
            f"{video_data[7]}%" if video_data[7] is not None else "0%"   # Finish Rate
    )

    def update_top_videos(self, event=None):
        """Update the top videos table based on the selected date."""
        selected_date = self.date_picker.get_date()
        formatted_date = selected_date.strftime("%B %d, %Y")
        self.update_header(f"Top Videos for {formatted_date}")
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get data from database
        videos = self.data_manager.get_videos_by_date(selected_date)
        
        # Store the current videos for search functionality
        self._current_videos = []
        
        # Insert formatted data into tree
        for video in videos:
            formatted_row = self.format_video_data(video)
            self.tree.insert('', tk.END, values=formatted_row)
            self._current_videos.append(formatted_row)
        
        # Clear the search bar
        self.search_var.set("")

    def treeview_sort_column(self, col):
        """Sort tree contents when a column header is clicked."""
        # Get current sorting order
        ascending = True
        if hasattr(self, '_last_sort'):
            if self._last_sort == (col, True):
                ascending = False
        
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # Try to convert to float for numeric sorting
            # Remove any formatting characters ($, %, ,) before converting
            l.sort(key=lambda t: float(t[0].replace(',', '').replace('$', '').replace('%', '')), 
                reverse=not ascending)
        except ValueError:
            # Fall back to string sorting if conversion fails
            l.sort(reverse=not ascending)
        
        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        
        # Store the sort state
        self._last_sort = (col, ascending)
        
        # Reverse sort next time if clicked again
        self.tree.heading(col, 
            command=lambda c=col: self.treeview_sort_column(c))

    def show_notifications(self):
        """Show the notifications popup relative to the main window."""
        # Create a toplevel window for notifications
        popup = tk.Toplevel(self.master)
        popup.title("Notifications")
        popup.geometry("300x400")
        
        # Make the window modal
        popup.transient(self.master)
        popup.grab_set()
        
        # Calculate position relative to main window
        main_window_x = self.master.winfo_x()
        main_window_y = self.master.winfo_y()
        main_window_width = self.master.winfo_width()
        
        # Position the popup on the right side of the main window
        popup_x = main_window_x + main_window_width - 320  # 300px width + 20px padding
        popup_y = main_window_y + 50  # Offset from top
        
        # Set the position
        popup.geometry(f"+{popup_x}+{popup_y}")
        
        # Add a close button
        ttk.Button(
            popup,
            text="Close",
            command=popup.destroy
        ).pack(side=tk.BOTTOM, pady=10)
        
        # If no notifications
        if self.notification_count == 0:
            ttk.Label(
                popup,
                text="No new notifications",
                padding=20
            ).pack(expand=True)
        else:
            # Here you would add actual notifications
            # This is a placeholder for future implementation
            ttk.Label(
                popup,
                text="Notification content will appear here",
                padding=20
            ).pack(expand=True)

# Trending Videos View

    def create_trending_videos_content_frame(self):
        """
        Create the content frame where the trending videos will be displayed.
        """
        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def update_header(self, title):
        """
        Update the header with the given title.

        Args:
            title (str): Title text to display.
        """
        header_label = ttk.Label(self.content_frame, text=title, font=('Helvetica', 16))
        header_label.pack(pady=10)

    def show_trending_videos(self):
        """
        Display the trending videos using the virality calculator.
        """
        self.clear_content_frame()
        self.create_trending_videos_content_frame()
        self.update_header("Trending Videos")

        # Retrieve trending videos
        trending_videos_df = self.virality_calculator.get_trending_videos()

        # If no trending videos are found, display a message
        if trending_videos_df.empty:
            tk.Label(self.content_frame, text="No trending videos found.").pack()
            return

        # Display the trending videos in a table
        self.display_trending_videos(trending_videos_df)

    def display_trending_videos(self, df):
        """
        Display the trending videos in a Treeview widget.

        Args:
            df (DataFrame): DataFrame containing trending videos.
        """
        # Define columns to display
        columns = ('Video ID', 'Trending Score', 'Total Views', 'Daily Views', 'DGR (%)', 'ER (%)')

        # Create Treeview
        self.tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')

        # Set up column headings and formatting
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')

        # Insert data into the Treeview
        for _, row in df.iterrows():
            self.tree.insert('', tk.END, values=(
                row['video_id'],
                f"{row['trending_score']:.2f}",
                int(row['total_views']),
                int(row['daily_views']),
                f"{row['dgr']:.2f}",
                f"{row['er']:.2f}"
            ))

        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)