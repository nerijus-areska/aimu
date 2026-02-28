from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label
from textual.containers import Vertical

from ui.feedback_modal import ImageSelector, HAPPY_IMAGES, AROUSED_IMAGES


class MoodModal(ModalScreen):
    """Session mood questionnaire: pleasure (1-5) + arousal (1-5)."""

    CSS = """
    MoodModal {
        align: center middle;
    }

    #mood_dialog {
        width: 70;
        height: auto;
        border: solid magenta;
        background: $surface;
        padding: 1 2;
    }

    #mood_title {
        text-align: center;
    }

    #mood_hint {
        height: 1;
        text-align: center;
    }

    ImageSelector {
        height: auto;
        border: solid $panel;
        padding: 0 1;
    }

    ImageSelector:focus {
        border: solid magenta;
    }

    ImageSelector > Label {
        height: 1;
    }

    .img-row {
        height: auto;
    }

    .img-cell {
        width: 11;
        height: 5;
        border: solid transparent;
        padding: 0;
        margin: 0;
    }

    .img-cell.selected {
        border: solid yellow;
    }

    Image {
        background: transparent;
    }
    """

    BINDINGS = [
        ("s",      "save",   "Save"),
        ("ctrl+s", "save",   "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, pleasure: int = 3, arousal: int = 3) -> None:
        super().__init__()
        self._pleasure_idx = max(1, min(5, pleasure)) - 1
        self._arousal_idx  = max(1, min(5, arousal))  - 1

    def compose(self) -> ComposeResult:
        with Vertical(id="mood_dialog"):
            yield Label(
                "[bold magenta]◈  S T A T I O N  M O O D  ◈[/bold magenta]",
                id="mood_title",
            )
            yield ImageSelector("MOOD",   HAPPY_IMAGES,   self._pleasure_idx, id="sel_mood")
            yield ImageSelector("ENERGY", AROUSED_IMAGES, self._arousal_idx,  id="sel_arousal")
            yield Label(
                "[dim]← →[/dim]  change    [dim]tab[/dim]  next section"
                "    [dim]ctrl+s[/dim]  save    [dim]esc[/dim]  cancel",
                id="mood_hint",
            )

    def on_mount(self) -> None:
        self.query_one("#sel_mood").focus()

    def action_save(self) -> None:
        self.dismiss({
            "mood_pleasure": self.query_one("#sel_mood",    ImageSelector).value,
            "mood_arousal":  self.query_one("#sel_arousal", ImageSelector).value,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)
