from tkinter import ttk
import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime

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
        self.current_view = None
        self.notification_count = 0  # Track number of notifications
        
        # Create main containers
        self.main_frame = None
        self.submenu_frame = None
        self.content_frame = None
        self.date_frame = None
        self.table_frame = None
        self.header_label = None
        self.notification_button = None
        
        # Store submenu buttons for styling
        self.submenu_buttons = {}
        
        # Create the table
        self.tree = None
        
        # Create styles for buttons
        self.setup_styles()

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
        
        # Create style for notification button
        style.configure('Notification.TButton',
                    font=('Helvetica', 10))

    def show_trending(self):
        """Display the Trending page."""
        self.clear_page_callback()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        

        # Create top bar with submenu and notifications
        self.create_top_bar()
        # Create submenu frame
        self.create_submenu()
        
        # Create header label
        self.header_label = ttk.Label(self.main_frame, style='Header.TLabel')
        self.header_label.pack(fill=tk.X, pady=(5, 10))
        
        # Create content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Show Top Videos by default
        self.show_top_videos()

    def create_submenu(self):
        """Create the submenu with three options."""
        self.submenu_frame = ttk.Frame(self.main_frame)
        self.submenu_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create submenu buttons
        button_configs = [
            ('top_videos', 'Top Videos', self.show_top_videos),
            ('outperforming', 'Outperforming Benchmark', self.show_outperforming),
            ('trending', 'Starting to Trend', self.show_starting_trend)
        ]
        
        for id_, text, command in button_configs:
            btn = ttk.Button(
                self.submenu_frame,
                text=text,
                command=command,
                style='Submenu.TButton'
            )
            btn.pack(side=tk.LEFT, padx=(0 if id_ == 'top_videos' else 5, 5))
            self.submenu_buttons[id_] = btn
    
    def create_top_bar(self):
        """Create the top bar containing submenu and notifications."""
        top_bar = ttk.Frame(self.main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Create submenu frame on the left
        self.submenu_frame = ttk.Frame(top_bar)
        self.submenu_frame.pack(side=tk.LEFT, fill=tk.X)
        
        # Create notification frame on the right
        notification_frame = ttk.Frame(top_bar)
        notification_frame.pack(side=tk.RIGHT, padx=10)
        
        # Create notification button
        self.notification_button = ttk.Button(
            notification_frame,
            text=f"Notifications ({self.notification_count})",
            style='Notification.TButton',
            command=self.show_notifications
        )
        self.notification_button.pack(side=tk.RIGHT)


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
        
        # Update header with current date
        current_date = datetime.now().strftime("%B %d, %Y")
        self.update_header(f"Top Videos for {current_date}")
        
        self.create_date_picker()
        self.create_video_table()

    def show_outperforming(self):
        """Show the Outperforming Benchmark view."""
        self.clear_content_frame()
        self.current_view = "outperforming"
        self.update_submenu_styling('outperforming')
        self.update_header("Videos Outperforming Benchmark")
        ttk.Label(self.content_frame, text="Outperforming Benchmark (Under Construction)").pack(pady=20)

    def show_starting_trend(self):
        """Show the Starting to Trend view."""
        self.clear_content_frame()
        self.current_view = "starting_trend"
        self.update_submenu_styling('trending')
        self.update_header("Videos Starting to Trend")
        ttk.Label(self.content_frame, text="Starting to Trend (Under Construction)").pack(pady=20)

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
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack scrollbars and tree
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def clear_content_frame(self):
        """Clear all widgets from the content frame."""
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()

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
        
        # Insert data into tree
        for video in videos:
            formatted_row = (
                video[0],  # Video ID
                f"{video[1]:,}",  # Views
                f"{video[2]:,}",  # Shares
                f"{video[3]:,}",  # Comments
                f"${video[4]:,.2f}",  # GMV
                f"{video[5]}%",  # CTR
                f"{video[6]}%",  # CTOR
                f"{video[7]}%"   # Finish Rate
            )
            self.tree.insert('', tk.END, values=formatted_row)

    def treeview_sort_column(self, col):
        """Sort tree contents when a column header is clicked."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # Try to convert to float for numeric sorting
            l.sort(key=lambda t: float(t[0].replace(',', '').replace('$', '').replace('%', '')))
        except ValueError:
            # Fall back to string sorting if conversion fails
            l.sort()
            
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

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