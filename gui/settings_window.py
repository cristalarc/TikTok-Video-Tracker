#settings_window.py is the file that handles the settings window of the app.
import tkinter as tk
from tkinter import ttk, messagebox

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, data_manager, settings_manager):
        """
        Initialize the SettingsWindow, allowing users to adjust application settings.

        Args:
            parent (tk.Tk): The parent window.
            data_manager (DataManager): An instance of DataManager for accessing settings.
            settings_manager (SettingsManager): An instance of SettingsManager for saving settings.
        """
        super().__init__(parent)
        self.title("Settings")
        self.data_manager = data_manager
        self.settings_manager = settings_manager
        self.create_widgets_settings()
        
        # Make this window transient for the parent window
        self.transient(parent)
        
        # Set the window position relative to the parent window
        self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        
        # Make the window modal
        self.grab_set()
        
    def create_widgets_settings(self):
        """
        Create and arrange widgets within the Settings window for adjusting thresholds and week start day.
        """
        # Video View Ingestion Threshold setting
        ttk.Label(self, text="Video View Ingestion Threshold:").grid(row=0, column=0, padx=5, pady=5)
        self.threshold_var = tk.StringVar(value=str(self.data_manager.vv_threshold))
        ttk.Entry(self, textvariable=self.threshold_var).grid(row=0, column=1, padx=5, pady=5)

        # Week Start Day setting
        ttk.Label(self, text="Week Starts On:").grid(row=1, column=0, padx=5, pady=5)
        self.week_start_var = tk.StringVar(value=self.data_manager.week_start)
        self.week_start_options = ['Sunday', 'Monday']
        ttk.Combobox(self, textvariable=self.week_start_var, values=self.week_start_options, state='readonly').grid(row=1, column=1, padx=5, pady=5)

        # Save button
        ttk.Button(self, text="Save", command=self.save_user_settings).grid(row=2, column=0, columnspan=2, pady=10)

    def save_user_settings(self):
        """
        Validate and save the user's settings through the SettingsManager.
        """
        try:
            # Validate Video View Ingestion Threshold
            new_threshold = int(self.threshold_var.get())
            if new_threshold <= 0:
                raise ValueError("Threshold must be a positive integer")
            
            # Validate Week Start Day
            new_week_start = self.week_start_var.get()
            if new_week_start not in ['Sunday', 'Monday']:
                raise ValueError("Week start day must be 'Sunday' or 'Monday'")

            # Save settings using SettingsManager
            self.settings_manager.save_settings_to_storage(new_threshold, new_week_start)

            messagebox.showinfo("Success", "Settings saved successfully")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
