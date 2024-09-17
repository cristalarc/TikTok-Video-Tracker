import tkinter as tk
from gui import TikTokTrackerGUI
import os
import platform

def main():
    # Ensure db_backup folder exists
    os.makedirs('db_backup', exist_ok=True)
    
    root = tk.Tk()
    if platform.system() == "Windows":
        root.state('zoomed')
    else:
        root.attributes('-zoomed', True)
    app = TikTokTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()