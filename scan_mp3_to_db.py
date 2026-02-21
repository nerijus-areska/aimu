#!/usr/bin/env python3
"""
Tool to scan a directory for MP3 files and store them in the SQLite database.
Run this separately from the main app.
"""

import argparse
import sys
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from core.db import MusicDatabase


def extract_mp3_metadata(file_path: str, print_metadata: bool = True) -> dict:
    """
    Extract metadata from an MP3 file using mutagen.
    
    Args:
        file_path: Path to the MP3 file
        print_metadata: If True, print metadata to console
        
    Returns:
        Dictionary with metadata fields
    """
    metadata = {}
    
    try:
        audio = MP3(file_path)
        duration_seconds = int(audio.info.length)
        bitrate_kbps = audio.info.bitrate // 1000
        
        metadata['duration'] = duration_seconds
        metadata['bitrate'] = bitrate_kbps
        
        if print_metadata:
            print(f"Duration: {duration_seconds // 60}:{duration_seconds % 60:02}")
            print(f"Bitrate:  {bitrate_kbps} kbps")
        
        # Get ID3 Tags (Artist, Title, etc.)
        # EasyID3 makes the tags human-readable (keys like 'artist' instead of 'TPE1')
        tags = EasyID3(file_path)
        
        # Map EasyID3 keys to our database fields
        tag_mapping = {
            'album': 'album',
            'bpm': 'bpm',
            'title': 'title',
            'artist': 'artist',
            'albumartist': 'albumartist',
            'tracknumber': 'tracknumber',
            'genre': 'genre',
            'date': 'date'
        }
        
        for key, db_field in tag_mapping.items():
            if key in tags and tags[key]:
                value = tags[key][0]
                metadata[db_field] = value
                if print_metadata:
                    print(f"{key.capitalize()}: {value}")
        
        # Convert bpm to int if present
        if 'bpm' in metadata:
            try:
                metadata['bpm'] = int(metadata['bpm'])
            except (ValueError, TypeError):
                pass
            
    except ID3NoHeaderError:
        metadata['_warn'] = 'no_tags'
        if print_metadata:
            print(f"  [warning] No ID3 tags — added without metadata")
    except Exception as e:
        metadata['_warn'] = str(e)
        if print_metadata:
            print(f"  [warning] Could not read metadata ({e}) — added without metadata")
    
    return metadata


def scan_mp3_files(root_path: str, print_metadata: bool = True) -> tuple[list[str], list[dict]]:
    """
    Recursively scan for all MP3 files in the given directory.
    
    Args:
        root_path: Path to the directory to scan
        print_metadata: If True, print metadata for each file found
        
    Returns:
        Tuple of (list of absolute paths to MP3 files, list of metadata dicts)
    """
    directory = Path(root_path)
    
    if not directory.exists():
        print(f"Error: The directory '{root_path}' does not exist.")
        return [], []
    
    if not directory.is_dir():
        print(f"Error: '{root_path}' is not a directory.")
        return [], []
    
    mp3_files = []
    metadata_list = []
    warn_count = 0

    print(f"Scanning {root_path} for MP3 files...")

    try:
        for file_path in directory.rglob("*.mp3"):
            if file_path.is_file():
                file_path_str = str(file_path.absolute())
                if print_metadata:
                    print(f"File: {file_path_str}")

                metadata = extract_mp3_metadata(file_path_str, print_metadata=print_metadata)
                if '_warn' in metadata:
                    warn_count += 1
                    metadata.pop('_warn')

                mp3_files.append(file_path_str)
                metadata_list.append(metadata)

                if print_metadata:
                    print()

    except PermissionError:
        print(f"Permission denied scanning some folders in {root_path}")

    if warn_count:
        print(f"Note: {warn_count} file(s) had unreadable metadata and were added without it.")

    # Sort files and metadata together
    sorted_pairs = sorted(zip(mp3_files, metadata_list))
    mp3_files, metadata_list = zip(*sorted_pairs) if sorted_pairs else ([], [])

    return list(mp3_files), list(metadata_list)


def main():
    parser = argparse.ArgumentParser(
        description="Scan a directory for MP3 files and store paths in SQLite database"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the directory to scan for MP3 files"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./music.db",
        help="Path to the SQLite database file (default: ./music.db)"
    )
    parser.add_argument(
        "--rating",
        type=int,
        default=3,
        help="Rating to assign to all files (default: 3)"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip printing metadata for each file"
    )
    
    args = parser.parse_args()
    
    # Scan for MP3 files and extract metadata
    mp3_files, metadata_list = scan_mp3_files(args.path, print_metadata=not args.no_metadata)
    
    if not mp3_files:
        print("No MP3 files found.")
        sys.exit(0)
    
    print(f"Found {len(mp3_files)} MP3 files")
    
    # Initialize database and recreate table to ensure new schema
    print(f"Connecting to database at {args.db_path}...")
    db = MusicDatabase(db_path=args.db_path)

    # Add files to database with metadata
    print(f"Adding files to database with rating {args.rating}...")
    db.add_files_batch(mp3_files, rating=args.rating, metadata_list=metadata_list)
    
    # Verify
    count = db.count()
    print(f"Database now contains {count} files")
    
    # Close database connection
    db.close()
    print("Done!")


if __name__ == "__main__":
    main()
