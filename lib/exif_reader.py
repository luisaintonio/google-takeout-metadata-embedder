"""Read existing EXIF metadata from media files."""

import subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging
import os

from lib.exiftool import get_exiftool_path

logger = logging.getLogger(__name__)


def read_exif_date_enhanced(media_path: Path) -> Optional[Tuple[datetime, str]]:
    """Read date from EXIF metadata with multiple fallbacks.

    Tries multiple EXIF fields in priority order:
    1. DateTimeOriginal (primary - when photo was taken)
    2. CreateDate (when file was created)
    3. ModifyDate (when file was modified in camera/app)

    Args:
        media_path: Path to media file

    Returns:
        Tuple of (datetime, source) or None if no date found
        Source can be: "DateTimeOriginal", "CreateDate", or "ModifyDate"
    """
    exiftool_path = get_exiftool_path()
    if not exiftool_path:
        logger.warning("exiftool not found, cannot read EXIF data")
        return None

    # Try multiple EXIF date fields in priority order
    date_fields = [
        ("DateTimeOriginal", "DateTimeOriginal"),
        ("CreateDate", "CreateDate"),
        ("ModifyDate", "ModifyDate")
    ]

    for field_name, source_name in date_fields:
        try:
            result = subprocess.run(
                [exiftool_path, f"-{field_name}", "-s3", str(media_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                date_str = result.stdout.strip()

                # Parse exiftool date format: "2022:12:21 01:44:43"
                try:
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    logger.debug(f"Found {source_name} for {media_path.name}: {dt}")
                    return (dt, source_name)
                except ValueError:
                    # Try without time
                    try:
                        dt = datetime.strptime(date_str.split()[0], "%Y:%m:%d")
                        logger.debug(f"Found {source_name} for {media_path.name}: {dt}")
                        return (dt, source_name)
                    except ValueError:
                        logger.debug(f"Could not parse {field_name} date: {date_str}")
                        continue

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout reading {field_name} from: {media_path.name}")
            continue
        except Exception as e:
            logger.debug(f"Error reading {field_name} from {media_path.name}: {e}")
            continue

    return None


def read_file_mtime_safe(media_path: Path, min_age_days: int = 30) -> Optional[Tuple[datetime, str]]:
    """Read file modification time with safety validation.

    Only returns modification time if it passes validation checks:
    - Date is between 2000 and current year
    - Date is not in the future
    - Date is older than min_age_days (to avoid recent copy operations)

    Args:
        media_path: Path to media file
        min_age_days: Minimum age in days for modification time to be considered valid

    Returns:
        Tuple of (datetime, "file_mtime") or None if invalid
    """
    try:
        # Get file modification time
        mtime = os.path.getmtime(str(media_path))
        file_date = datetime.fromtimestamp(mtime)

        # Get current date
        now = datetime.now()
        current_year = now.year

        # Validation checks
        if file_date.year < 2000:
            logger.debug(f"File mtime too old ({file_date.year}) for {media_path.name}")
            return None

        if file_date.year > current_year:
            logger.debug(f"File mtime in future ({file_date.year}) for {media_path.name}")
            return None

        if file_date > now:
            logger.debug(f"File mtime in future for {media_path.name}")
            return None

        # Check minimum age
        age_days = (now - file_date).days
        if age_days < min_age_days:
            logger.debug(f"File mtime too recent ({age_days} days) for {media_path.name}")
            return None

        logger.debug(f"File mtime validated for {media_path.name}: {file_date}")
        return (file_date, "file_mtime")

    except Exception as e:
        logger.debug(f"Error reading file mtime for {media_path.name}: {e}")
        return None


def read_exif_date(media_path: Path) -> Optional[datetime]:
    """Read DateTimeOriginal from existing file.

    Args:
        media_path: Path to media file

    Returns:
        datetime from EXIF or None if not found
    """
    exiftool_path = get_exiftool_path()
    if not exiftool_path:
        logger.warning("exiftool not found, cannot read EXIF data")
        return None

    try:
        result = subprocess.run(
            [exiftool_path, "-DateTimeOriginal", "-s3", str(media_path)],
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


def read_any_date(media_path: Path, use_file_mtime: bool = False, min_age_days: int = 30) -> Optional[Tuple[datetime, str]]:
    """Read date from any available source with priority order.

    Priority:
    1. EXIF DateTimeOriginal, CreateDate, or ModifyDate
    2. File modification time (if use_file_mtime=True and passes validation)

    Args:
        media_path: Path to media file
        use_file_mtime: Whether to use file modification time as fallback
        min_age_days: Minimum age for file mtime to be considered valid

    Returns:
        Tuple of (datetime, source) or None if no date found
    """
    # Try EXIF data first
    exif_result = read_exif_date_enhanced(media_path)
    if exif_result:
        return exif_result

    # Fall back to file modification time if enabled
    if use_file_mtime:
        mtime_result = read_file_mtime_safe(media_path, min_age_days)
        if mtime_result:
            return mtime_result

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
