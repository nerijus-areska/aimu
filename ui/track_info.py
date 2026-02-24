from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label
from ui.waveform import WaveformWidget


def _squares(value: int, total: int, color: str) -> str:
    """Render spaced filled/empty squares, e.g. '■ ■ □ □ □'."""
    parts = [f"[{color}]■[/{color}]"] * value + ["[dim]□[/dim]"] * (total - value)
    return " ".join(parts)


class TrackInfoPanel(Container):
    """Right panel showing metadata for the currently highlighted track."""

    def compose(self) -> ComposeResult:
        yield Label("", id="info_now_playing")
        yield WaveformWidget(id="waveform")
        yield Label("", id="info_title")
        yield Label("", id="info_artist")
        yield Label("", id="info_sep")
        yield Label("", id="info_album")
        yield Label("", id="info_genre")
        yield Label("", id="info_date")
        yield Label("", id="info_bpm")
        yield Label("", id="info_volume")
        yield Label("", id="info_feedback_sep")
        yield Label("", id="info_feedback")

    def _volume_bar(self, level: int) -> str:
        lines = ["[dim]VOLUME[/dim]"]
        for i in range(10, 0, -1):
            block = "[green]█[/green]" if i <= level else "[dim]░[/dim]"
            marker = " [bold green]◄[/bold green]" if i == level else ""
            lines.append(f"  {block} {i:2d}{marker}")
        return "\n".join(lines)

    def update_volume(self, level: int) -> None:
        self.query_one("#info_volume", Label).update(self._volume_bar(level))

    def set_track(
        self,
        song: dict | None,
        is_playing: bool = False,
        feedback_history: list[dict] | None = None,
    ) -> None:
        """Update the panel to show metadata for the given song."""
        all_ids = [
            "#info_now_playing", "#info_title", "#info_artist", "#info_sep",
            "#info_album", "#info_genre", "#info_date", "#info_bpm",
            "#info_feedback_sep", "#info_feedback",
        ]

        if song is None:
            for wid in all_ids:
                self.query_one(wid, Label).update("")
            self.query_one(WaveformWidget).display = False
            return

        # Now playing indicator
        self.query_one("#info_now_playing", Label).update(
            "[bold green reverse] ▶  NOW PLAYING [/bold green reverse]" if is_playing else ""
        )
        self.query_one(WaveformWidget).display = is_playing

        # Title — big and loud
        title = song.get("title") or ""
        self.query_one("#info_title", Label).update(
            f"\n[bold bright_yellow]{title.upper()}[/bold bright_yellow]" if title else ""
        )

        # Artist — softer, indented feel
        artist = song.get("artist") or ""
        self.query_one("#info_artist", Label).update(
            f"[italic cyan]  {artist}[/italic cyan]" if artist else ""
        )

        # Separator
        self.query_one("#info_sep", Label).update(
            "\n[dim]  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·[/dim]\n" if (title or artist) else ""
        )

        # Metadata rows — each field gets its own color
        def row(color: str, icon: str, label: str, val) -> str:
            if val is None or val == "":
                return ""
            return f"  [bold {color}]{icon} {label:<7}[/bold {color}]  {val}"

        self.query_one("#info_album", Label).update(row("magenta",     "◆", "ALBUM",  song.get("album")))
        self.query_one("#info_genre", Label).update(row("blue",        "◆", "GENRE",  song.get("genre")))
        self.query_one("#info_date",  Label).update(row("yellow",      "◆", "YEAR",   song.get("date")))
        self.query_one("#info_bpm",   Label).update(row("green",       "◆", "BPM",    song.get("bpm")))

        # Feedback history
        entries = feedback_history or []
        if entries:
            lines = [
                "\n[dim]  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·[/dim]",
                "",
                "  [bold cyan]◆ FEEDBACK[/bold cyan]",
            ]
            for i, entry in enumerate(entries):
                mood = _squares(int(entry.get("mood_pleasure") or 0), 5, "magenta")
                energy = _squares(int(entry.get("mood_arousal") or 0), 5, "yellow")
                rating = _squares(int(entry.get("rating") or 0), 3, "green")
                lines.append("")
                lines.append(f"  [dim]MOOD  [/dim]  {mood}")
                lines.append(f"  [dim]ENERGY[/dim]  {energy}")
                lines.append(f"  [dim]RATING[/dim]  {rating}")
                if i < len(entries) - 1:
                    lines.append("  [dim]─ ─ ─ ─ ─ ─ ─ ─[/dim]")

            self.query_one("#info_feedback_sep", Label).update("")
            self.query_one("#info_feedback", Label).update("\n".join(lines))
        else:
            self.query_one("#info_feedback_sep", Label).update("")
            self.query_one("#info_feedback", Label).update("")
