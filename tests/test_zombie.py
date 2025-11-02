"""Unit tests for zombie protocol module."""

import pathlib
import tempfile

import numpy as np

from src.cell import Cell
from src.delta import DeltaLogger
from src.zombie import (
    _compute_neighbor_aggregate,
    compute_region_fidelity,
    demonstrate_zombie_protocol,
    kill_region,
    resurrect_cell,
)


class TestZombieProtocol:
    """Test cases for zombie protocol functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp())
        self.log_path = self.temp_dir / "test_zombie_log.json"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_kill_region(self):
        """Test killing a region preserves colors but marks cells dead."""
        cells = [
            Cell(0, 0),
            Cell(1, 1),
            Cell(2, 2)
        ]

        # Set up cells with custom colors and alive states
        cells[0].color_vector = np.array([255, 0, 0], dtype=np.uint8)  # Red
        cells[0].alive = True

        cells[1].color_vector = np.array([0, 255, 0], dtype=np.uint8)  # Green
        cells[1].alive = True

        cells[2].color_vector = np.array([0, 0, 255], dtype=np.uint8)  # Blue
        cells[2].alive = False  # Already dead

        original_colors = [cell.color_vector.copy() for cell in cells]
        original_alive = [cell.alive for cell in cells]

        # Kill the region
        kill_region(cells)

        # Verify colors are preserved
        for cell, original_color in zip(cells, original_colors):
            assert np.array_equal(cell.color_vector, original_color)

        # Verify alive states changed appropriately
        assert not cells[0].alive  # Was alive, now dead
        assert not cells[1].alive  # Was alive, now dead
        assert not cells[2].alive  # Was dead, still dead

    def test_resurrect_cell_with_neighbors(self):
        """Test resurrecting a cell using neighbor aggregation."""
        logger = DeltaLogger(log_path=self.log_path)

        # Create a dead cell to resurrect
        dead_cell = Cell(1, 1)
        dead_cell.alive = False
        dead_cell.color_vector = np.array([255, 100, 50], dtype=np.uint8)  # Original color

        # Create neighbor cells with different colors
        neighbors = [
            Cell(0, 1), Cell(2, 1), Cell(1, 0), Cell(1, 2)
        ]
        for i, neighbor in enumerate(neighbors):
            neighbor.alive = True
            # Give neighbors distinct colors
            neighbor.color_vector = np.array([50 + i*50, 100 + i*30, 150 + i*20], dtype=np.uint8)

        # Resurrect the cell
        fidelity = resurrect_cell(dead_cell, neighbors, logger)

        # Cell should now be alive
        assert dead_cell.alive

        # Color should be based on neighbor aggregate (mean of neighbor colors)
        expected_aggregate = np.mean([n.color_vector for n in neighbors], axis=0).astype(np.uint8)
        assert np.array_equal(dead_cell.color_vector, expected_aggregate)

        # Since no deltas exist, fidelity should be based on original vs aggregate
        # This will be low since original color is very different from neighbor average
        assert 0.0 <= fidelity <= 1.0

    def test_resurrect_cell_with_deltas(self):
        """Test resurrecting a cell using neighbor aggregation + delta reconstruction."""
        logger = DeltaLogger(log_path=self.log_path)

        # Create a cell and apply some deltas to build history
        cell = Cell(2, 3)
        original_color = cell.color_vector.copy()

        # Apply some deltas and log them
        deltas = [
            np.array([20, -10, 5], dtype=np.int8),
            np.array([-5, 15, 10], dtype=np.int8),
            np.array([0, 0, -20], dtype=np.int8)
        ]

        for delta in deltas:
            cell.apply_delta(delta)
            logger.log_delta(cell.position, delta, 1000.0, cell.color_vector)

        # Now kill the cell (preserve final color)
        final_color = cell.color_vector.copy()
        cell.alive = False

        # Create neighbors
        neighbors = [Cell(1, 3), Cell(3, 3), Cell(2, 2), Cell(2, 4)]
        for neighbor in neighbors:
            neighbor.alive = True
            neighbor.color_vector = np.array([120, 130, 140], dtype=np.uint8)

        # Resurrect using neighbor aggregate + delta reconstruction
        fidelity = resurrect_cell(cell, neighbors, logger)

        # Cell should be alive and color should be reconstructed
        assert cell.alive

        # The reconstruction should be much closer to the final color than just neighbor aggregate
        neighbor_aggregate = np.mean([n.color_vector for n in neighbors], axis=0).astype(np.uint8)
        reconstructed_vs_final = np.mean((cell.color_vector.astype(float) - final_color.astype(float))**2)**0.5
        aggregate_vs_final = np.mean((neighbor_aggregate.astype(float) - final_color.astype(float))**2)**0.5

        # Reconstruction should be better than just using neighbor aggregate
        assert reconstructed_vs_final <= aggregate_vs_final * 1.5  # Allow some tolerance

        # Fidelity should be reasonably high
        assert fidelity >= 0.80  # Should achieve good reconstruction

    def test_resurrect_cell_already_alive(self):
        """Test resurrecting a cell that's already alive returns perfect fidelity."""
        logger = DeltaLogger(log_path=self.log_path)

        cell = Cell(0, 0)
        cell.alive = True
        neighbors = []

        fidelity = resurrect_cell(cell, neighbors, logger)

        assert fidelity == 1.0
        assert cell.alive  # Still alive

    def test_compute_region_fidelity(self):
        """Test computing average fidelity for a resurrected region."""
        # Create original cells
        original_cells = []
        resurrected_cells = []

        for i in range(3):
            orig = Cell(i, 0)
            orig.color_vector = np.array([100 + i*20, 110 + i*15, 120 + i*10], dtype=np.uint8)

            resurr = Cell(i, 0)
            # Simulate imperfect resurrection
            resurr.color_vector = orig.color_vector + np.array([i-1, i-1, i-1], dtype=np.int8)

            original_cells.append(orig)
            resurrected_cells.append(resurr)

        avg_fidelity = compute_region_fidelity(original_cells, resurrected_cells)

        # Should be between 0 and 1
        assert 0.0 <= avg_fidelity <= 1.0

        # Individual fidelities should be high since differences are small
        from src.delta import compute_delta_fidelity
        for orig, resurr in zip(original_cells, resurrected_cells):
            individual_fidelity = compute_delta_fidelity(orig.color_vector, resurr.color_vector)
            assert individual_fidelity >= 0.95  # Very close colors

    def test_compute_neighbor_aggregate(self):
        """Test neighbor color aggregation."""
        # Create neighbors with different colors
        neighbors = []
        for i in range(4):
            neighbor = Cell(i, 0)
            neighbor.alive = True
            neighbor.color_vector = np.array([100 + i*10, 110 + i*5, 120 + i*2], dtype=np.uint8)
            neighbors.append(neighbor)

        aggregate = _compute_neighbor_aggregate(neighbors)

        # Should be mean of all neighbor colors
        expected = np.mean([n.color_vector for n in neighbors], axis=0).astype(np.uint8)
        assert np.array_equal(aggregate, expected)

    def test_compute_neighbor_aggregate_no_live_neighbors(self):
        """Test neighbor aggregation with no live neighbors."""
        neighbors = [Cell(0, 0), Cell(1, 1)]
        for neighbor in neighbors:
            neighbor.alive = False

        aggregate = _compute_neighbor_aggregate(neighbors)

        # Should return default grey
        expected = np.array([128, 128, 128], dtype=np.uint8)
        assert np.array_equal(aggregate, expected)

    def test_demonstrate_zombie_protocol(self):
        """Test the complete zombie protocol demonstration."""
        logger = DeltaLogger(log_path=self.log_path)

        # Create a 4x4 grid for testing
        grid_cells = []
        for y in range(4):
            row = []
            for x in range(4):
                cell = Cell(x, y)
                cell.alive = True
                # Give each cell a unique color
                cell.color_vector = np.array([50 + x*20, 60 + y*15, 70 + (x+y)*10], dtype=np.uint8)
                row.append(cell)
            grid_cells.append(row)

        # Apply some deltas to build history
        for y in range(4):
            for x in range(4):
                if (x + y) % 2 == 0:  # Apply to every other cell
                    delta = np.array([5, -3, 2], dtype=np.int8)
                    grid_cells[y][x].apply_delta(delta)
                    logger.log_delta((x, y), delta, 1000.0, grid_cells[y][x].color_vector)

        # Define kill region (2x2 center area)
        kill_coords = [(1, 1), (2, 1), (1, 2), (2, 2)]

        # Run zombie protocol demonstration
        result = demonstrate_zombie_protocol(grid_cells, logger, kill_coords)

        # Verify results structure
        assert "region_size" in result
        assert "average_fidelity" in result
        assert "perfect_resurrections" in result
        assert "good_resurrections" in result
        assert "fidelity_scores" in result
        assert "success" in result

        # Should have killed 4 cells
        assert result["region_size"] == 4

        # Fidelity scores should be reasonable
        assert len(result["fidelity_scores"]) == 4
        for fidelity in result["fidelity_scores"]:
            assert 0.0 <= fidelity <= 1.0

        # Average fidelity should be computed
        expected_avg = sum(result["fidelity_scores"]) / len(result["fidelity_scores"])
        assert abs(result["average_fidelity"] - expected_avg) < 0.001

        # Check that cells were actually killed and resurrected
        for x, y in kill_coords:
            cell = grid_cells[y][x]
            assert cell.alive, f"Cell ({x},{y}) should be resurrected"

    def test_demonstrate_zombie_protocol_empty_region(self):
        """Test zombie protocol with invalid/empty region."""
        logger = DeltaLogger(log_path=self.log_path)
        grid_cells = [[Cell(0, 0)]]

        result = demonstrate_zombie_protocol(grid_cells, logger, [])

        assert "error" in result
        assert result["error"] == "No valid cells found in kill region"

    def test_resurrection_fidelity_target(self):
        """Test that resurrection can achieve >90% fidelity under ideal conditions."""
        logger = DeltaLogger(log_path=self.log_path)

        # Create a cell with known color history
        cell = Cell(1, 1)
        original_color = cell.color_vector.copy()

        # Apply a small, recoverable delta
        delta = np.array([10, -5, 8], dtype=np.int8)
        cell.apply_delta(delta)
        logger.log_delta(cell.position, delta, 1000.0, cell.color_vector)

        # Kill the cell
        cell.alive = False

        # Create neighbors that are close to the final color
        neighbors = []
        for i in range(4):
            neighbor = Cell(i, 0)
            neighbor.alive = True
            # Make neighbors close to the cell's final color
            noise = np.random.randint(-5, 6, 3)
            neighbor.color_vector = (cell.color_vector + noise).clip(0, 255).astype(np.uint8)
            neighbors.append(neighbor)

        # Resurrect
        fidelity = resurrect_cell(cell, neighbors, logger)

        # Should achieve very high fidelity since deltas provide exact reconstruction
        assert fidelity >= 0.95, f"Fidelity {fidelity} should be >= 0.95 for ideal conditions"

        # Cell should be resurrected with reasonably accurate color
        color_error = np.mean(np.abs(cell.color_vector.astype(float) - original_color.astype(float)))
        assert color_error <= 20.0, f"Color error {color_error} should be reasonable"
