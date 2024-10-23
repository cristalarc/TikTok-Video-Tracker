# processes/__init__.py

from .data_manager import DataManager
from .file_handler import FileHandler
from .settings_manager import SettingsManager
# Define what should be imported when using "from processes import *"
__all__ = ['DataManager', 'FileHandler', 'SettingsManager']
__version__ = "1.0.0"
