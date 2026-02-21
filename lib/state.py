"""Processing state management for resume capability."""

import json
import hashlib
from pathlib import Path
from typing import Set
import logging

logger = logging.getLogger(__name__)


class ProcessingState:
    """Track processing state to enable resume capability.

    Maintains a list of successfully processed files so that
    interrupted processing can be resumed without reprocessing files.
    """

    def __init__(self, state_file: Path):
        """Initialize state tracker.

        Args:
            state_file: Path to state file (e.g., .processing_state.json)
        """
        self.state_file = state_file
        self.processed_files: Set[str] = self._load_state()
        self.newly_processed = 0

    def _load_state(self) -> Set[str]:
        """Load previously processed files from state file.

        Returns:
            Set of file hashes that were successfully processed
        """
        if not self.state_file.exists():
            return set()

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded processing state: {len(data)} files previously processed")
                return set(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load state file: {e}, starting fresh")
            return set()

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute unique hash for a file path.

        Uses MD5 of the absolute path to uniquely identify files.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash string
        """
        absolute_path = str(file_path.resolve())
        return hashlib.md5(absolute_path.encode('utf-8')).hexdigest()

    def is_processed(self, file_path: Path) -> bool:
        """Check if file was already successfully processed.

        Args:
            file_path: Path to file

        Returns:
            True if file was already processed
        """
        file_hash = self._compute_file_hash(file_path)
        return file_hash in self.processed_files

    def mark_processed(self, file_path: Path):
        """Mark file as successfully processed.

        Args:
            file_path: Path to file that was processed
        """
        file_hash = self._compute_file_hash(file_path)
        self.processed_files.add(file_hash)
        self.newly_processed += 1

        # Save state after every 10 files for safety
        if self.newly_processed % 10 == 0:
            self.save_state()

    def save_state(self):
        """Persist state to disk.

        Writes the set of processed file hashes to the state file.
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(list(self.processed_files), f, indent=2)
            logger.debug(f"Saved processing state: {len(self.processed_files)} files")
        except IOError as e:
            logger.error(f"Failed to save state file: {e}")

    def clear(self):
        """Clear all processing state.

        Removes the state file and resets in-memory state.
        """
        self.processed_files.clear()
        self.newly_processed = 0

        if self.state_file.exists():
            try:
                self.state_file.unlink()
                logger.info("Cleared processing state")
            except IOError as e:
                logger.warning(f"Could not delete state file: {e}")

    def get_stats(self) -> dict:
        """Get statistics about processing state.

        Returns:
            Dictionary with state statistics
        """
        return {
            'total_processed': len(self.processed_files),
            'newly_processed': self.newly_processed,
            'state_file': str(self.state_file)
        }
