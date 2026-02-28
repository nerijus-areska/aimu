from pathlib import Path

from PIL import Image as PILImage
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label
from textual.containers import Vertical, Horizontal
from textual.widget import Widget
from textual_image.widget import Image as TuiImage

ASSETS = Path(__file__).parent.parent / "assets"
# Textual default dark-theme $surface ≈ #1e1e1e
_BG = (30, 30, 30)


def _load(name: str) -> PILImage.Image | None:
    p = ASSETS / name
    if not p.exists():
        return None
    img = PILImage.open(p).convert("RGBA")
    bg = PILImage.new("RGBA", img.size, (*_BG, 255))
    return PILImage.alpha_composite(bg, img).convert("RGB")


HAPPY_IMAGES   = [_load(f"happy_{i}.png")   for i in range(1, 6)]
AROUSED_IMAGES = [_load(f"aroused_{i}.png") for i in range(1, 6)]
RATING_IMAGES  = [_load(f"rating_{i}.png") for i in range(1, 4)]


class ImageSelector(Widget):
    """A focusable row showing all images side-by-side; ← / → moves the highlight."""

    can_focus = True

    BINDINGS = [
        ("left",  "prev", "Previous"),
        ("right", "next", "Next"),
    ]

    def __init__(self, label: str, images: list, initial: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._label  = label
        self._images = [img for img in images if img is not None]
        self._index  = max(0, min(initial, len(self._images) - 1))

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self._label}[/bold]")
        with Horizontal(classes="img-row"):
            for i, img in enumerate(self._images):
                cls = "img-cell selected" if i == self._index else "img-cell"
                with Vertical(classes=cls):
                    yield TuiImage(img)

    def _set_selected(self, index: int) -> None:
        items = list(self.query(".img-cell"))
        items[self._index].remove_class("selected")
        self._index = index
        items[self._index].add_class("selected")

    def action_prev(self) -> None:
        self._set_selected((self._index - 1) % len(self._images))

    def action_next(self) -> None:
        self._set_selected((self._index + 1) % len(self._images))

    @property
    def value(self) -> int:
        """Return the selected level as a 1-based integer."""
        return self._index + 1


class FeedbackModal(ModalScreen):
    """Visual questionnaire: mood (1-5), energy (1-5), rating (1-3)."""

    CSS = """
    FeedbackModal {
        align: center middle;
    }

    #feedback_dialog {
        width: 70;
        height: auto;
        border: solid green;
        background: $surface;
        padding: 1 2;
    }

    #feedback_title {
        text-align: center;
    }

    ImageSelector {
        height: auto;
        border: solid $panel;
        padding: 0 1;
    }

    ImageSelector:focus {
        border: solid green;
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

    #feedback_hint {
        height: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        ("s",      "save",   "Save"),
        ("ctrl+s", "save",   "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        track_name: str,
        pleasure: int = 3,
        arousal:  int = 3,
        rating:   int = 2,
        focus_rating: bool = False,
    ) -> None:
        super().__init__()
        self.track_name    = track_name
        self._pleasure_idx = max(1, min(5, pleasure)) - 1
        self._arousal_idx  = max(1, min(5, arousal))  - 1
        self._rating_idx   = max(1, min(3, rating))   - 1
        self._focus_rating = focus_rating

    def compose(self) -> ComposeResult:
        with Vertical(id="feedback_dialog"):
            yield Label(
                f"[bold green]Feedback[/bold green]  [dim]{self.track_name}[/dim]",
                id="feedback_title",
            )
            yield ImageSelector("MOOD",   HAPPY_IMAGES,   self._pleasure_idx, id="sel_mood")
            yield ImageSelector("ENERGY", AROUSED_IMAGES, self._arousal_idx,  id="sel_arousal")
            yield ImageSelector("RATING", RATING_IMAGES,  self._rating_idx,   id="sel_rating")
            yield Label(
                "[dim]← →[/dim]  change    [dim]tab[/dim]  next section"
                "    [dim]ctrl+s[/dim]  save    [dim]esc[/dim]  cancel",
                id="feedback_hint",
            )

    def on_mount(self) -> None:
        if self._focus_rating:
            self.query_one("#sel_rating").focus()
        else:
            self.query_one("#sel_mood").focus()

    def action_save(self) -> None:
        self.dismiss({
            "mood_pleasure": self.query_one("#sel_mood",    ImageSelector).value,
            "mood_arousal":  self.query_one("#sel_arousal", ImageSelector).value,
            "rating":        self.query_one("#sel_rating",  ImageSelector).value,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)
