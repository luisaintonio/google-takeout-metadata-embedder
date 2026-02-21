"""Exiftool command building and execution for metadata embedding."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Path to exiftool binary
EXIFTOOL_PATH = "/opt/homebrew/bin/exiftool"


def check_exiftool() -> bool:
    """Check if exiftool is available.

    Returns:
        True if exiftool is installed and accessible
    """
    try:
        result = subprocess.run(
            [EXIFTOOL_PATH, "-ver"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"Found exiftool version: {version}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"exiftool not found: {e}")

    return False


def format_datetime(dt: datetime) -> str:
    """Convert datetime to exiftool format.

    Args:
        dt: datetime object

    Returns:
        Formatted string: "YYYY:MM:DD HH:MM:SS"
    """
    return dt.strftime("%Y:%m:%d %H:%M:%S")


def is_video_file(file_path: Path) -> bool:
    """Check if file is a video based on extension.

    Args:
        file_path: Path to media file

    Returns:
        True if video file, False if image
    """
    video_extensions = {'.mov', '.mp4', '.avi'}
    return file_path.suffix.lower() in video_extensions


def build_image_command(
    file_path: Path,
    dt: Optional[datetime],
    gps: Optional[Tuple[float, float, float]],
    people: List[str],
    description: str,
    url: str
) -> List[str]:
    """Build exiftool command for image files.

    Args:
        file_path: Path to image file
        dt: Datetime to embed
        gps: GPS coordinates (lat, lon, alt) or None
        people: List of people names
        description: Image description
        url: Google Photos URL

    Returns:
        Command arguments list
    """
    cmd = [EXIFTOOL_PATH, "-overwrite_original"]

    # Date/time tags
    if dt:
        dt_str = format_datetime(dt)
        cmd.extend([
            f"-DateTimeOriginal={dt_str}",
            f"-CreateDate={dt_str}",
            f"-ModifyDate={dt_str}"
        ])

    # GPS coordinates
    if gps:
        lat, lon, alt = gps
        cmd.extend([
            f"-GPSLatitude={lat}",
            f"-GPSLongitude={lon}",
            f"-GPSAltitude={alt}"
        ])

    # People tags (add to both XMP and IPTC)
    for person in people:
        # Escape quotes in names
        safe_name = person.replace('"', '\\"')
        cmd.append(f"-XMP:PersonInImage={safe_name}")
        cmd.append(f"-IPTC:Keywords+={safe_name}")

    # Description
    if description:
        safe_desc = description.replace('"', '\\"')
        cmd.append(f"-ImageDescription={safe_desc}")

    # URL as identifier
    if url:
        cmd.append(f"-XMP:Identifier={url}")

    cmd.append(str(file_path))
    return cmd


def build_video_command(file_path: Path, dt: Optional[datetime]) -> List[str]:
    """Build exiftool command for video files.

    Args:
        file_path: Path to video file
        dt: Datetime to embed

    Returns:
        Command arguments list
    """
    cmd = [EXIFTOOL_PATH, "-overwrite_original"]

    # Video files: use QuickTime tags
    if dt:
        dt_str = format_datetime(dt)
        cmd.extend([
            f"-QuickTime:CreateDate={dt_str}",
            f"-QuickTime:ModifyDate={dt_str}",
            f"-XMP:DateCreated={dt_str}"
        ])

    cmd.append(str(file_path))
    return cmd


def embed_metadata(
    media_path: Path,
    dt: Optional[datetime],
    gps: Optional[Tuple[float, float, float]],
    people: List[str],
    description: str,
    url: str
) -> bool:
    """Embed metadata into media file using exiftool.

    Args:
        media_path: Path to media file
        dt: Datetime to embed
        gps: GPS coordinates or None
        people: List of people names
        description: Description text
        url: Google Photos URL

    Returns:
        True on success, False on failure
    """
    try:
        # Build appropriate command based on file type
        if is_video_file(media_path):
            cmd = build_video_command(media_path, dt)
        else:
            cmd = build_image_command(media_path, dt, gps, people, description, url)

        logger.debug(f"Running exiftool command: {' '.join(cmd)}")

        # Execute exiftool
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.debug(f"Successfully embedded metadata in: {media_path.name}")
            return True
        else:
            logger.error(f"exiftool failed for {media_path.name}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"exiftool timeout for: {media_path.name}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error embedding metadata in {media_path.name}: {e}")
        return False
