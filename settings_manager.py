#settings_manager.py is the file that handles the settings saving and loading.
# No logging needed for this file.

class SettingsManager:
    def __init__(self, data_manager):
        """
        Initialize the SettingsManager for saving settings.

        Args:
            data_manager (DataManager): An instance of DataManager for accessing and updating settings.
        """
        self.data_manager = data_manager

    def save_settings_to_storage(self, vv_threshold, week_start):
        """
        Save the user's settings to the DataManager.

        Args:
            vv_threshold (int): The video view ingestion threshold.
            week_start (str): The day the week starts on ('Sunday' or 'Monday').
        """
        self.data_manager.set_vv_threshold(vv_threshold)
        self.data_manager.set_week_start(week_start)