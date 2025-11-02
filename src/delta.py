"""Delta operations module for CyberMesh Conway Demo.

This module implements delta logging and bulk operations for tracking
and replaying color changes in the Conway grid.
"""

import json
import pathlib
import tempfile
import time
from typing import Dict, List, Tuple, Any

import numpy as np

from .cell import Cell


class DeltaLogger:
    """Atomic JSON logging of all delta operations.

    Maintains a persistent log of color changes with timestamps,
    using atomic writes to prevent corruption.
    """

    log_path: pathlib.Path
    max_entries: int
    entries: List[Dict[str, Any]]

    def __init__(self, log_path: pathlib.Path = pathlib.Path("logs/delta_log.json"),
                 max_entries: int = 1000) -> None:
        """Initialize logger with log file path.

        Args:
            log_path: Path to the JSON log file
            max_entries: Maximum number of entries to keep (rotates old entries)
        """
        self.log_path = log_path
        self.max_entries = max_entries
        self.entries = []

        # Ensure logs directory exists
        self.log_path.parent.mkdir(exist_ok=True)

        # Load existing log if it exists
        self._load_log()

    def log_delta(self, cell_id: Tuple[int, int], delta: np.ndarray,
                  timestamp: float, result_color: np.ndarray) -> None:
        """Append delta operation to log with atomic write.

        Args:
            cell_id: (x, y) coordinates of the cell
            delta: RGB delta values applied
            timestamp: Unix timestamp of the operation
            result_color: Final color after delta application
        """
        entry = {
            "timestamp": timestamp,
            "cell_id": list(cell_id),
            "delta": delta.tolist(),
            "result_color": result_color.tolist()
        }

        self.entries.append(entry)

        # Rotate if we exceed max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        # Atomic write to disk
        self._save_log()

    def get_recent_deltas(self, cell_id: Tuple[int, int], count: int = 10) -> List[Dict[str, Any]]:
        """Return last N delta operations for a specific cell.

        Args:
            cell_id: (x, y) coordinates of the cell
            count: Maximum number of entries to return

        Returns:
            List of delta entries for the cell (most recent first)
        """
        cell_entries = [
            entry for entry in reversed(self.entries)
            if entry["cell_id"] == list(cell_id)
        ]
        return cell_entries[:count]

    def get_all_deltas_for_cell(self, cell_id: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Return all delta operations for a specific cell.

        Args:
            cell_id: (x, y) coordinates of the cell

        Returns:
            List of all delta entries for the cell (chronological order)
        """
        return [
            entry for entry in self.entries
            if entry["cell_id"] == list(cell_id)
        ]

    def clear_log(self) -> None:
        """Reset delta log (for testing)."""
        self.entries = []
        self._save_log()

    def get_log_size(self) -> int:
        """Return number of entries in the log."""
        return len(self.entries)

    def _load_log(self) -> None:
        """Load log from JSON file, creating empty log if file doesn't exist or is corrupted."""
        if not self.log_path.exists():
            self.entries = []
            self._save_log()  # Create the initial empty log file
            return

        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)

            # Validate structure
            if not isinstance(data, dict) or "entries" not in data:
                raise ValueError("Invalid log format")

            self.entries = data["entries"]

            # Validate entries
            for entry in self.entries:
                required_keys = ["timestamp", "cell_id", "delta", "result_color"]
                if not all(key in entry for key in required_keys):
                    raise ValueError(f"Invalid entry format: {entry}")

        except (json.JSONDecodeError, ValueError, IOError):
            # Log is corrupted or invalid, start fresh
            print(f"Warning: Could not load delta log {self.log_path}, starting fresh")
            self.entries = []
            self._save_log()

    def _save_log(self) -> None:
        """Atomically save log to JSON file."""
        data = {
            "version": "1.0.0",
            "entries": self.entries
        }

        # Atomic write: write to temp file, then rename
        with tempfile.NamedTemporaryFile(mode='w', dir=self.log_path.parent,
                                       suffix='.tmp', delete=False) as f:
            try:
                json.dump(data, f, indent=2)
                temp_path = f.name
            except Exception:
                # Clean up temp file on error
                pathlib.Path(f.name).unlink(missing_ok=True)
                raise

        # Atomic rename
        pathlib.Path(temp_path).replace(self.log_path)


def apply_delta_to_cells(cells: List[Cell], delta: np.ndarray,
                        logger: DeltaLogger) -> None:
    """Apply delta to multiple cells with logging.

    Args:
        cells: List of cells to modify
        delta: RGB delta values to apply
        logger: DeltaLogger instance for recording operations
    """
    timestamp = time.time()

    for cell in cells:
        original_color = cell.color_vector.copy()
        cell.apply_delta(delta)

        logger.log_delta(
            cell_id=cell.position,
            delta=delta,
            timestamp=timestamp,
            result_color=cell.color_vector
        )


def reconstruct_color_from_deltas(cell_id: Tuple[int, int], base_color: np.ndarray,
                                deltas: List[Dict[str, Any]]) -> np.ndarray:
    """Reconstruct cell color by applying a sequence of deltas.

    Args:
        cell_id: (x, y) coordinates of the cell
        base_color: Starting color before applying deltas
        deltas: List of delta entries in chronological order

    Returns:
        Reconstructed color after applying all deltas
    """
    color = base_color.copy()

    for entry in deltas:
        if entry["cell_id"] == list(cell_id):
            delta_array = np.array(entry["delta"], dtype=np.int8)
            # Apply delta with clipping
            new_color = color.astype(np.int16) + delta_array.astype(np.int16)
            color = np.clip(new_color, 0, 255).astype(np.uint8)

    return color


def compute_delta_fidelity(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """Compute cosine similarity between original and reconstructed colors.

    Args:
        original: Original color vector
        reconstructed: Reconstructed color vector

    Returns:
        Fidelity score between 0.0 and 1.0 (1.0 = perfect match)
    """
    # Cosine similarity
    dot_product = np.dot(original.astype(float), reconstructed.astype(float))
    norm_original = np.linalg.norm(original.astype(float))
    norm_reconstructed = np.linalg.norm(reconstructed.astype(float))

    if norm_original == 0 or norm_reconstructed == 0:
        return 1.0 if np.array_equal(original, reconstructed) else 0.0

    return dot_product / (norm_original * norm_reconstructed)
