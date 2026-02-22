"""Recursive file scanning to find media files and matching JSON metadata."""

import json
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Supported media file extensions
MEDIA_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.heic', '.webp', '.dng', '.nef',
    # Videos
    '.mov', '.mp4', '.avi'
}


def find_matching_json(media_file: Path) -> Optional[Path]:
    """Find matching JSON metadata file for media file.

    Searches in this order:
    1. Exact match: filename.ext.json
    2. Numbered suffix: filename.ext(1).json, filename.ext(2).json, ...
    3. Any JSON starting with filename.ext, verifying title field matches

    Args:
        media_file: Path to media file

    Returns:
        Path to matching JSON file or None if not found
    """
    parent = media_file.parent
    media_name = media_file.name

    # 1. Try exact match
    exact_json = parent / f"{media_name}.json"
    if exact_json.exists():
        logger.debug(f"Found exact JSON match: {exact_json.name}")
        return exact_json

    # 2. Try numbered suffixes (1) through (99)
    for i in range(1, 100):
        numbered_json = parent / f"{media_name}({i}).json"
        if numbered_json.exists():
            logger.debug(f"Found numbered JSON match: {numbered_json.name}")
            return numbered_json

    # 3. Search for any JSON starting with media filename and check title field
    pattern = f"{media_name}*.json"
    matching_jsons = list(parent.glob(pattern))

    for json_path in matching_jsons:
        # Skip macOS resource fork JSON files
        if json_path.name.startswith('._'):
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                title = metadata.get('title', '')

                # Check if title matches media filename
                if title == media_name:
                    logger.debug(f"Found JSON via title match: {json_path.name}")
                    return json_path
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            logger.debug(f"Skipping invalid JSON {json_path.name}: {e}")
            continue

    logger.debug(f"No matching JSON found for: {media_name}")
    return None


def scan_folder(root_path: Path, progress_callback=None) -> Tuple[List[Tuple[Path, Path]], List[Path]]:
    """Recursively scan folder for media files with and without JSON metadata.

    Args:
        root_path: Root directory to scan
        progress_callback: Optional callback function(photo_count, video_count) called for each file found

    Returns:
        Tuple of:
        - List of tuples (media_file_path, json_file_path) for files with JSON
        - List of media_file_path for files without JSON
    """
    if not root_path.exists() or not root_path.is_dir():
        logger.error(f"Invalid directory: {root_path}")
        return [], []

    media_with_json = []
    media_without_json = []

    # Extensions for photos vs videos
    photo_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.heic', '.webp', '.dng', '.nef'}
    video_extensions = {'.mov', '.mp4', '.avi'}

    photo_count = 0
    video_count = 0

    # Recursively find all files
    for file_path in root_path.rglob('*'):
        # Skip if not a file
        if not file_path.is_file():
            continue

        # Skip macOS resource fork files (._filename) but keep real files (_filename)
        if file_path.name.startswith('._'):
            continue

        # Check if it's a media file
        if file_path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue

        # Skip files in Output directory (avoid reprocessing)
        if 'Output' in file_path.parts:
            continue

        # Count photos vs videos
        if file_path.suffix.lower() in photo_extensions:
            photo_count += 1
        elif file_path.suffix.lower() in video_extensions:
            video_count += 1

        # Try to find matching JSON
        json_path = find_matching_json(file_path)
        if json_path:
            media_with_json.append((file_path, json_path))
            logger.debug(f"Paired: {file_path.name} <-> {json_path.name}")
        else:
            media_without_json.append(file_path)
            logger.debug(f"No JSON metadata found for: {file_path}")

        # Call progress callback if provided
        if progress_callback:
            progress_callback(photo_count, video_count)

    logger.info(f"Found {len(media_with_json)} media files with JSON metadata")
    logger.info(f"Found {len(media_without_json)} media files without JSON metadata")
    return media_with_json, media_without_json


def extract_number_from_filename(filename: str) -> Optional[int]:
    """Extract the numeric sequence from a filename.

    Examples:
        IMG_3689.JPG -> 3689
        DSC_8217.NEF -> 8217
        photo123.jpg -> 123
        VID20220101.mp4 -> 20220101

    Args:
        filename: The filename to extract number from

    Returns:
        Extracted number or None if no number found
    """
    # Try to find a sequence of digits (usually 3+ digits)
    matches = re.findall(r'\d{3,}', filename)
    if matches:
        return int(matches[0])  # Return first match

    # Try shorter sequences as fallback
    matches = re.findall(r'\d+', filename)
    if matches:
        return int(matches[-1])  # Return last match

    return None


def guess_date_from_similar_files(
    media_file: Path,
    files_with_metadata: List[Tuple[Path, datetime]]
) -> Optional[datetime]:
    """Guess the date of a media file based on similar filenames.

    Looks for files with similar names and sequential numbers.
    For example, if IMG_3689 has metadata, IMG_3690 can use a similar date.

    Args:
        media_file: Media file without metadata
        files_with_metadata: List of (file_path, datetime) tuples for files with known dates

    Returns:
        Guessed datetime or None if can't guess
    """
    if not files_with_metadata:
        return None

    # Extract number from target filename
    target_number = extract_number_from_filename(media_file.name)
    if target_number is None:
        logger.debug(f"No number found in filename: {media_file.name}")
        return None

    # Get the prefix pattern (everything before the number)
    # e.g., "IMG_3689.JPG" -> "IMG_", "DSC8217.NEF" -> "DSC"
    match = re.search(r'^([^\d]*)', media_file.stem)
    prefix = match.group(1) if match else ""

    # Find files with similar prefix and close numbers
    similar_files = []
    for file_path, dt in files_with_metadata:
        if not file_path.stem.startswith(prefix):
            continue

        file_number = extract_number_from_filename(file_path.name)
        if file_number is None:
            continue

        # Calculate distance
        distance = abs(file_number - target_number)
        similar_files.append((distance, dt, file_path.name))

    if not similar_files:
        logger.debug(f"No similar files found for: {media_file.name}")
        return None

    # Sort by distance and get closest
    similar_files.sort(key=lambda x: x[0])
    closest_distance, closest_date, closest_name = similar_files[0]

    # Only use if the number is very close (within 100)
    if closest_distance <= 100:
        logger.info(f"Guessing date for {media_file.name} from {closest_name} (distance: {closest_distance})")
        return closest_date
    else:
        logger.debug(f"Closest file too far ({closest_distance}) for: {media_file.name}")
        return None
