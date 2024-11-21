import tkinter as tk
import os
import platform
from gui.main_gui import TikTokTrackerGUI
from config import DATA_DIR, DB_BACKUP_DIR
from processes.database_migration import run_migration #TODO Delete

def main():
    # Run database migration before starting the application #TODO Delete
    # run_migration()
    
    root = tk.Tk()
    if platform.system() == "Windows":
        root.state('zoomed')
    else:
        root.attributes('-zoomed', True)
    app = TikTokTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()