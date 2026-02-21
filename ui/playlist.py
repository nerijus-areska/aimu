from textual.widgets import DataTable
from textual.binding import Binding


class TrackListView(DataTable):
    """
    A scrollable list of music tracks.
    """

    # We can add custom key bindings if needed, but default
    # arrow keys and Enter are handled by DataTable automatically.

    def on_mount(self) -> None:
        # Set up the table structure
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_column("Track Name", width=None)

    def load_tracks(self, songs: list):
        """
        Populate the table with the list of songs.
        """
        self.clear()

        for index, song in enumerate(songs):
            # add_row returns a key, but we can also manually specify a key (the index).
            # We store the FULL PATH as the row identifier so we can retrieve it easily.
            # We use the index as a prefix to ensure uniqueness just in case.
            row_key = f"{index}|{song['path']}"

            self.add_row(song["name"], key=row_key)

        # Select the first row by default if list is not empty
        if songs:
            self.action_cursor_down()
