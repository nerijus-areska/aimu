import random
from rich.text import Text
from textual.widget import Widget


_CHARS  = ['·', '·', '·', '·', '•', '◦']
_STYLES = ['dim', 'dim', 'dim', 'dim cyan', 'dim magenta', 'dim green']


class ParticleField(Widget):
    """
    Sparse field of slowly drifting dots.
    Abstract, calm — makes no pretense of reacting to music.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._particles: list[dict] = []
        self._ready = False

    def on_mount(self) -> None:
        self.set_interval(0.15, self._update)   # ~6 fps — intentionally slow

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _init(self, w: int, h: int) -> None:
        n = max(10, (w * h) // 50)             # roughly 1 dot per 50 cells
        self._particles = [
            {
                'x':     random.uniform(0, w),
                'y':     random.uniform(0, h),
                'vx':    random.uniform(-0.06, 0.06),
                'vy':    random.uniform(-0.04, 0.04),
                'char':  random.choice(_CHARS),
                'style': random.choice(_STYLES),
            }
            for _ in range(n)
        ]
        self._ready = True

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self) -> None:
        if not self.is_attached:
            return
        w, h = self.size.width, self.size.height
        if w == 0 or h == 0:
            return
        if not self._ready:
            self._init(w, h)
            return

        for p in self._particles:
            p['x'] = (p['x'] + p['vx']) % w
            p['y'] = (p['y'] + p['vy']) % h
            # Rare tiny velocity nudge so paths drift rather than loop
            if random.random() < 0.015:
                p['vx'] = max(-0.08, min(0.08, p['vx'] + random.uniform(-0.02, 0.02)))
                p['vy'] = max(-0.05, min(0.05, p['vy'] + random.uniform(-0.015, 0.015)))

        self.refresh()

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> Text:
        w, h = self.size.width, self.size.height
        if w == 0 or h == 0 or not self._ready:
            return Text("")

        # Build a blank grid then stamp each particle onto it
        grid: list[list[tuple[str, str]]] = [
            [(' ', '') for _ in range(w)] for _ in range(h)
        ]
        for p in self._particles:
            px = int(p['x']) % w
            py = int(p['y']) % h
            grid[py][px] = (p['char'], p['style'])

        result = Text()
        for ri, row in enumerate(grid):
            for ch, style in row:
                result.append(ch, style=style) if style else result.append(ch)
            if ri < h - 1:
                result.append('\n')

        return result
