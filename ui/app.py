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

    def __init__(self):
        super().__init__()
        self.audio = AudioEngine()
        self.db = MusicDatabase(db_path=DB_PATH)
        self.songs = []
        self.current_index = -1
        self.highlighted_index = -1
        self.station_mode = False
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
            self.play_track(self._pick_station_song())
        else:
            # Sync playlist cursor back to the currently playing song
            if 0 <= self.current_index < len(self.songs):
                playlist.cursor_coordinate = (self.current_index, 0)
            playlist.focus()

    def _pick_station_song(self) -> int:
        """Return a random song index weighted by 2^(rating-1)."""
        weights = [2 ** max(0, (song.get("rating") or 1) - 1) for song in self.songs]
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
            return
        song = self.songs[self.highlighted_index]
        is_playing = self.highlighted_index == self.current_index
        panel.set_track(song, is_playing=is_playing)

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_rating_up(self):
        self._adjust_rating(1)

    def action_rating_down(self):
        self._adjust_rating(-1)

    def _adjust_rating(self, delta: int) -> None:
        if self.highlighted_index < 0 or self.highlighted_index >= len(self.songs):
            return
        song = self.songs[self.highlighted_index]
        new_rating = max(0, min(5, (song.get("rating") or 0) + delta))
        song["rating"] = new_rating
        self.db.update_rating(song["path"], new_rating)
        self._update_info_panel()

    def action_feedback(self) -> None:
        if self.highlighted_index < 0 or self.highlighted_index >= len(self.songs):
            return
        song = self.songs[self.highlighted_index]

        def on_result(text: str | None) -> None:
            if text is None:
                return
            song["feedback"] = text
            self.db.update_feedback(song["path"], text)
            self._update_info_panel()

        self.push_screen(
            FeedbackModal(track_name=song["name"], existing=song.get("feedback") or ""),
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
