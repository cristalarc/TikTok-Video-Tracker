import tkinter as tk
import os
import platform
from gui.main_gui import TikTokTrackerGUI
from config import DATA_DIR, DB_BACKUP_DIR

def main():
    root = tk.Tk()
    if platform.system() == "Windows":
        root.state('zoomed')
    else:
        root.attributes('-zoomed', True)
    app = TikTokTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()