# AIMU

A terminal-based music player (TUI) for your MP3 library, built with [Textual](https://github.com/Textualize/textual).

Features a track browser, playback controls, a star rating system, per-track notes, and an ambient "station" mode.

## Requirements

- Python 3.10+
- [VLC Media Player](https://www.videolan.org/vlc/) (must be installed as a system application)

```bash
# macOS
brew install --cask vlc
```

## Installation

```bash
git clone https://github.com/nerijus-areska/aimu.git
cd aimu

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

### 1. Scan your music library

Point the scanner at a directory containing MP3 files. It will recursively find all tracks and store their metadata in a local SQLite database (`music.db`).

```bash
python scan_mp3_to_db.py /path/to/your/music
```

Options:

| Flag | Description |
|------|-------------|
| `--db-path PATH` | Use a custom database file location |
| `--rating N` | Set a default star rating (0–5) for newly added tracks |
| `--no-metadata` | Skip reading ID3 tags (faster scan) |

### 2. Launch the player

```bash
python main.py
```

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Play selected track |
| `Space` | Pause / Resume |
| `N` | Skip to next track |
| `←` / `→` | Seek backward / forward 10 seconds |
| `[` / `]` | Decrease / Increase rating |
| `F` | Open feedback / notes for current track |
| `S` | Toggle station mode (ambient auto-play) |
| `Q` | Quit |

## Project Structure

```
aimu/
├── main.py               # Entry point
├── config.py             # DB path and default volume
├── scan_mp3_to_db.py     # CLI tool to import music metadata
├── requirements.txt
├── core/
│   ├── audio.py          # VLC playback engine
│   └── db.py             # SQLite database interface
└── ui/
    ├── app.py            # Main Textual app and controller
    ├── playlist.py       # Track list widget
    ├── status_bar.py     # Progress bar and time display
    ├── track_info.py     # Metadata and rating panel
    ├── station_view.py   # Ambient station mode view
    ├── feedback_modal.py # Per-track notes dialog
    ├── waveform.py       # Animated waveform decoration
    └── particles.py      # Ambient particle field animation
```

## License

MIT
