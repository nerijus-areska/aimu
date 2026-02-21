from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, TextArea
from textual.containers import Vertical


class FeedbackModal(ModalScreen):
    """Modal overlay for entering/editing feedback on a track."""

    CSS = """
    FeedbackModal {
        align: center middle;
    }

    #feedback_dialog {
        width: 64;
        height: 18;
        border: solid green;
        background: $surface;
        padding: 1 2;
    }

    #feedback_title {
        margin-bottom: 1;
        text-align: center;
    }

    TextArea {
        height: 10;
        border: solid $panel-lighten-2;
        margin-bottom: 1;
    }

    #feedback_hint {
        text-align: center;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, track_name: str, existing: str = "") -> None:
        super().__init__()
        self.track_name = track_name
        self.existing = existing

    def compose(self) -> ComposeResult:
        with Vertical(id="feedback_dialog"):
            yield Label(
                f"[bold green]Feedback[/bold green]  [dim]{self.track_name}[/dim]",
                id="feedback_title",
            )
            yield TextArea(self.existing, id="feedback_input")
            yield Label(
                "[dim]ctrl+s[/dim]  save      [dim]esc[/dim]  cancel",
                id="feedback_hint",
            )

    def on_mount(self) -> None:
        ta = self.query_one(TextArea)
        ta.focus()
        # Move cursor to end of any existing text
        if self.existing:
            ta.move_cursor_relative(rows=len(self.existing.splitlines()))

    def action_save(self) -> None:
        text = self.query_one(TextArea).text.strip()
        self.dismiss(text)

    def action_cancel(self) -> None:
        self.dismiss(None)
