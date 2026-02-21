from ui.app import MusicPlayerApp
import sys

if __name__ == "__main__":
    # Ensure strict mode isn't accidentally on if using older Python versions
    # though Textual handles this well now.

    app = MusicPlayerApp()
    app.run()
