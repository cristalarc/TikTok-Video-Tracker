import tkinter as tk
from gui import TikTokTrackerGUI

def main():
    root = tk.Tk()
    app = TikTokTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()