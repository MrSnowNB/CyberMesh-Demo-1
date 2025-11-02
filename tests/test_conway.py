"""Unit tests for Conway grid module."""

import numpy as np

from src.conway import ConwayGrid


class TestConwayGrid:
    """Test cases for ConwayGrid class."""

    def test_initialization(self):
        """Test grid initialization with correct dimensions and cell states."""
        grid = ConwayGrid()

        assert grid.width == 8
        assert grid.height == 8
        assert grid.generation == 0
        assert grid.alive_count == 0

        # Check all cells are dead and grey
        for y in range(grid.height):
            for x in range(grid.width):
                cell = grid.cells[y][x]
                assert not cell.alive
                assert np.array_equal(cell.color_vector, np.array([128, 128, 128], dtype=np.uint8))
                assert cell.position == (x, y)

    def test_get_neighbors_center(self):
        """Test neighbor calculation for center cell (should have 8 neighbors)."""
        grid = ConwayGrid()

        neighbors = grid.get_neighbors(4, 4)
        assert len(neighbors) == 8

        # Check all expected positions (no wrapping needed)
        expected_positions = [
            (3, 3), (4, 3), (5, 3),  # Top row
            (3, 4),         (5, 4),  # Middle row (skip self)
            (3, 5), (4, 5), (5, 5),  # Bottom row
        ]

        neighbor_positions = [n.position for n in neighbors]
        for pos in expected_positions:
            assert pos in neighbor_positions

    def test_get_neighbors_corner_wrapping(self):
        """Test toroidal wrapping at corners."""
        grid = ConwayGrid()

        # Top-left corner (0,0) should wrap to bottom-right
        neighbors = grid.get_neighbors(0, 0)
        positions = [n.position for n in neighbors]

        # Should include (7,7), (0,7), (1,7), (7,0), (1,0), (7,1), (0,1), (1,1)
        assert (7, 7) in positions  # Bottom-right wrap
        assert (0, 7) in positions  # Bottom wrap
        assert (1, 7) in positions  # Bottom-right wrap
        assert (7, 0) in positions  # Left wrap
        assert (1, 0) in positions  # Right
        assert (7, 1) in positions  # Top-left wrap
        assert (0, 1) in positions  # Bottom
        assert (1, 1) in positions  # Bottom-right

    def test_get_neighbors_edge_wrapping(self):
        """Test toroidal wrapping at edges."""
        grid = ConwayGrid()

        # Right edge (7,4) should wrap left
        neighbors = grid.get_neighbors(7, 4)
        positions = [n.position for n in neighbors]

        assert (6, 3) in positions  # Normal
        assert (0, 3) in positions  # Left wrap
        assert (0, 4) in positions  # Left wrap
        assert (0, 5) in positions  # Left wrap

    def test_get_cell_wrapping(self):
        """Test get_cell with coordinate wrapping."""
        grid = ConwayGrid()

        # Normal access
        cell = grid.get_cell(2, 3)
        assert cell.position == (2, 3)

        # Wrapping
        cell = grid.get_cell(8, 3)  # x=8 -> x=0
        assert cell.position == (0, 3)

        cell = grid.get_cell(2, 9)  # y=9 -> y=1
        assert cell.position == (2, 1)

        cell = grid.get_cell(-1, 3)  # x=-1 -> x=7
        assert cell.position == (7, 3)

    def test_reset(self):
        """Test grid reset functionality."""
        grid = ConwayGrid()

        # Modify some cells
        grid.cells[0][0].alive = True
        grid.cells[1][1].apply_delta(np.array([50, 0, 0], dtype=np.int8))
        grid.generation = 5
        grid.alive_count = 2

        # Reset
        grid.reset()

        # Check all cells are dead and grey
        for row in grid.cells:
            for cell in row:
                assert not cell.alive
                assert np.array_equal(cell.color_vector, np.array([128, 128, 128], dtype=np.uint8))

        assert grid.generation == 0
        assert grid.alive_count == 0

    def test_create_glider(self):
        """Test glider creation with green delta."""
        grid = ConwayGrid()

        grid.create_glider(4, 4)

        # Check glider pattern (5 live cells with green color)
        expected_positions = [
            (4, 3),   # Top center
            (5, 4),   # Middle right
            (3, 5),   # Bottom left
            (4, 5),   # Bottom center
            (5, 5),   # Bottom right
        ]

        green_color = np.array([128, 228, 128], dtype=np.uint8)  # 128 + [0,100,0]

        for x, y in expected_positions:
            cell = grid.get_cell(x, y)
            assert cell.alive, f"Cell at ({x},{y}) should be alive"
            assert np.array_equal(cell.color_vector, green_color), f"Cell at ({x},{y}) should be green"

        assert grid.alive_count == 5

    def test_kill_region(self):
        """Test killing a region of cells."""
        grid = ConwayGrid()

        # Create some live cells
        cells_to_kill = [
            grid.get_cell(2, 2),
            grid.get_cell(2, 3),
            grid.get_cell(3, 2),
        ]

        for cell in cells_to_kill:
            cell.alive = True

        grid._update_alive_count()
        assert grid.alive_count == 3

        # Kill the region
        grid.kill_region(cells_to_kill)

        for cell in cells_to_kill:
            assert not cell.alive

        assert grid.alive_count == 0

    def test_step_empty_grid(self):
        """Test stepping with empty grid (no changes)."""
        grid = ConwayGrid()

        initial_repr = repr(grid)
        grid.step()

        assert repr(grid) == initial_repr
        assert grid.generation == 1
        assert grid.alive_count == 0

    def test_step_blinker_pattern(self):
        """Test blinker oscillator pattern (period 2)."""
        grid = ConwayGrid()

        # Create horizontal blinker: XXX
        blinker_positions = [(3, 4), (4, 4), (5, 4)]
        for x, y in blinker_positions:
            grid.get_cell(x, y).alive = True

        grid._update_alive_count()
        assert grid.alive_count == 3

        # Step 1: Should become vertical
        grid.step()
        assert grid.alive_count == 3

        vertical_positions = [(4, 3), (4, 4), (4, 5)]
        for x, y in vertical_positions:
            assert grid.get_cell(x, y).alive, f"Cell ({x},{y}) should be alive in vertical blinker"

        # Step 2: Should become horizontal again
        grid.step()
        assert grid.alive_count == 3

        for x, y in blinker_positions:
            assert grid.get_cell(x, y).alive, f"Cell ({x},{y}) should be alive in horizontal blinker"

    def test_step_block_still_life(self):
        """Test block still life pattern (no changes over time)."""
        grid = ConwayGrid()

        # Create block pattern: XX
        #                       XX
        block_positions = [(3, 3), (4, 3), (3, 4), (4, 4)]
        for x, y in block_positions:
            grid.get_cell(x, y).alive = True

        grid._update_alive_count()
        initial_repr = repr(grid)

        # Step multiple times - should remain unchanged
        for _ in range(5):
            grid.step()
            assert repr(grid) == initial_repr
            assert grid.alive_count == 4

    def test_glider_movement(self):
        """Test glider persists for multiple steps (basic movement test)."""
        grid = ConwayGrid()

        grid.create_glider(4, 4)  # Create glider in center

        # Glider should maintain 5 cells for at least 10 steps
        for step in range(10):
            grid.step()
            assert grid.alive_count == 5, f"Step {step}: Glider should have 5 cells, got {grid.alive_count}"

        # After 10 steps, glider should still be moving and alive
        assert grid.generation == 10
        assert grid.alive_count == 5

    def test_birth_and_death_rules(self):
        """Test Conway B3/S23 rules explicitly."""
        grid = ConwayGrid()

        # Test cases: (initial_alive, live_neighbors) -> expected_alive
        test_cases = [
            # Birth rule (B3)
            (False, 3, True),   # Dead + 3 neighbors -> birth
            (False, 2, False),  # Dead + 2 neighbors -> stay dead
            (False, 4, False),  # Dead + 4 neighbors -> stay dead

            # Survival rule (S23)
            (True, 2, True),    # Alive + 2 neighbors -> survive
            (True, 3, True),    # Alive + 3 neighbors -> survive
            (True, 1, False),   # Alive + 1 neighbor -> death
            (True, 4, False),   # Alive + 4 neighbors -> death
        ]

        for initial_alive, live_neighbors, expected_alive in test_cases:
            assert grid._should_be_alive(initial_alive, live_neighbors) == expected_alive, \
                f"Rule failed: alive={initial_alive}, neighbors={live_neighbors} -> {expected_alive}"

    def test_repr(self):
        """Test string representation."""
        grid = ConwayGrid()

        # Empty grid
        repr_str = repr(grid)
        lines = repr_str.split('\n')
        assert len(lines) == 8
        for line in lines:
            assert line == '· · · · · · · ·'

        # Add some live cells
        grid.get_cell(0, 0).alive = True
        grid.get_cell(7, 7).alive = True
        grid.get_cell(4, 4).alive = True

        repr_str = repr(grid)
        lines = repr_str.split('\n')

        # Check first line has live cell at position 0
        assert '█' in lines[0] and lines[0][0] == '█'

        # Check last line has live cell at position 14 (7*2, since "█ " is 2 chars per cell)
        assert '█' in lines[7] and lines[7][14] == '█'

        # Check middle line has live cell at position 8 (4*2)
        assert '█' in lines[4] and lines[4][8] == '█'
