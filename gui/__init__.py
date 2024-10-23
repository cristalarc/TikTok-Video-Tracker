# gui/__init__.py

from .main_gui import TikTokTrackerGUI
from .home_view import HomeView
from .trending_page import TrendingPage
from .settings_window import SettingsWindow
from .context_menu import ContextMenuManager

# Define what should be imported when using "from gui import *"
__all__ = ['TikTokTrackerGUI', 'HomeView', 'TrendingPage', 'SettingsWindow', 'ContextMenuManager']
__version__ = "1.0.0"
