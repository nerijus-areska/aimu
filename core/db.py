import sqlite3
from pathlib import Path
import os


class MusicDatabase:
    """
    Manages the SQLite database for storing music file paths and ratings.
    """

    def __init__(self, db_path: str = "./music.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Ensure the database directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to SQLite database
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        
        # Create table if it doesn't exist, then apply any migrations
        self._create_table()
        self._migrate()

    def _create_table(self):
        """Create the music_files and feedback tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS music_files (
                path TEXT PRIMARY KEY,
                rating INTEGER NOT NULL DEFAULT 1,
                duration INTEGER,
                bitrate INTEGER,
                album TEXT,
                bpm INTEGER,
                title TEXT,
                artist TEXT,
                albumartist TEXT,
                tracknumber TEXT,
                genre TEXT,
                date TEXT,
                feedback TEXT,
                mood_pleasure REAL,
                mood_arousal REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                mood_pleasure REAL,
                mood_arousal REAL,
                rating INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (path) REFERENCES music_files(path)
            )
        """)
        self.conn.commit()

    def _migrate(self):
        """Add any columns that didn't exist in older versions of the schema."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(music_files)")
        existing = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("feedback", "ALTER TABLE music_files ADD COLUMN feedback TEXT"),
            ("mood_pleasure", "ALTER TABLE music_files ADD COLUMN mood_pleasure REAL"),
            ("mood_arousal", "ALTER TABLE music_files ADD COLUMN mood_arousal REAL"),
        ]
        for column, sql in migrations:
            if column not in existing:
                cursor.execute(sql)
        self.conn.commit()

    def _recreate_table(self):
        """Drop and recreate the table with new schema. Use only when you want to reset the database."""
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS music_files")
        cursor.execute("""
            CREATE TABLE music_files (
                path TEXT PRIMARY KEY,
                rating INTEGER NOT NULL DEFAULT 1,
                duration INTEGER,
                bitrate INTEGER,
                album TEXT,
                bpm INTEGER,
                title TEXT,
                artist TEXT,
                albumartist TEXT,
                tracknumber TEXT,
                genre TEXT,
                date TEXT,
                feedback TEXT,
                mood_pleasure REAL,
                mood_arousal REAL
            )
        """)
        self.conn.commit()

    def add_file(self, file_path: str, rating: int = 1, duration: int = None, 
                 bitrate: int = None, album: str = None, bpm: int = None,
                 title: str = None, artist: str = None, albumartist: str = None,
                 tracknumber: str = None, genre: str = None, date: str = None):
        """
        Add a file path to the database with metadata.
        
        Args:
            file_path: Absolute path to the music file
            rating: Rating for the file (default: 1)
            duration: Duration in seconds
            bitrate: Bitrate in kbps
            album: Album name
            bpm: Beats per minute
            title: Song title
            artist: Artist name
            albumartist: Album artist name
            tracknumber: Track number
            genre: Genre
            date: Release date/year
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO music_files 
            (path, rating, duration, bitrate, album, bpm, title, artist, 
             albumartist, tracknumber, genre, date) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_path, rating, duration, bitrate, album, bpm, title, artist,
              albumartist, tracknumber, genre, date))
        self.conn.commit()

    def add_files_batch(self, file_paths: list[str], rating: int = 1, 
                       metadata_list: list[dict] = None):
        """
        Add multiple file paths to the database in a batch.
        
        Args:
            file_paths: List of absolute paths to music files
            rating: Rating for all files (default: 1)
            metadata_list: Optional list of metadata dicts (one per file)
        """
        if not file_paths:
            return
        
        cursor = self.conn.cursor()
        # Use executemany for batch insert
        if metadata_list and len(metadata_list) == len(file_paths):
            data = [
                (path, rating, 
                 metadata.get('duration'), metadata.get('bitrate'),
                 metadata.get('album'), metadata.get('bpm'),
                 metadata.get('title'), metadata.get('artist'),
                 metadata.get('albumartist'), metadata.get('tracknumber'),
                 metadata.get('genre'), metadata.get('date'))
                for path, metadata in zip(file_paths, metadata_list)
            ]
        else:
            data = [(path, rating, None, None, None, None, None, None, None, None, None, None) 
                   for path in file_paths]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO music_files
            (path, rating, duration, bitrate, album, bpm, title, artist,
             albumartist, tracknumber, genre, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()

    def get_all_files(self) -> list[dict]:
        """
        Retrieve all files from the database, with latest feedback per track.

        Returns:
            List of dictionaries with all metadata fields
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.path, m.rating, m.duration, m.bitrate, m.album, m.bpm,
                   m.title, m.artist, m.albumartist, m.tracknumber, m.genre,
                   m.date, m.feedback,
                   f.mood_pleasure, f.mood_arousal, f.rating AS f_rating
            FROM music_files m
            LEFT JOIN feedback f ON f.path = m.path
                AND f.id = (SELECT MAX(f2.id) FROM feedback f2 WHERE f2.path = m.path)
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "path": row["path"],
                "rating": row["f_rating"] if row["f_rating"] is not None else row["rating"],
                "duration": row["duration"],
                "bitrate": row["bitrate"],
                "album": row["album"],
                "bpm": row["bpm"],
                "title": row["title"],
                "artist": row["artist"],
                "albumartist": row["albumartist"],
                "tracknumber": row["tracknumber"],
                "genre": row["genre"],
                "date": row["date"],
                "feedback": row["feedback"],
                "mood_pleasure": row["mood_pleasure"],
                "mood_arousal": row["mood_arousal"],
            })

        return result

    def get_feedback_history(self, file_path: str) -> list[dict]:
        """Return all feedback entries for a track, newest first."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT mood_pleasure, mood_arousal, rating FROM feedback WHERE path = ? ORDER BY id DESC",
            (file_path,),
        )
        return [
            {"mood_pleasure": r["mood_pleasure"], "mood_arousal": r["mood_arousal"], "rating": r["rating"]}
            for r in cursor.fetchall()
        ]

    def add_feedback(self, file_path: str, mood_pleasure: float, mood_arousal: float, rating: int) -> None:
        """Insert a new feedback record for a track (never updates)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (path, mood_pleasure, mood_arousal, rating) VALUES (?, ?, ?, ?)",
            (file_path, mood_pleasure, mood_arousal, rating),
        )
        self.conn.commit()

    def update_feedback(self, file_path: str, feedback: str):
        """Update the feedback text for a specific file."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE music_files SET feedback = ? WHERE path = ?",
            (feedback, file_path)
        )
        self.conn.commit()

    def delete_file(self, file_path: str):
        """
        Remove a file from the database.
        
        Args:
            file_path: Absolute path to the music file to remove
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM music_files WHERE path = ?", (file_path,))
        self.conn.commit()

    def count(self) -> int:
        """
        Get the total number of files in the database.
        
        Returns:
            Number of files stored
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM music_files")
        result = cursor.fetchone()
        return result["count"] if result else 0

    def close(self):
        """Close the database connection."""
        self.conn.close()
