"""Unit tests for delta operations module."""

import json
import pathlib
import tempfile

import numpy as np
import pytest

from src.cell import Cell
from src.delta import (
    DeltaLogger,
    apply_delta_to_cells,
    compute_delta_fidelity,
    reconstruct_color_from_deltas,
)


class TestDeltaLogger:
    """Test cases for DeltaLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp())
        self.log_path = self.temp_dir / "test_delta_log.json"

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temp directory and all contents
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_new_log(self):
        """Test logger initialization with new log file."""
        logger = DeltaLogger(log_path=self.log_path, max_entries=100)

        assert logger.log_path == self.log_path
        assert logger.max_entries == 100
        assert logger.entries == []
        assert logger.get_log_size() == 0

        # File should be created
        assert self.log_path.exists()

    def test_initialization_existing_log(self):
        """Test logger initialization with existing log file."""
        # Create a log file with some entries
        initial_data = {
            "version": "1.0.0",
            "entries": [
                {
                    "timestamp": 1000.0,
                    "cell_id": [1, 2],
                    "delta": [10, 20, 30],
                    "result_color": [140, 150, 160]
                }
            ]
        }

        with open(self.log_path, 'w') as f:
            json.dump(initial_data, f)

        logger = DeltaLogger(log_path=self.log_path)
        assert len(logger.entries) == 1
        assert logger.entries[0]["cell_id"] == [1, 2]

    def test_initialization_corrupted_log(self):
        """Test logger initialization with corrupted log file."""
        # Create corrupted JSON
        with open(self.log_path, 'w') as f:
            f.write("{ invalid json }")

        # Should start with empty log and create valid file
        logger = DeltaLogger(log_path=self.log_path)
        assert logger.entries == []

        # File should contain valid JSON
        with open(self.log_path) as f:
            data = json.load(f)
        assert "version" in data
        assert "entries" in data
        assert data["entries"] == []

    def test_log_delta(self):
        """Test logging delta operations."""
        logger = DeltaLogger(log_path=self.log_path)

        cell_id = (3, 4)
        delta = np.array([10, -5, 25], dtype=np.int8)
        timestamp = 123456.789
        result_color = np.array([140, 120, 155], dtype=np.uint8)

        logger.log_delta(cell_id, delta, timestamp, result_color)

        assert len(logger.entries) == 1
        entry = logger.entries[0]
        assert entry["timestamp"] == timestamp
        assert entry["cell_id"] == [3, 4]
        assert entry["delta"] == [10, -5, 25]
        assert entry["result_color"] == [140, 120, 155]

        # File should be updated
        with open(self.log_path) as f:
            data = json.load(f)
        assert len(data["entries"]) == 1

    def test_log_rotation(self):
        """Test log rotation when exceeding max entries."""
        logger = DeltaLogger(log_path=self.log_path, max_entries=3)

        # Add 5 entries
        for i in range(5):
            logger.log_delta(
                cell_id=(i, 0),
                delta=np.array([i, 0, 0], dtype=np.int8),
                timestamp=float(i),
                result_color=np.array([128, 128, 128], dtype=np.uint8)
            )

        # Should only keep last 3 entries
        assert len(logger.entries) == 3
        assert logger.entries[0]["cell_id"] == [2, 0]  # First entry was rotated out
        assert logger.entries[-1]["cell_id"] == [4, 0]  # Last entry

    def test_get_recent_deltas(self):
        """Test retrieving recent deltas for a specific cell."""
        logger = DeltaLogger(log_path=self.log_path)

        # Add deltas for different cells
        logger.log_delta((0, 0), np.array([1, 0, 0], dtype=np.int8), 1.0, np.array([129, 128, 128], dtype=np.uint8))
        logger.log_delta((1, 1), np.array([0, 1, 0], dtype=np.int8), 2.0, np.array([128, 129, 128], dtype=np.uint8))
        logger.log_delta((0, 0), np.array([0, 0, 1], dtype=np.int8), 3.0, np.array([128, 128, 129], dtype=np.uint8))
        logger.log_delta((1, 1), np.array([1, 1, 0], dtype=np.int8), 4.0, np.array([129, 129, 128], dtype=np.uint8))

        # Get recent deltas for (0,0)
        recent = logger.get_recent_deltas((0, 0), count=5)
        assert len(recent) == 2
        assert recent[0]["timestamp"] == 3.0  # Most recent first
        assert recent[1]["timestamp"] == 1.0

        # Limit count
        recent_limited = logger.get_recent_deltas((0, 0), count=1)
        assert len(recent_limited) == 1
        assert recent_limited[0]["timestamp"] == 3.0

    def test_get_all_deltas_for_cell(self):
        """Test retrieving all deltas for a specific cell."""
        logger = DeltaLogger(log_path=self.log_path)

        # Add deltas for cell (0,0)
        logger.log_delta((0, 0), np.array([1, 0, 0], dtype=np.int8), 1.0, np.array([129, 128, 128], dtype=np.uint8))
        logger.log_delta((1, 1), np.array([0, 1, 0], dtype=np.int8), 2.0, np.array([128, 129, 128], dtype=np.uint8))
        logger.log_delta((0, 0), np.array([0, 0, 1], dtype=np.int8), 3.0, np.array([128, 128, 129], dtype=np.uint8))

        all_deltas = logger.get_all_deltas_for_cell((0, 0))
        assert len(all_deltas) == 2
        assert all_deltas[0]["timestamp"] == 1.0  # Chronological order
        assert all_deltas[1]["timestamp"] == 3.0

    def test_clear_log(self):
        """Test clearing the delta log."""
        logger = DeltaLogger(log_path=self.log_path)

        # Add some entries
        logger.log_delta((0, 0), np.array([1, 0, 0], dtype=np.int8), 1.0, np.array([129, 128, 128], dtype=np.uint8))
        assert len(logger.entries) == 1

        # Clear log
        logger.clear_log()
        assert len(logger.entries) == 0

        # File should be updated
        with open(self.log_path) as f:
            data = json.load(f)
        assert data["entries"] == []

    def test_atomic_write_corruption_resistance(self):
        """Test that atomic writes prevent log corruption."""
        logger = DeltaLogger(log_path=self.log_path)

        # Simulate partial write by corrupting temp file during write
        original_save = logger._save_log

        def failing_save():
            # Create temp file but don't write valid JSON
            fd, temp_path = tempfile.mkstemp(dir=self.log_path.parent, suffix='.tmp')
            with open(fd, 'w') as f:
                f.write("{ invalid json")
            import os
            os.close(fd)
            # Don't complete the atomic rename - simulates crash

        logger._save_log = failing_save

        # This should not corrupt the main log file
        with pytest.raises(Exception):
            logger.log_delta((0, 0), np.array([1, 0, 0], dtype=np.int8), 1.0, np.array([129, 128, 128], dtype=np.uint8))

        # Main log should still be valid
        with open(self.log_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "entries" in data


class TestDeltaOperations:
    """Test cases for delta operation functions."""

    def test_apply_delta_to_cells(self):
        """Test bulk delta application with logging."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        log_path = temp_dir / "test_log.json"

        try:
            logger = DeltaLogger(log_path=log_path)

            # Create test cells
            cells = [
                Cell(0, 0),
                Cell(1, 1),
                Cell(2, 2)
            ]

            # Apply delta to all cells
            delta = np.array([10, 20, 30], dtype=np.int8)
            apply_delta_to_cells(cells, delta, logger)

            # Check cells were modified
            for cell in cells:
                expected_color = np.array([138, 148, 158], dtype=np.uint8)  # 128 + [10, 20, 30]
                assert np.array_equal(cell.color_vector, expected_color)

            # Check logging
            assert logger.get_log_size() == 3
            for i, cell in enumerate(cells):
                deltas = logger.get_all_deltas_for_cell(cell.position)
                assert len(deltas) == 1
                assert deltas[0]["delta"] == [10, 20, 30]

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_reconstruct_color_from_deltas(self):
        """Test color reconstruction from delta sequence."""
        base_color = np.array([100, 110, 120], dtype=np.uint8)

        deltas = [
            {
                "cell_id": [2, 3],
                "delta": [10, 0, 0],
                "timestamp": 1.0,
                "result_color": [110, 110, 120]
            },
            {
                "cell_id": [2, 3],
                "delta": [0, 5, 0],
                "timestamp": 2.0,
                "result_color": [110, 115, 120]
            },
            {
                "cell_id": [2, 3],
                "delta": [0, 0, -10],
                "timestamp": 3.0,
                "result_color": [110, 115, 110]
            }
        ]

        reconstructed = reconstruct_color_from_deltas((2, 3), base_color, deltas)

        # Should apply all deltas in sequence: 100+10, 110+5, 120-10 = [110, 115, 110]
        expected = np.array([110, 115, 110], dtype=np.uint8)
        assert np.array_equal(reconstructed, expected)

    def test_reconstruct_color_no_matching_deltas(self):
        """Test reconstruction when no deltas match the cell."""
        base_color = np.array([100, 110, 120], dtype=np.uint8)

        deltas = [
            {
                "cell_id": [0, 0],  # Different cell
                "delta": [10, 0, 0],
                "timestamp": 1.0,
                "result_color": [110, 110, 120]
            }
        ]

        reconstructed = reconstruct_color_from_deltas((2, 3), base_color, deltas)

        # Should return base color unchanged
        assert np.array_equal(reconstructed, base_color)

    def test_compute_delta_fidelity(self):
        """Test fidelity computation between original and reconstructed colors."""
        original = np.array([100, 150, 200], dtype=np.uint8)
        reconstructed = np.array([100, 150, 200], dtype=np.uint8)

        # Perfect match
        fidelity = compute_delta_fidelity(original, reconstructed)
        assert fidelity == pytest.approx(1.0)

        # Partial match
        reconstructed_partial = np.array([120, 140, 180], dtype=np.uint8)
        fidelity_partial = compute_delta_fidelity(original, reconstructed_partial)
        assert 0.0 < fidelity_partial < 1.0

        # No match
        reconstructed_opposite = np.array([200, 50, 0], dtype=np.uint8)
        fidelity_opposite = compute_delta_fidelity(original, reconstructed_opposite)
        assert fidelity_opposite < 0.5  # Should be low similarity

    def test_compute_delta_fidelity_zero_vectors(self):
        """Test fidelity computation with zero vectors."""
        zero = np.array([0, 0, 0], dtype=np.uint8)

        # Both zero - perfect match
        fidelity = compute_delta_fidelity(zero, zero)
        assert fidelity == 1.0

        # One zero, one non-zero
        non_zero = np.array([100, 100, 100], dtype=np.uint8)
        fidelity = compute_delta_fidelity(zero, non_zero)
        assert fidelity == 0.0

    def test_compute_delta_fidelity_identical_vectors(self):
        """Test fidelity with identical non-zero vectors."""
        color = np.array([50, 100, 150], dtype=np.uint8)
        fidelity = compute_delta_fidelity(color, color)
        assert fidelity == pytest.approx(1.0)
