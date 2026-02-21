# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AIMU is a terminal-based music player (TUI) built with Python using Textual, python-vlc, and SQLite.

## Setup

**System requirement:** VLC Media Player must be installed (`brew install --cask vlc` on macOS).

```bash
python3 -m venv venv
source venv/bin/activate
pip install textual python-vlc mutagen
```

## Commands

```bash
# Run the application
python main.py

# Scan a directory and populate the database
python scan_mp3_to_db.py /path/to/music/directory

# Test core modules in isolation
python core/audio.py /path/to/song.mp3
python core/db.py
```

There is no test suite or linter configured.

## Architecture

The app separates three concerns: data persistence (`core/db.py`), audio playback (`core/audio.py`), and the TUI (`ui/`).

**Data flow:**
1. `scan_mp3_to_db.py` scans a directory and writes MP3 metadata to `music.db` (SQLite).
2. On startup, `MusicPlayerApp.on_mount()` loads all tracks from the DB into memory (`self.songs`), sorts them, and populates `TrackListView`.
3. User selects a track → `play_track()` calls `AudioEngine.play(file_path)` (VLC wrapper).
4. A 0.5s Textual interval timer calls `check_playback_status()`, which updates `PlayerControlBar` (progress + time) and auto-advances on song end.

**Key files:**
- `config.py` — `DB_PATH` and `DEFAULT_VOLUME`
- `core/db.py` — `MusicDatabase`: SQLite CRUD; schema has `path` as primary key plus metadata fields (`title`, `artist`, `album`, `bpm`, `rating`, etc.)
- `core/audio.py` — `AudioEngine`: thin VLC wrapper; `play()`, `toggle_pause()`, `stop()`, `get_info()` (returns progress/time/is_playing), `has_finished()`
- `ui/app.py` — `MusicPlayerApp`: main controller; owns `AudioEngine` and `MusicDatabase` instances; keybindings: Space (pause), N (next), Q (quit), Enter (play selected)
- `ui/playlist.py` — `TrackListView`: DataTable widget; row keys encode `{index}:{file_path}`
- `ui/status_bar.py` — `PlayerControlBar`: two-row widget (song name + time / progress bar); updated via `update_status()`
