"""Read existing EXIF metadata from media files."""

import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Path to exiftool binary
EXIFTOOL_PATH = "/opt/homebrew/bin/exiftool"


def read_exif_date(media_path: Path) -> Optional[datetime]:
    """Read DateTimeOriginal from existing file.

    Args:
        media_path: Path to media file

    Returns:
        datetime from EXIF or None if not found
    """
    try:
        result = subprocess.run(
            [EXIFTOOL_PATH, "-DateTimeOriginal", "-s3", str(media_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()

            # Parse exiftool date format: "2022:12:21 01:44:43"
            try:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                # Try without time
                try:
                    return datetime.strptime(date_str.split()[0], "%Y:%m:%d")
                except ValueError:
                    logger.debug(f"Could not parse date: {date_str}")
                    return None

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout reading EXIF from: {media_path.name}")
    except Exception as e:
        logger.debug(f"Error reading EXIF from {media_path.name}: {e}")

    return None


def has_matching_metadata(media_path: Path, json_datetime: datetime) -> bool:
    """Check if file already has metadata matching the JSON.

    Compares DateTimeOriginal in file with photoTakenTime from JSON.
    If they match (within 1 minute), file likely already processed.

    Args:
        media_path: Path to media file
        json_datetime: Expected datetime from JSON

    Returns:
        True if metadata matches (can skip processing), False otherwise
    """
    exif_date = read_exif_date(media_path)

    if exif_date is None:
        # No EXIF date found, needs processing
        return False

    # Compare dates (allow 1 minute difference for rounding)
    time_diff = abs((exif_date - json_datetime).total_seconds())

    if time_diff <= 60:
        logger.info(f"File {media_path.name} already has matching metadata, skipping")
        return True
    else:
        logger.debug(f"Date mismatch for {media_path.name}: EXIF={exif_date}, JSON={json_datetime}")
        return False
