"""JSON metadata parsing and extraction from Google Takeout files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_json(json_path: Path) -> Optional[dict]:
    """Load and parse JSON metadata file.

    Args:
        json_path: Path to JSON file

    Returns:
        Parsed JSON dict or None if parsing fails
    """
    # Try UTF-8 first (most common)
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        # Fallback to latin-1 which can handle any byte sequence
        logger.warning(f"UTF-8 decode failed for {json_path.name}, trying latin-1 encoding")
        try:
            with open(json_path, 'r', encoding='latin-1') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse JSON {json_path.name} with latin-1: {e}")
            return None
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to parse JSON {json_path.name}: {e}")
        return None


def extract_datetime(metadata: dict) -> Optional[datetime]:
    """Extract datetime from metadata with fallback.

    Tries photoTakenTime.timestamp first, then creationTime.timestamp.

    Args:
        metadata: Parsed JSON metadata

    Returns:
        datetime object or None if no valid timestamp found
    """
    try:
        # Try photoTakenTime first (primary source)
        timestamp = metadata.get('photoTakenTime', {}).get('timestamp')
        if timestamp:
            return datetime.fromtimestamp(int(timestamp))

        # Fallback to creationTime
        timestamp = metadata.get('creationTime', {}).get('timestamp')
        if timestamp:
            return datetime.fromtimestamp(int(timestamp))

    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Invalid timestamp in metadata: {e}")

    return None


def extract_gps(metadata: dict) -> Optional[Tuple[float, float, float]]:
    """Extract GPS coordinates from metadata.

    Args:
        metadata: Parsed JSON metadata

    Returns:
        Tuple of (latitude, longitude, altitude) or None if missing/zero
    """
    try:
        geo_data = metadata.get('geoData', {})
        lat = float(geo_data.get('latitude', 0))
        lon = float(geo_data.get('longitude', 0))
        alt = float(geo_data.get('altitude', 0))

        # Only return if coordinates are non-zero (Google uses 0.0 for missing data)
        if lat != 0.0 or lon != 0.0:
            return (lat, lon, alt)

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid GPS data in metadata: {e}")

    return None


def extract_people(metadata: dict) -> List[str]:
    """Extract people names from metadata.

    Args:
        metadata: Parsed JSON metadata

    Returns:
        List of people names (empty list if none found)
    """
    try:
        people = metadata.get('people', [])
        names = [person.get('name') for person in people if person.get('name')]
        return [name for name in names if name]  # Filter out None/empty
    except (TypeError, AttributeError) as e:
        logger.warning(f"Invalid people data in metadata: {e}")

    return []


def extract_description(metadata: dict) -> str:
    """Extract description from metadata.

    Args:
        metadata: Parsed JSON metadata

    Returns:
        Description string (empty string if not found)
    """
    try:
        return metadata.get('description', '').strip()
    except AttributeError:
        return ''


def extract_url(metadata: dict) -> str:
    """Extract Google Photos URL from metadata.

    Args:
        metadata: Parsed JSON metadata

    Returns:
        URL string (empty string if not found)
    """
    try:
        return metadata.get('url', '').strip()
    except AttributeError:
        return ''
