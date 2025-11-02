"""Unit tests for Cell module."""

import time
from unittest.mock import patch

import numpy as np
import pytest

from src.cell import Cell


class TestCell:
    """Test cases for Cell class."""

    def test_initialization_valid_coordinates(self):
        """Test cell initialization with valid coordinates."""
        cell = Cell(3, 4)

        assert cell.position == (3, 4)
        assert not cell.alive
        assert np.array_equal(cell.color_vector, np.array([128, 128, 128], dtype=np.uint8))
        assert np.array_equal(cell.ema_aggregate, np.array([128, 128, 128], dtype=np.uint8))
        assert isinstance(cell.last_updated, float)

    def test_initialization_invalid_coordinates(self):
        """Test cell initialization with invalid coordinates raises ValueError."""
        with pytest.raises(ValueError, match="Cell coordinates \\(-1, 0\\) must be in range \\[0, 7\\]"):
            Cell(-1, 0)

        with pytest.raises(ValueError, match="Cell coordinates \\(8, 0\\) must be in range \\[0, 7\\]"):
            Cell(8, 0)

        with pytest.raises(ValueError, match="Cell coordinates \\(0, -1\\) must be in range \\[0, 7\\]"):
            Cell(0, -1)

        with pytest.raises(ValueError, match="Cell coordinates \\(0, 8\\) must be in range \\[0, 7\\]"):
            Cell(0, 8)

    def test_apply_delta_positive_green(self):
        """Test applying positive green delta (+50 green) increases color."""
        cell = Cell(0, 0)
        initial_color = cell.color_vector.copy()

        delta = np.array([0, 50, 0], dtype=np.int8)
        result = cell.apply_delta(delta)

        # Should return self for method chaining
        assert result is cell

        # Green channel should increase by 50
        expected = initial_color + np.array([0, 50, 0])
        assert np.array_equal(cell.color_vector, expected)

        # Timestamp should be updated
        assert cell.last_updated > time.time() - 1  # Within last second

    def test_apply_delta_large_positive_clips_to_255(self):
        """Test applying large positive delta clips to 255."""
        cell = Cell(0, 0)

        # Use a delta that will cause overflow when added to uint8
        delta = np.array([127, 127, 127], dtype=np.int8)  # Max int8 value
        cell.apply_delta(delta)

        # 128 + 127 = 255, which should stay at 255
        expected = np.array([255, 255, 255], dtype=np.uint8)
        assert np.array_equal(cell.color_vector, expected)

    def test_apply_delta_large_negative_clips_to_0(self):
        """Test applying large negative delta clips to 0."""
        cell = Cell(0, 0)

        # Use a delta that will cause underflow when added to uint8
        delta = np.array([-128, -128, -128], dtype=np.int8)  # Min int8 value
        cell.apply_delta(delta)

        # 128 + (-128) = 0, which should stay at 0
        expected = np.array([0, 0, 0], dtype=np.uint8)
        assert np.array_equal(cell.color_vector, expected)

    def test_apply_delta_mixed_values(self):
        """Test applying delta with mixed positive/negative values."""
        cell = Cell(0, 0)
        # Start with grey (128, 128, 128)

        delta = np.array([50, -30, 100], dtype=np.int8)
        cell.apply_delta(delta)

        expected = np.array([178, 98, 228], dtype=np.uint8)  # 128+50, 128-30, 128+100
        assert np.array_equal(cell.color_vector, expected)

    def test_apply_delta_invalid_input(self):
        """Test applying invalid delta raises ValueError."""
        cell = Cell(0, 0)

        # Wrong shape
        with pytest.raises(ValueError, match="Delta must be int8 numpy array of shape \\(3,\\)"):
            cell.apply_delta(np.array([1, 2], dtype=np.int8))

        # Wrong dtype
        with pytest.raises(ValueError, match="Delta must be int8 numpy array of shape \\(3,\\)"):
            cell.apply_delta(np.array([1, 2, 3], dtype=np.int32))

        # Not a numpy array
        with pytest.raises(ValueError, match="Delta must be int8 numpy array of shape \\(3,\\)"):
            cell.apply_delta([1, 2, 3])  # type: ignore

    def test_reset_color(self):
        """Test resetting color to default grey."""
        cell = Cell(0, 0)

        # Modify color
        cell.apply_delta(np.array([100, -50, 25], dtype=np.int8))
        assert not np.array_equal(cell.color_vector, np.array([128, 128, 128], dtype=np.uint8))

        # Reset
        result = cell.reset_color()
        assert result is cell  # Method chaining

        # Should be back to grey
        expected = np.array([128, 128, 128], dtype=np.uint8)
        assert np.array_equal(cell.color_vector, expected)
        assert np.array_equal(cell.ema_aggregate, expected)

        # Timestamp should be updated
        assert cell.last_updated > time.time() - 1

    def test_update_ema_aggregate(self):
        """Test updating exponential moving average of neighbor colors."""
        cell = Cell(0, 0)

        # Initial EMA should be grey
        assert np.array_equal(cell.ema_aggregate, np.array([128, 128, 128], dtype=np.uint8))

        # Update with red and blue neighbors
        neighbor_colors = [
            np.array([255, 0, 0], dtype=np.uint8),    # Red
            np.array([0, 0, 255], dtype=np.uint8),    # Blue
        ]

        cell.update_ema_aggregate(neighbor_colors, alpha=0.5)

        # Should be average of neighbors: (255+0)/2=127.5, (0+0)/2=0, (0+255)/2=127.5
        # With alpha=0.5: 0.5 * new + 0.5 * old = 0.5 * [127.5, 0, 127.5] + 0.5 * [128, 128, 128]
        # = [63.75 + 64, 0 + 64, 63.75 + 64] = [127.75, 64, 127.75] → [127, 64, 127] when cast to uint8
        expected = np.array([127, 64, 127], dtype=np.uint8)
        assert np.array_equal(cell.ema_aggregate, expected)

    def test_update_ema_aggregate_empty_neighbors(self):
        """Test updating EMA with empty neighbor list does nothing."""
        cell = Cell(0, 0)
        original_ema = cell.ema_aggregate.copy()

        cell.update_ema_aggregate([])

        assert np.array_equal(cell.ema_aggregate, original_ema)

    def test_repr(self):
        """Test string representation."""
        cell = Cell(3, 4)
        repr_str = repr(cell)

        assert "Cell(3,4,alive=False,[128,128,128])" == repr_str

        # Test with modified state
        cell.alive = True
        cell.apply_delta(np.array([10, 20, 30], dtype=np.int8))

        repr_str = repr(cell)
        assert "Cell(3,4,alive=True,[138,148,158])" == repr_str

    def test_equality_and_hash(self):
        """Test equality and hashing based on position."""
        cell1 = Cell(2, 3)
        cell2 = Cell(2, 3)
        cell3 = Cell(3, 4)

        # Same position should be equal
        assert cell1 == cell2
        assert cell1 != cell3

        # Should be hashable for use in sets/dicts
        cell_set = {cell1, cell2, cell3}
        assert len(cell_set) == 2  # cell1 and cell2 are considered equal

    @patch('time.time')
    def test_timestamp_updates(self, mock_time):
        """Test that timestamps are updated correctly."""
        mock_time.return_value = 1000.0

        cell = Cell(0, 0)
        assert cell.last_updated == 1000.0

        mock_time.return_value = 1001.0
        cell.apply_delta(np.array([1, 2, 3], dtype=np.int8))
        assert cell.last_updated == 1001.0

        mock_time.return_value = 1002.0
        cell.reset_color()
        assert cell.last_updated == 1002.0
