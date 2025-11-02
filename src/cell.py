"""Cell module for CyberMesh Conway Demo.

This module implements the Cell class, representing a single cell in the Conway grid
with color state and delta-driven modifications.
"""

from __future__ import annotations

import time

import numpy as np
import numpy.typing as npt


class Cell:
    """Represents a single cell in the Conway grid with color state.

    Each cell maintains its alive/dead state, position, and RGB color vector.
    Colors can be modified through delta operations with automatic clipping.
    """

    # Core attributes
    alive: bool
    position: tuple[int, int]  # (x, y) coordinates, 0-7 range
    color_vector: npt.NDArray[np.uint8]  # Shape: (3,) - [R, G, B]

    # CyberMesh memory attributes
    ema_aggregate: npt.NDArray[np.uint8]  # Exponential moving average of neighbor colors
    last_updated: float  # Timestamp of last delta application

    def __init__(self, x: int, y: int) -> None:
        """Initialize cell at position (x,y) with default grey color.

        Args:
            x: X coordinate (0-7)
            y: Y coordinate (0-7)

        Raises:
            ValueError: If coordinates are outside valid range [0, 7]
        """
        if not (0 <= x < 8 and 0 <= y < 8):
            raise ValueError(f"Cell coordinates ({x}, {y}) must be in range [0, 7]")

        self.alive = False
        self.position = (x, y)

        # Initialize with grey color (128, 128, 128)
        self.color_vector = np.array([128, 128, 128], dtype=np.uint8)
        self.ema_aggregate = np.array([128, 128, 128], dtype=np.uint8)
        self.last_updated = time.time()

    def apply_delta(self, delta: npt.NDArray[np.int8]) -> Cell:
        """Apply RGB delta to color_vector with clipping to [0, 255].

        Args:
            delta: RGB delta values as int8 array, shape (3,)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If delta is not a valid int8 array of shape (3,)
        """
        if not (isinstance(delta, np.ndarray) and
                delta.dtype == np.int8 and
                delta.shape == (3,)):
            raise ValueError("Delta must be int8 numpy array of shape (3,)")

        # Apply delta with clipping to valid range
        new_color = self.color_vector.astype(np.int16) + delta.astype(np.int16)
        self.color_vector = np.clip(new_color, 0, 255).astype(np.uint8)
        self.last_updated = time.time()

        return self

    def reset_color(self) -> Cell:
        """Reset color to default grey (128, 128, 128).

        Returns:
            Self for method chaining
        """
        self.color_vector = np.array([128, 128, 128], dtype=np.uint8)
        self.ema_aggregate = np.array([128, 128, 128], dtype=np.uint8)
        self.last_updated = time.time()

        return self

    def update_ema_aggregate(self, neighbor_colors: list[npt.NDArray[np.uint8]],
                           alpha: float = 0.1) -> None:
        """Update exponential moving average of neighbor colors.

        Args:
            neighbor_colors: List of color vectors from neighboring cells
            alpha: Smoothing factor (0.1 = 10% new, 90% old)
        """
        if not neighbor_colors:
            return

        # Compute mean of neighbor colors
        neighbor_mean = np.mean(neighbor_colors, axis=0).astype(np.uint8)

        # Update EMA: ema = alpha * new + (1 - alpha) * old
        self.ema_aggregate = (
            alpha * neighbor_mean +
            (1 - alpha) * self.ema_aggregate
        ).astype(np.uint8)

    def __repr__(self) -> str:
        """Debug representation: Cell(3,4,alive=True,[128,128,128])."""
        x, y = self.position
        r, g, b = self.color_vector
        return f"Cell({x},{y},alive={self.alive},[{r},{g},{b}])"

    def __eq__(self, other: object) -> bool:
        """Equality based on position only."""
        if not isinstance(other, Cell):
            return NotImplemented
        return self.position == other.position

    def __hash__(self) -> int:
        """Hash based on position for use in sets/dicts."""
        return hash(self.position)
