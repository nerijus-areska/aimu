import json
from pathlib import Path

DEFAULT_BINDINGS: list[tuple[str, str, str]] = [
    ("h",     "help",           "Help"),
    ("q",     "quit",           "Quit"),
    ("space", "toggle_pause",   "Pause/Resume"),
    ("n",     "next_song",      "Next"),
    ("s",     "toggle_station", "Station"),
    ("f",     "feedback",       "Feedback"),
    ("left",  "seek_backward",  "- 10s"),
    ("right", "seek_forward",   "+ 10s"),
    ("z",     "volume_down",    "Vol -"),
    ("x",     "volume_up",      "Vol +"),
]


def load_bindings(path: str) -> list[tuple[str, str, str]]:
    try:
        data = json.loads(Path(path).read_text())  # {action: key}
        return [(data.get(action, key), action, desc)
                for key, action, desc in DEFAULT_BINDINGS]
    except (FileNotFoundError, json.JSONDecodeError):
        return list(DEFAULT_BINDINGS)


def save_bindings(path: str, bindings: list[tuple[str, str, str]]) -> None:
    Path(path).write_text(
        json.dumps({action: key for key, action, desc in bindings}, indent=2)
    )
