# TikTok Tracker

## Overview

TikTok Tracker is a Python-based application designed to help track and analyze the performance of TikTok videos over time. It provides a user-friendly interface for data ingestion, visualization, and analysis of TikTok video metrics.

## Features

- **Data Ingestion**: Import daily TikTok performance data from Excel (.xlsx) files.
- **Video Tracking**: Automatically track videos that reach 4000+ views and continue monitoring regardless of future view counts.
- **Database Management**: Store and manage video performance data over time.
- **Search Functionality**: Easily search for specific videos within the database.
- **Data Visualization**: Plot performance metrics for individual videos over time.
- **Dual Metric Plotting**: Compare two different metrics on the same graph.
- **Data Aggregation**: View aggregated data (daily, weekly, monthly) for comprehensive analysis.
- **Settings Management**: Customize application settings, including view threshold for video ingestion.
- **Database Backup and Restore**: Ensure data integrity with backup and restore capabilities.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/cristalarc/tiktok-tracker.git
   cd tiktok-tracker
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```
   python main.py
   ```

2. Use the GUI to perform various operations:
   - Upload TikTok performance data files
   - Search for videos
   - View video details
   - Plot performance metrics
   - Manage application settings

## File Structure
#TODO: Update the file structure. IGNORE.
your_project/
│
├── gui/
│ ├── init.py
│ ├── home_view.py
│ ├── trending_page.py
│ ├── settings_window.py
│ └── main_gui.py
│
├── data_manager/
│ ├── init.py
│ └── data_manager.py
│
├── plotter/
│ ├── init.py
│ └── plotter.py
│
├── file_handler.py
├── main.py
├── requirements.txt
└── README.md


## Key Components

1. **GUI (gui/main_gui.py)**: Manages the main application interface.
2. **Data Manager (data_manager/data_manager.py)**: Handles data processing and database operations.
3. **Plotter (plotter/plotter.py)**: Responsible for creating performance plots.
4. **File Handler (file_handler.py)**: Manages file operations and data ingestion.

## Features in Detail

### Data Ingestion
- Upload daily TikTok performance Excel files.
- Automatically filter and track videos with 4000+ views.
- Handle multiple file uploads with error reporting.

### Video Database
- Store comprehensive video details and daily performance metrics.
- Search functionality for quick video lookup.
- Display aggregated video data in the main interface.

### Performance Plotting
- Plot individual metrics over time for selected videos.
- Dual metric plotting for performance comparison.
- Support for different time aggregations (daily, weekly, monthly).

### Settings
- Configurable view threshold for video ingestion.
- Customizable application settings through a dedicated settings window.

### Data Management
- Database backup and restore functionality.
- Clear performance data for specific dates.

## Contributing

Contributions to the TikTok Tracker project are welcome. Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## Acknowledgments

- TikTok for rocking at building a great platform and sucking at helping display the data.
- The Python community for the excellent libraries used in this project.

## License

This project is licensed under a non-commercial use license. See the [LICENSE] file for details.

**For commercial use, please contact talaverajuancarlos1311@gmail.com.**
