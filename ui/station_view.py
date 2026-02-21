import random
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label

from ui.particles import ParticleField


QUIRKY_MESSAGES = [
    "Moving around quantum matter to establish connection to the next song",
    "Consulting the ancient vinyl oracle for harmonic guidance",
    "Negotiating with sound waves across 11 dimensions",
    "Reverse engineering your soul's resonant frequency signature",
    "Harvesting emotional residue from parallel universes",
    "Recalibrating the hypersonic taste matrix, please stand by",
    "Communing with the ghost of frequencies past",
    "Compressing infinity into three and a half minutes",
    "Convincing electrons to do something musically interesting",
    "Translating butterfly wing patterns into audio waveforms",
    "Synchronizing your heartbeat with the universe's bassline",
    "Searching for the perfect song in the space between atoms",
    "Assembling sonic particles from the quantum foam",
    "Persuading reluctant sound waves to enter your cochlea",
    "Cross-referencing your vibe with 47 interdimensional playlists",
    "Untangling the cosmic web of musical fate",
    "Warming up the chrono-acoustic transducers",
    "Detecting optimal wavelengths for your current emotional state",
    "Bribing the algorithm with imaginary currency and good intentions",
    "Folding spacetime carefully to avoid creasing the good frequencies",
]


class StationView(Container):
    """Left panel in station mode — spectrum analyzer + quirky messages."""

    def compose(self) -> ComposeResult:
        yield Label(
            "[bold magenta]◈  S T A T I O N  M O D E  ◈[/bold magenta]",
            id="station_title",
        )
        yield ParticleField(id="particles")
        yield Label("", id="station_message")

    def on_mount(self) -> None:
        self._last_message = ""
        self.set_interval(15.0, self._cycle_message)
        self._cycle_message()

    def _cycle_message(self) -> None:
        choices = [m for m in QUIRKY_MESSAGES if m != self._last_message]
        msg = random.choice(choices)
        self._last_message = msg
        self.query_one("#station_message", Label).update(
            f"[italic dim]{msg}[/italic dim]"
        )
