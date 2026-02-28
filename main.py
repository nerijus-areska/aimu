from ui.app import MusicPlayerApp
import sys

if __name__ == "__main__":
    debug = "--debug" in sys.argv
    app = MusicPlayerApp(debug=debug)
    app.run()
