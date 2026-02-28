# AIMU — Music Player

A terminal-based music player built around mood. Browse your MP3 library, give feedback tied to how you feel right now, and let Station Mode use that context to pick tracks that fit your current state.

Built with [Textual](https://github.com/Textualize/textual), [python-vlc](https://github.com/oaubert/python-vlc), and SQLite.

![Giving feedback](screenshots/giving_feedback.png)

## Core Feature: Mood Feedback

Every time you listen to a track, you can rate it in the context of how YOU feel at that moment:

- **Mood** (1–5) — how happy / pleasant do YOU feel right now
- **Energy** (1–5) — how energetic / arousing do YOU feel right now
- **Rating** (1–3) — your overall preference for this track in this context

Feedback is stored as an append-only log — every submission is a new record, so your history of impressions over time is preserved. The info panel shows all past feedback entries for the selected track as visual square indicators, displayed side by side.

![Track with feedback history](screenshots/track_with_2_feedbacks.png)

The key insight: the same track can feel different depending on your current mood. Capturing both together builds a richer picture than a static rating ever could.

## Station Mode

Station Mode is an ambient auto-play mode. When you enter it, you set your current **Mood** and **Energy** state. The player then uses your feedback history to pick tracks that were rated well *in a similar mood context*, and avoids tracks that were rated poorly in that context.

![Station mode](screenshots/station_view.png)

### How track selection works

1. For each song, the closest past feedback entry to your current station mood is found using Euclidean distance on the mood/energy axes.
2. That entry's rating is mapped to a score: poor (−1), ok (+1), great (+4).
3. The score is scaled by proximity: an exact mood match carries full weight; a distant match is discounted.
4. Songs with no feedback get a neutral score and participate in uniform random selection.
5. Scores are mapped to a 1–5 scale (anchored at 0 → 3), then converted to exponential weights for random selection — ensuring well-matched tracks are strongly preferred and poorly-matched tracks are effectively excluded.

The info panel shows each song's **Rating for Station** (1–5 squares) so you can see how the current track scores against your station mood.

## Requirements

- Python 3.10+
- [VLC Media Player](https://www.videolan.org/vlc/)

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

```bash
python scan_mp3_to_db.py /path/to/your/music
```

This recursively finds all MP3 files and stores their metadata in a local SQLite database (`music.db`).

| Flag | Description |
|------|-------------|
| `--db-path PATH` | Custom database file location |
| `--rating N` | Default rating (0–5) for new tracks |
| `--no-metadata` | Skip reading ID3 tags |

### 2. Launch the player

```bash
python main.py
```

Add `--debug` to log station selection scores to `debug.log`.

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Play selected track |
| `Space` | Pause / Resume |
| `N` | Next track |
| `W` / `S` | Volume up / down |
| `Left` / `Right` | Seek -/+ 10 seconds |
| `F` | Open feedback modal |
| `X` | Toggle station mode |
| `H` | Help overlay |
| `Q` | Quit |

Keybindings are customizable via `keybindings.json`.

## License

MIT
