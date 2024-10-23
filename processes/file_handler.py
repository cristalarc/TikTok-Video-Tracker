#file_handler.py is the file that handles the file ingestion and processing.

import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import os
from datetime import datetime

class FileHandler:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def upload_video_performance_file(self, master):
        """
        Handle the uploading of one or more Excel files containing video performance data.
        Creates a database backup before processing and updates the UI upon completion.
        """
        try:
            file_paths = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xlsx")])
            if not file_paths:
                return

            # Create a backup before processing any files
            self.data_manager.backup_database()

            # Logic to be able to select multiple files and process them.
            skipped_files = []
            processed_files = []

            for file_path in file_paths:
                result = self.process_single_file(file_path)
                if result.startswith("Error") or result.startswith("Data for"):
                    skipped_files.append(result)
                else:
                    processed_files.append(result)

            # Prepare the result message
            result_message = "File processing complete.\n\n"
            if processed_files:
                result_message += "Processed files:\n" + "\n".join(processed_files) + "\n\n"
            if skipped_files:
                result_message += "Skipped files:\n" + "\n".join(skipped_files)

            messagebox.showinfo("Upload Result", result_message)

            return True

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}\n\nPlease check the log for more details."
            messagebox.showerror("Error", error_message)
            logging.error(f"Error in upload_file: {str(e)}", exc_info=True)
            return False

    def process_single_file(self, file_path):
        """
        Process a single Excel file to read, filter, and insert video performance data into the database.

        Args:
            file_path (str): The path to the Excel file to process.

        Returns:
            str: A message indicating the result of the processing.
        """
        try:
            df = self.data_manager.read_video_performance_excel(file_path)
            filtered_df = self.data_manager.filter_videos(df)
            
            # Check if data already exists for this date
            date = filtered_df['performance_date'].iloc[0]
            if self.data_manager.check_existing_data(date):
                response = messagebox.askyesno("Data Already Exists", 
                    f"Data for {date} already exists in the database. Do you want to replace it?")
                if response:
                    self.data_manager.replace_data_for_date(filtered_df, date)
                    messagebox.showinfo("Success", f"Data for {date} has been replaced successfully!")
                    return f"File for {date} processed successfully."
                else:
                    return f"Data for {date} already exists in the database. Skipped."        
            else:
                self.data_manager.insert_or_update_records(filtered_df)
                return f"File for {date} processed successfully."
        except ValueError as ve:
            return f"Error processing file {os.path.basename(file_path)}: {str(ve)}"
        except Exception as e:
            return f"Unexpected error processing file {os.path.basename(file_path)}: {str(e)}"

    def restore_database(self):
        """
        Restore the database from a selected backup file and update the UI accordingly.
        """
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Set the initial directory to the db_backup folder
        initial_dir = os.path.join(current_dir, 'db_backup')
        
        # Open file dialog
        backup_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Database Backup",
            filetypes=[("Database files", "*.db")]
        )
        
        if backup_path:
            result = self.data_manager.restore_database(backup_path)
            if result:
                messagebox.showinfo("Success", "Database restored successfully.")
                return True
            else:
                messagebox.showerror("Error", "Failed to restore database. Check the log for details.")
                return False