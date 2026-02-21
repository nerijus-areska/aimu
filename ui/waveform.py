import math
from rich.text import Text
from textual.widget import Widget

# Eight sub-cell heights from lowest to highest
_CHARS = " ▁▂▃▄▅▆▇█"


class WaveformWidget(Widget):
    """
    A compact two-row animated waveform shown in the track info panel.
    Row 0: green sine wave.  Row 1: cyan counter-phase sine wave.
    Pure decoration — not connected to audio data.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._phase = 0.0

    def on_mount(self) -> None:
        self.set_interval(0.08, self._tick)  # ~12 fps

    def _tick(self) -> None:
        self._phase += 0.28
        self.refresh()

    def render(self) -> Text:
        w = self.size.width
        draw_w = w - 4          # leave a 2-char indent on each side
        if draw_w <= 0:
            return Text("")

        result = Text()
        for row in range(2):
            phase = self._phase + (math.pi if row == 1 else 0.0)
            color = "green" if row == 0 else "cyan"

            result.append("  ")
            for x in range(draw_w):
                # Two overlapping sine waves for a more organic shape
                val = (
                    math.sin(x * 0.30 + phase) * 0.6 +
                    math.sin(x * 0.13 + phase * 0.71) * 0.4
                )
                normalized = (val + 1) / 2           # 0.0 – 1.0
                idx = int(normalized * (len(_CHARS) - 1))
                result.append(_CHARS[idx], style=color)

            if row == 0:
                result.append("\n")

        return result
