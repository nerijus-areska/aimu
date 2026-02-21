from pathlib import Path

# --- CONFIGURATION ---

# Path to the SQLite database file (resolved relative to this config file)
DB_PATH = str(Path(__file__).parent / "music.db")

# Path to the keybindings override file
KEYBINDINGS_PATH = str(Path(__file__).parent / "keybindings.json")

# Optional: Set the initial volume (0 to 100)
DEFAULT_VOLUME = 80
