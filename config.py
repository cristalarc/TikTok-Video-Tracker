import os

# Define the project root directory
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Define the data directory
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Define the settings file path
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')

# Define the database file path
DATABASE_FILE = os.path.join(DATA_DIR, 'tiktok_tracker.db')

# Define the database backup directory
DB_BACKUP_DIR = os.path.join(DATA_DIR, 'db_backup')

# Ensure the backup directory exists
os.makedirs(DB_BACKUP_DIR, exist_ok=True)