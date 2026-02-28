import math
import random
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Container, Horizontal

from core.audio import AudioEngine
from core.db import MusicDatabase
from core.keybindings import load_bindings
from config import DEFAULT_VOLUME, DB_PATH, KEYBINDINGS_PATH
from ui.playlist import TrackListView
from ui.status_bar import PlayerControlBar
from ui.track_info import TrackInfoPanel
from ui.station_view import StationView
from ui.feedback_modal import FeedbackModal
from ui.mood_modal import MoodModal
from ui.help_modal import HelpModal
from pathlib import Path

_BINDINGS = load_bindings(KEYBINDINGS_PATH)


class MusicPlayerApp(App):
    """The Main Controller."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_content {
        height: 1fr;
        layout: horizontal;
    }

    #left_panel {
        width: 1fr;
        height: 100%;
    }

    TrackListView {
        width: 100%;
        height: 100%;
        border: solid green;
    }

    StationView {
        width: 100%;
        height: 100%;
        border: solid magenta;
        display: none;
        layout: vertical;
        padding: 1 1;
    }

    #station_title {
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }

    ParticleField {
        height: 1fr;
    }

    #station_message {
        text-align: center;
        height: 1;
        margin-top: 1;
    }

    WaveformWidget {
        height: 2;
        display: none;
    }

    TrackInfoPanel {
        width: 1fr;
        height: 100%;
        border: solid green;
        padding: 1 2;
    }

    #info_station_row {
        height: auto;
        width: 100%;
    }

    #info_station_mood {
        width: 1fr;
    }

    #info_station_rating {
        width: 1fr;
    }

    PlayerControlBar {
        height: auto;
        dock: bottom;
        border-top: solid green;
        padding: 0 0;
    }

    .info_row {
        height: 1;
        width: 100%;
        padding: 0 2;
        margin-bottom: 1;
    }

    #info_volume {
        dock: right;
        width: 12;
        height: 100%;
        content-align: center middle;
    }

    #status_text {
        width: 1fr;
    }

    #time_text {
        width: auto;
        color: yellow;
    }

    ProgressBar {
        height: 2;
        margin: 0 0;
        padding: 0 0;
        width: 100%;
        background: $surface-lighten-1;
    }

    ProgressBar > Bar {
        width: 1fr;
        height: 100%;
    }
    """

    BINDINGS = _BINDINGS

    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug_mode = debug
        self.audio = AudioEngine()
        self.db = MusicDatabase(db_path=DB_PATH)
        self.songs = []
        self.current_index = -1
        self.highlighted_index = -1
        self.station_mode = False
        self.station_pleasure: int = 3
        self.station_arousal: int = 3
        self.volume_level: int = DEFAULT_VOLUME // 10
        self.audio.set_volume(DEFAULT_VOLUME)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_content"):
            with Container(id="left_panel"):
                yield TrackListView(id="playlist")
                yield StationView(id="station_view")
            yield TrackInfoPanel(id="track_info")
        yield PlayerControlBar(id="status_bar")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "AIMU"

        try:
            db_files = self.db.get_all_files()
        except Exception as e:
            self.notify(f"Error loading database: {e}", severity="error")
            db_files = []

        self.songs = []
        for file_entry in db_files:
            try:
                artist = file_entry.get("artist") if file_entry.get("artist") else "Unknown Artist"
                title = file_entry.get("title") if file_entry.get("title") else Path(file_entry["path"]).stem
                display_name = f"{artist} - {title}"

                self.songs.append({
                    "name": display_name,
                    "path": file_entry["path"],
                    "rating": file_entry.get("rating", 1),
                    "duration": file_entry.get("duration"),
                    "bitrate": file_entry.get("bitrate"),
                    "album": file_entry.get("album"),
                    "bpm": file_entry.get("bpm"),
                    "title": file_entry.get("title"),
                    "artist": file_entry.get("artist"),
                    "albumartist": file_entry.get("albumartist"),
                    "tracknumber": file_entry.get("tracknumber"),
                    "genre": file_entry.get("genre"),
                    "date": file_entry.get("date"),
                    "feedback": file_entry.get("feedback"),
                    "mood_pleasure": file_entry.get("mood_pleasure"),
                    "mood_arousal": file_entry.get("mood_arousal"),
                })
            except Exception:
                continue

        self.songs.sort(key=lambda x: (x.get("artist") or "", x.get("title") or ""))

        playlist = self.query_one(TrackListView)
        playlist.load_tracks(self.songs)
        playlist.focus()

        if not self.songs:
            self.notify("No tracks found in database. Run scan_mp3_to_db.py first.", severity="warning")

        self.set_interval(0.5, self.check_playback_status)
        self.query_one(TrackInfoPanel).update_volume(self.volume_level)

    # ── Help overlay ──────────────────────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(HelpModal(load_bindings(KEYBINDINGS_PATH), KEYBINDINGS_PATH))

    # ── Station mode ──────────────────────────────────────────────────────────

    def action_toggle_station(self) -> None:
        if not self.songs:
            return
        self.station_mode = not self.station_mode

        playlist = self.query_one(TrackListView)
        station = self.query_one(StationView)
        playlist.display = not self.station_mode
        station.display = self.station_mode

        if self.station_mode:
            def on_mood(result: dict | None) -> None:
                if result is not None:
                    self.station_pleasure = result["mood_pleasure"]
                    self.station_arousal  = result["mood_arousal"]
                self.play_track(self._pick_station_song())

            self.push_screen(
                MoodModal(self.station_pleasure, self.station_arousal),
                on_mood,
            )
        else:
            # Sync playlist cursor back to the currently playing song
            if 0 <= self.current_index < len(self.songs):
                playlist.cursor_coordinate = (self.current_index, 0)
            playlist.focus()
            self._update_info_panel()

    def _song_station_score(self, feedback_history: list) -> float | None:
        """Return the mood-proximity raw score for a single song, or None if no valid feedback."""
        RATING_MAP = {1: -1, 2: 1, 3: 4}
        px, py = self.station_pleasure, self.station_arousal
        best_score: float | None = None
        best_dist: float = float("inf")
        for entry in feedback_history:
            ep = entry.get("mood_pleasure")
            ea = entry.get("mood_arousal")
            er = entry.get("rating")
            if ep is None or ea is None or er is None:
                continue
            raw = RATING_MAP.get(int(er))
            if raw is None:
                continue
            dist = math.sqrt((ep - px) ** 2 + (ea - py) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_score = raw / (1.0 + dist)
        return best_score

    def _pick_station_song(self) -> int:
        """Return a random song index weighted by mood-proximity and feedback rating."""
        RATING_MAP = {1: -1, 2: 1, 3: 4}
        px, py = self.station_pleasure, self.station_arousal

        raw_scores: list[float] = []
        for song in self.songs:
            history = self.db.get_feedback_history(song["path"])
            best_score: float | None = None
            best_dist: float = float("inf")
            for entry in history:
                ep = entry.get("mood_pleasure")
                ea = entry.get("mood_arousal")
                er = entry.get("rating")
                if ep is None or ea is None or er is None:
                    continue
                raw = RATING_MAP.get(int(er))
                if raw is None:
                    continue
                dist = math.sqrt((ep - px) ** 2 + (ea - py) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_score = raw / (1.0 + dist)
            raw_scores.append(best_score if best_score is not None else 0.0)

        # Fixed mapping anchored at 0 → 3 (neutral/no-feedback).
        # Theoretical raw range: [-1, 4] from RATING_MAP + distance scaling.
        normalised = [
            (3.0 + 2.0 * s / 4.0) if s >= 0.0 else (3.0 + 2.0 * s)
            for s in raw_scores
        ]

        weights = [2.0 ** (n - 1.0) - 1.0 for n in normalised]

        if self.debug_mode:
            with open("debug.log", "a") as f:
                f.write(f"\n--- station pick  mood={px}  arousal={py} ---\n")
                for song, norm in zip(self.songs, normalised):
                    f.write(f"  {norm:.2f}  {song['name']}\n")

        return random.choices(range(len(self.songs)), weights=weights, k=1)[0]

    # ── Playback ──────────────────────────────────────────────────────────────

    def on_data_table_row_highlighted(self, message: TrackListView.RowHighlighted) -> None:
        if message.data_table.id != "playlist":
            return
        row_key = message.row_key.value
        if not row_key:
            return
        index_str, _ = row_key.split("|", 1)
        self.highlighted_index = int(index_str)
        self._update_info_panel()

    def on_data_table_row_selected(self, message: TrackListView.RowSelected) -> None:
        if message.data_table.id != "playlist":
            return
        row_key = message.row_key.value
        if not row_key:
            return
        index_str, _ = row_key.split("|", 1)
        self.play_track(int(index_str))

    def play_track(self, index: int) -> None:
        if 0 <= index < len(self.songs):
            self.current_index = index
            # In station mode keep the info panel in sync with what's playing
            if self.station_mode:
                self.highlighted_index = index
            song = self.songs[index]

            self.audio.play(song["path"])

            playlist = self.query_one(TrackListView)
            playlist.cursor_coordinate = (index, 0)

            bar = self.query_one(PlayerControlBar)
            bar.update_status(song["name"], 0.0, 0, 0)

            self._update_info_panel()

    def _update_info_panel(self) -> None:
        panel = self.query_one(TrackInfoPanel)
        if self.highlighted_index < 0 or self.highlighted_index >= len(self.songs):
            panel.set_track(None)
            panel.set_station_mood(None, None)
            return
        song = self.songs[self.highlighted_index]
        is_playing = self.highlighted_index == self.current_index
        feedback_history = self.db.get_feedback_history(song["path"])
        panel.set_track(song, is_playing=is_playing, feedback_history=feedback_history)
        if self.station_mode:
            station_score = self._song_station_score(feedback_history)
            panel.set_station_mood(self.station_pleasure, self.station_arousal, station_score)
        else:
            panel.set_station_mood(None, None)

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_feedback(self) -> None:
        if self.highlighted_index < 0 or self.highlighted_index >= len(self.songs):
            return
        song = self.songs[self.highlighted_index]

        if self.station_mode:
            # Preselect session mood; land focus on rating
            pleasure = self.station_pleasure
            arousal  = self.station_arousal
        else:
            pleasure = int(song.get("mood_pleasure") or 3)
            arousal  = int(song.get("mood_arousal")  or 3)

        rating = max(1, min(3, int(song.get("rating") or 2)))

        def on_result(result: dict | None) -> None:
            if result is None:
                return
            song["mood_pleasure"] = result["mood_pleasure"]
            song["mood_arousal"]  = result["mood_arousal"]
            song["rating"]        = result["rating"]
            self.db.add_feedback(
                song["path"],
                result["mood_pleasure"],
                result["mood_arousal"],
                result["rating"],
            )
            self._update_info_panel()

        self.push_screen(
            FeedbackModal(
                track_name=song["name"],
                pleasure=pleasure,
                arousal=arousal,
                rating=rating,
                focus_rating=self.station_mode,
            ),
            on_result,
        )

    def action_volume_up(self) -> None:
        if self.volume_level < 10:
            self.volume_level += 1
            self.audio.set_volume(self.volume_level * 10)
            self.query_one(TrackInfoPanel).update_volume(self.volume_level)

    def action_volume_down(self) -> None:
        if self.volume_level > 1:
            self.volume_level -= 1
            self.audio.set_volume(self.volume_level * 10)
            self.query_one(TrackInfoPanel).update_volume(self.volume_level)

    def action_seek_backward(self):
        self.audio.seek_relative(-10)

    def action_seek_forward(self):
        self.audio.seek_relative(10)

    def action_toggle_pause(self):
        self.audio.toggle_pause()

    def action_next_song(self):
        if self.station_mode:
            self.play_track(self._pick_station_song())
        else:
            next_idx = self.current_index + 1
            if next_idx < len(self.songs):
                self.play_track(next_idx)

    def check_playback_status(self):
        info = self.audio.get_info()

        current_song_name = ""
        if self.current_index >= 0:
            current_song_name = self.songs[self.current_index]["name"]

        bar = self.query_one(PlayerControlBar)
        bar.update_status(
            song_name=current_song_name,
            progress=info["progress"],
            current_ms=info["current_ms"],
            total_ms=info["total_ms"],
        )

        if self.audio.has_finished() and self.current_index != -1:
            self.action_next_song()

    def on_unmount(self) -> None:
        if hasattr(self, 'db'):
            self.db.close()
