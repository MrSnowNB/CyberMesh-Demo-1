"""Conway grid module for CyberMesh Conway Demo.

This module implements the ConwayGrid class, managing an 8×8 toroidal grid
of Conway's Game of Life with color state preservation.
"""

from typing import List

import numpy as np

from .cell import Cell


class ConwayGrid:
    """8×8 toroidal Conway's Game of Life grid with color preservation.

    Manages cell states, applies Conway B3/S23 rules, and handles toroidal
    boundary wrapping. Colors are preserved through state transitions.
    """

    width: int = 8
    height: int = 8
    cells: List[List[Cell]]
    generation: int = 0
    alive_count: int = 0

    def __init__(self) -> None:
        """Initialize 8×8 grid with all cells dead and grey."""
        self.cells = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Cell(x, y))
            self.cells.append(row)

        self.generation = 0
        self.alive_count = 0

    def step(self) -> None:
        """Execute one Conway generation using B3/S23 rules.

        Birth (B3): Dead cell becomes alive if exactly 3 live neighbors
        Survival (S23): Live cell stays alive if 2 or 3 live neighbors
        Death: All other cases result in dead cell

        Colors are preserved through state transitions.
        """
        # Calculate next state for all cells
        next_states = []
        for y in range(self.height):
            row_states = []
            for x in range(self.width):
                cell = self.cells[y][x]
                live_neighbors = self._count_live_neighbors(x, y)
                next_alive = self._should_be_alive(cell.alive, live_neighbors)
                row_states.append(next_alive)
            next_states.append(row_states)

        # Apply next states
        alive_count = 0
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y][x]
                was_alive = cell.alive
                cell.alive = next_states[y][x]

                if cell.alive:
                    alive_count += 1

                    # Update EMA aggregate for live cells
                    neighbors = self.get_neighbors(x, y)
                    live_neighbors = [n for n in neighbors if n.alive]
                    if live_neighbors:
                        cell.update_ema_aggregate([n.color_vector for n in live_neighbors])

        self.alive_count = alive_count
        self.generation += 1

    def get_neighbors(self, x: int, y: int) -> List[Cell]:
        """Return Moore neighborhood (8 cells) with toroidal wrapping.

        Args:
            x: X coordinate (0-7)
            y: Y coordinate (0-7)

        Returns:
            List of 8 neighboring Cell objects
        """
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip self

                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbors.append(self.cells[ny][nx])

        return neighbors

    def get_cell(self, x: int, y: int) -> Cell:
        """Get cell at (x,y) with toroidal wrapping.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Cell at the wrapped coordinates
        """
        x = x % self.width
        y = y % self.height
        return self.cells[y][x]

    def reset(self) -> None:
        """Reset all cells to dead state with grey color."""
        for row in self.cells:
            for cell in row:
                cell.alive = False
                cell.reset_color()

        self.generation = 0
        self.alive_count = 0

    def create_glider(self, x: int, y: int) -> None:
        """Create glider pattern centered at (x,y) with green delta.

        Glider pattern (5 cells):
        . # .
        . . #
        # # #

        Args:
            x: Center X coordinate
            y: Center Y coordinate
        """
        # Glider pattern relative coordinates
        pattern = [
            (0, -1),  # Top center
            (1, 0),   # Middle right
            (-1, 1),  # Bottom left
            (0, 1),   # Bottom center
            (1, 1),   # Bottom right
        ]

        green_delta = np.array([0, 100, 0], dtype=np.int8)

        for dx, dy in pattern:
            cell = self.get_cell(x + dx, y + dy)
            cell.alive = True
            cell.apply_delta(green_delta)

        self._update_alive_count()

    def kill_region(self, cells: List[Cell]) -> None:
        """Mark cells as dead, preserve colors for resurrection.

        Args:
            cells: List of cells to kill
        """
        for cell in cells:
            cell.alive = False

        self._update_alive_count()

    def _count_live_neighbors(self, x: int, y: int) -> int:
        """Count live neighbors for cell at (x,y)."""
        return sum(1 for neighbor in self.get_neighbors(x, y) if neighbor.alive)

    def _should_be_alive(self, currently_alive: bool, live_neighbors: int) -> bool:
        """Determine if cell should be alive in next generation.

        B3/S23 rules:
        - Birth: Dead cell with exactly 3 neighbors becomes alive
        - Survival: Live cell with 2-3 neighbors stays alive
        - Death: All other cases result in dead cell
        """
        if currently_alive:
            return live_neighbors in (2, 3)  # Survival
        else:
            return live_neighbors == 3  # Birth

    def _update_alive_count(self) -> None:
        """Update the alive_count property."""
        self.alive_count = sum(1 for row in self.cells for cell in row if cell.alive)

    def __repr__(self) -> str:
        """String representation of the grid."""
        lines = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = self.cells[y][x]
                char = "█" if cell.alive else "·"
                row.append(char)
            lines.append(" ".join(row))
        return "\n".join(lines)
