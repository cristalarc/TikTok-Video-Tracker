#gui.py is the main file that handles the GUI and the interaction between the different components of the app.
import tkinter as tk
import logging
from processes import DataManager
from plotter import Plotter
from processes import SettingsManager
from processes import FileHandler
from .settings_window import SettingsWindow 
from .trending_page import TrendingPage
from .context_menu import ContextMenuManager
from .home_view import HomeView

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
        self.trending_page = TrendingPage(self.master, self.clear_page, self.data_manager)
        self.file_handler = FileHandler(self.data_manager)
        self.home_view = HomeView(self.master, self.data_manager, self.file_handler, self.plotter)
        self.setup_context_menu()  # Set up context menu after creating widgets
        self.create_menu()
        self.home_view.load_and_display_all_videos()
        self.call_home_view()

    def create_menu(self):
        """
        Create the menu bar with Home, Trending, and Settings menus.
        """
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # Home menu
        menubar.add_command(label="Home", command=self.call_home_view)

        # Trending menu
        menubar.add_command(label="Trending", command=self.trending_page.show_trending)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Open Settings", command=self.open_settings_window)

    def open_settings_window(self):
        """
        Open the settings window.
        """
        SettingsWindow(self.master, self.data_manager, self.settings_manager)

    def setup_context_menu(self):
        """Set up the context menu after widgets are created."""
        # We need to create the context menu after the widgets are created because the context menu needs to know about the treeview widget.
        self.context_menu_manager = ContextMenuManager(self.master, self.data_manager, self.plotter, self.home_view.results_tree)
        self.context_menu_manager.create_home_view_context_menu()
        self.home_view.results_tree.bind("<Button-3>", self.context_menu_manager.show_context_menu_home_view)

    def call_home_view(self):
        """
        Calls the home page view to display the relevant frames and widgets.
        """
        # Clear any widgets from other pages
        self.clear_page()

        # Show all widgets related to the home page
        self.home_view.show_home_view()

    def clear_page(self):
        """
        Clear all widgets from the main window and reset the Trending label if present.
        Meant to be a main utility function to clear the page.
        """
        # Hide all widgets
        for widget in self.master.winfo_children():
            widget.pack_forget()