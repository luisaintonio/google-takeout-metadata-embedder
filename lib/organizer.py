"""Output path calculation and folder organization."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Month number to name mapping
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def get_output_path(input_root: Path, media_file: Path, dt: Optional[datetime]) -> Path:
    """Calculate organized output path for media file.

    Creates structure: {input_root}/Output/{YEAR}/{Month}/{filename}
    Files without dates go to: {input_root}/Output/Unknown/{filename}

    Args:
        input_root: Root input directory (where Output folder will be created)
        media_file: Original media file path
        dt: Datetime for organizing (None = Unknown folder)

    Returns:
        Full output path for the file
    """
    output_base = input_root / "Output"

    if dt is None:
        # No date available - use Unknown folder
        folder = output_base / "Unknown"
    else:
        # Organize by Year/Month
        year = str(dt.year)
        month = MONTH_NAMES[dt.month]
        folder = output_base / year / month

    # Get original filename
    filename = media_file.name
    output_path = folder / filename

    # Handle name collisions by adding counter suffix
    if output_path.exists():
        counter = 1
        stem = media_file.stem
        suffix = media_file.suffix

        while output_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            output_path = folder / new_name
            counter += 1

        logger.info(f"Name collision detected, using: {output_path.name}")

    return output_path


def ensure_output_directory(output_path: Path) -> bool:
    """Ensure output directory exists.

    Args:
        output_path: Full path where file will be written

    Returns:
        True if directory was created/exists, False on error
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {output_path.parent}: {e}")
        return False
