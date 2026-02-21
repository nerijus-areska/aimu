import vlc
import time

class AudioEngine:
    """
    A minimal wrapper around the python-vlc binding.
    Handles loading media, playback control, and status reporting.
    """

    def __init__(self):
        # Initialize the VLC instance with default arguments.
        # '--quiet' keeps VLC from printing log noise to your terminal.
        self._instance = vlc.Instance('--quiet') 
        self._player = self._instance.media_player_new()
        
    def play(self, file_path: str):
        """
        Loads a file path and starts playback immediately.
        """
        # Create a new Media object
        media = self._instance.media_new(str(file_path))
        
        # Set the media to the player
        self._player.set_media(media)
        
        # Start playing
        self._player.play()

    def stop(self):
        """Stops playback entirely."""
        self._player.stop()

    def pause(self):
        """Pauses playback."""
        self._player.set_pause(1)

    def resume(self):
        """Resumes playback if paused."""
        self._player.set_pause(0)

    def toggle_pause(self):
        """Toggles between pause and play."""
        self._player.pause()

    def get_info(self):
        """
        Returns a dictionary with current song status.
        Useful for the UI to update the progress bar.
        """
        # get_position returns a float between 0.0 and 1.0
        progress = self._player.get_position()
        
        # get_time returns current time in milliseconds
        current_time_ms = self._player.get_time()
        
        # get_length returns total duration in milliseconds
        total_time_ms = self._player.get_length()

        return {
            "progress": max(0, progress),  # Ensure it's never negative
            "current_ms": current_time_ms,
            "total_ms": total_time_ms,
            "is_playing": self._player.is_playing() == 1
        }

    def has_finished(self):
        """
        Checks if the media has reached the end.
        VLC state 'Ended' is code 6.
        """
        return self._player.get_state() == vlc.State.Ended

    def seek_relative(self, seconds: int):
        """Seek forward (positive) or backward (negative) by the given number of seconds."""
        current = self._player.get_time()
        total = self._player.get_length()
        if current < 0 or total <= 0:
            return
        target = max(0, min(total, current + seconds * 1000))
        self._player.set_time(target)

    def set_volume(self, volume: int):
        """Set volume (0 to 100)."""
        self._player.audio_set_volume(volume)

    def get_volume(self) -> int:
        """Return current volume (0 to 100)."""
        return self._player.audio_get_volume()

# --- Quick Test Block ---
# This allows you to run 'python core/audio.py' to verify it works
# without building the whole UI yet.
if __name__ == "__main__":
    import sys
    
    # Simple test: python core/audio.py /path/to/song.mp3
    if len(sys.argv) < 2:
        print("Usage: python audio.py <path_to_mp3>")
    else:
        path = sys.argv[1]
        engine = AudioEngine()
        print(f"Playing: {path}")
        engine.play(path)
        
        try:
            while True:
                info = engine.get_info()
                # Print a text progress bar
                bar_len = 20
                filled = int(info['progress'] * bar_len)
                bar = "#" * filled + "-" * (bar_len - filled)
                
                print(f"\r[{bar}] {info['current_ms']}/{info['total_ms']} ms", end="")
                
                if engine.has_finished():
                    print("\nSong finished.")
                    break
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            engine.stop()
            print("\nStopped.")