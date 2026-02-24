from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, DataTable
from textual.containers import Container

from core.keybindings import DEFAULT_BINDINGS, save_bindings


class RemapDialog(ModalScreen):
    """Tiny overlay that captures a single keypress for remapping."""

    DEFAULT_CSS = """
    RemapDialog { align: center middle; }
    #remap_dialog {
        width: 50;
        height: 6;
        border: solid yellow;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, description: str) -> None:
        super().__init__()
        self._description = description

    def compose(self) -> ComposeResult:
        with Container(id="remap_dialog"):
            yield Label(f"Press new key for: [bold]{self._description}[/bold]  •  Esc cancel")

    def on_key(self, event) -> None:
        event.stop()
        if event.key == "escape":
            self.dismiss(None)
        else:
            self.dismiss(event.key)


class HelpModal(ModalScreen):
    """Full-screen overlay listing all keybindings with remap support."""

    DEFAULT_CSS = """
    HelpModal { align: center middle; }
    #help_dialog {
        width: 70;
        height: 22;
        border: solid green;
        background: $surface;
        padding: 1 2;
    }
    #help_title  { text-align: center; margin-bottom: 1; }
    DataTable    { height: 14; }
    #help_hint   { text-align: center; margin-top: 1; }
    """

    def __init__(self, bindings: list[tuple[str, str, str]], keybindings_path: str) -> None:
        super().__init__()
        self._user_bindings = list(bindings)
        self._keybindings_path = keybindings_path

    def compose(self) -> ComposeResult:
        with Container(id="help_dialog"):
            yield Label("[bold]KEYBOARD SHORTCUTS[/bold]", id="help_title")
            yield DataTable(id="bindings_table")
            yield Label("Enter  remap   ·   r  reset defaults   ·   Esc  close", id="help_hint")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("KEY", "ACTION", "DESCRIPTION")
        for key, action, desc in self._user_bindings:
            table.add_row(key, action, desc)
        table.focus()

    def on_data_table_row_selected(self, message: DataTable.RowSelected) -> None:
        row_index = message.cursor_row
        _, action, desc = self._user_bindings[row_index]

        def on_remap(new_key: str | None) -> None:
            if new_key is None:
                return
            # Check for conflict with another action
            for i, (k, a, d) in enumerate(self._user_bindings):
                if k == new_key and a != action:
                    self.notify(
                        f"'{new_key}' is already bound to '{a}'. Choose a different key.",
                        severity="error",
                    )
                    return
            # Apply change
            for i, (k, a, d) in enumerate(self._user_bindings):
                if a == action:
                    self._user_bindings[i] = (new_key, a, d)
                    table = self.query_one(DataTable)
                    table.update_cell_at((i, 0), new_key)
                    break
            save_bindings(self._keybindings_path, self._user_bindings)
            self.notify("Key remapped. Restart AIMU to apply.")

        self.app.push_screen(RemapDialog(desc), on_remap)

    def on_key(self, event) -> None:
        if event.key == "escape":
            event.stop()
            self.action_close()
        elif event.key == "r":
            event.stop()
            self.action_reset_defaults()

    def action_close(self) -> None:
        self.dismiss()

    def action_reset_defaults(self) -> None:
        self._user_bindings = list(DEFAULT_BINDINGS)
        save_bindings(self._keybindings_path, self._user_bindings)
        table = self.query_one(DataTable)
        table.clear()
        for key, action, desc in self._user_bindings:
            table.add_row(key, action, desc)
        self.notify("Keybindings reset to defaults. Restart AIMU to apply.")
