from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, ProgressBar


class PlayerControlBar(Container):
    """
    The bottom bar showing current song info, time, and progress.
    """

    def compose(self) -> ComposeResult:
        # Top row: Song Name and Time
        with Horizontal(classes="info_row"):
            yield Label("Ready.", id="status_text")
            yield Label("--:-- / --:--", id="time_text")

        # Bottom row: The graphical bar
        # ADDED: show_percentage=False
        yield ProgressBar(
            total=100, show_eta=False, show_percentage=False, id="progress_bar"
        )

    def update_status(
        self, song_name: str, progress: float, current_ms: int, total_ms: int
    ):
        """
        Updates the UI with name, bar position, and timestamps.
        """
        text_widget = self.query_one("#status_text", Label)
        time_widget = self.query_one("#time_text", Label)
        bar_widget = self.query_one("#progress_bar", ProgressBar)

        # 1. Update Song Name
        if song_name:
            text_widget.update(f"Now Playing: {song_name}")

        # 2. Update Progress Bar (0-100)
        # Check for None just in case VLC returns odd data
        safe_progress = progress if progress is not None else 0
        bar_widget.progress = safe_progress * 100

        # 3. Update Time Text (0:00 / 3:45)
        current_str = self._format_time(current_ms)
        total_str = self._format_time(total_ms)
        time_widget.update(f"{current_str} / {total_str}")

    def _format_time(self, milliseconds: int) -> str:
        """Helper: Converts ms (e.g., 65000) to string (e.g., '1:05')."""
        if milliseconds is None or milliseconds < 0:
            return "0:00"

        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        rem_seconds = seconds % 60
        return f"{minutes}:{rem_seconds:02}"
