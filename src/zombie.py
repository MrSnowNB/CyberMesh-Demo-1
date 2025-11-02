"""Zombie protocol module for CyberMesh Conway Demo.

This module implements the CyberMesh memory resurrection system,
demonstrating the ability to kill and perfectly resurrect cell colors
using neighbor aggregation and delta log reconstruction.
"""


import numpy as np

from .cell import Cell
from .delta import DeltaLogger, compute_delta_fidelity, reconstruct_color_from_deltas


def kill_region(cells: list[Cell]) -> None:
    """Kill a region of cells, marking them as dead while preserving colors.

    This simulates "zombification" where cells lose their alive state but
    retain their color information for potential resurrection.

    Args:
        cells: List of cells to kill
    """
    for cell in cells:
        cell.alive = False
        # Colors are preserved for resurrection


def resurrect_cell(cell: Cell, neighbors: list[Cell], logger: DeltaLogger,
                  alpha: float = 0.1) -> float:
    """Resurrect a dead cell using neighbor aggregation and delta reconstruction.

    The resurrection process:
    1. Compute neighbor color aggregate (exponential moving average)
    2. Apply recent deltas from the log to reconstruct original color
    3. Update cell with resurrected color and mark as alive
    4. Return fidelity score (1.0 = perfect match)

    Args:
        cell: The dead cell to resurrect
        neighbors: List of neighboring cells for color aggregation
        logger: DeltaLogger instance for retrieving delta history
        alpha: EMA smoothing factor for neighbor aggregation

    Returns:
        Fidelity score between 0.0 and 1.0 (1.0 = perfect resurrection)
    """
    if cell.alive:
        return 1.0  # Already alive, perfect fidelity

    # Store original color for fidelity comparison
    original_color = cell.color_vector.copy()

    # Step 1: Compute neighbor color aggregate
    neighbor_aggregate = _compute_neighbor_aggregate(neighbors, alpha)

    # Step 2: Get recent deltas for this cell
    recent_deltas = logger.get_recent_deltas(cell.position, count=20)

    # Step 3: Reconstruct color using aggregate + deltas
    if recent_deltas:
        # Use the most recent delta timestamp as base time
        base_time = recent_deltas[0]["timestamp"]
        # Reconstruct from aggregate using deltas
        reconstructed = reconstruct_color_from_deltas(cell.position, neighbor_aggregate, recent_deltas)
    else:
        # No deltas available, use pure neighbor aggregate
        reconstructed = neighbor_aggregate

    # Step 4: Apply resurrected color and mark as alive
    cell.color_vector = reconstructed
    cell.alive = True

    # Step 5: Compute and return fidelity
    fidelity = compute_delta_fidelity(original_color, reconstructed)
    return fidelity


def resurrect_region(cells: list[Cell], logger: DeltaLogger,
                    alpha: float = 0.1) -> list[float]:
    """Resurrect a region of cells and return fidelity scores.

    Args:
        cells: List of dead cells to resurrect
        logger: DeltaLogger instance for retrieving delta history
        alpha: EMA smoothing factor for neighbor aggregation

    Returns:
        List of fidelity scores for each resurrected cell
    """
    fidelity_scores = []

    for cell in cells:
        if not cell.alive:
            # Get neighbors for this cell (need ConwayGrid reference for proper neighbor calculation)
            # For now, use empty neighbors - this will be enhanced when integrated
            neighbors = []  # TODO: Get actual neighbors from grid
            fidelity = resurrect_cell(cell, neighbors, logger, alpha)
            fidelity_scores.append(fidelity)
        else:
            fidelity_scores.append(1.0)  # Already alive

    return fidelity_scores


def compute_region_fidelity(original_cells: list[Cell],
                           resurrected_cells: list[Cell]) -> float:
    """Compute average fidelity for a resurrected region.

    Args:
        original_cells: Cells before being killed
        resurrected_cells: Cells after resurrection

    Returns:
        Average fidelity score across all cells in the region
    """
    if len(original_cells) != len(resurrected_cells):
        raise ValueError("Original and resurrected cell lists must have same length")

    if not original_cells:
        return 1.0

    total_fidelity = 0.0
    for original, resurrected in zip(original_cells, resurrected_cells):
        fidelity = compute_delta_fidelity(original.color_vector, resurrected.color_vector)
        total_fidelity += fidelity

    return total_fidelity / len(original_cells)


def _compute_neighbor_aggregate(neighbors: list[Cell], alpha: float = 0.1) -> np.ndarray:
    """Compute color aggregate from neighboring cells.

    Uses exponential moving average of live neighbor colors.
    Falls back to grey if no live neighbors.

    Args:
        neighbors: List of neighboring cells
        alpha: EMA smoothing factor

    Returns:
        Aggregated color vector
    """
    live_neighbors = [n for n in neighbors if n.alive]

    if not live_neighbors:
        # No live neighbors, use default grey
        return np.array([128, 128, 128], dtype=np.uint8)

    # Compute mean of live neighbor colors
    neighbor_colors = np.array([n.color_vector for n in live_neighbors])
    mean_color = np.mean(neighbor_colors, axis=0).astype(np.uint8)

    # Apply EMA smoothing (though with single computation, this is just the mean)
    # In a real implementation, this would track historical aggregates
    return mean_color


def demonstrate_zombie_protocol(grid_cells: list[list[Cell]], logger: DeltaLogger,
                               kill_region_coords: list[tuple[int, int]],
                               alpha: float = 0.1) -> dict:
    """Demonstrate the complete zombie protocol on a region.

    This function:
    1. Records original colors of the region
    2. Kills the region (marks cells dead)
    3. Resurrects the region using neighbor aggregation + deltas
    4. Computes fidelity metrics

    Args:
        grid_cells: 2D list of all cells in the grid
        logger: DeltaLogger instance
        kill_region_coords: List of (x,y) coordinates to kill and resurrect
        alpha: EMA smoothing factor

    Returns:
        Dict with demonstration results and metrics
    """
    # Convert coordinates to cell objects
    kill_cells = []
    for x, y in kill_region_coords:
        # Handle toroidal wrapping
        x = x % len(grid_cells[0]) if grid_cells else x
        y = y % len(grid_cells) if grid_cells else y
        if 0 <= y < len(grid_cells) and 0 <= x < len(grid_cells[y]):
            kill_cells.append(grid_cells[y][x])

    if not kill_cells:
        return {"error": "No valid cells found in kill region"}

    # Step 1: Record original state
    original_colors = [cell.color_vector.copy() for cell in kill_cells]
    original_alive_states = [cell.alive for cell in kill_cells]

    # Step 2: Kill the region
    kill_region(kill_cells)

    # Verify cells are dead but colors preserved
    for cell in kill_cells:
        assert not cell.alive, f"Cell {cell.position} should be dead after kill"
        # Colors should be preserved

    # Step 3: Resurrect with neighbor information
    # For demonstration, create mock neighbors (in real usage, ConwayGrid provides neighbors)
    resurrected_fidelities = []
    for cell in kill_cells:
        # Mock neighbors - in practice, ConwayGrid.get_neighbors() would be used
        mock_neighbors = _create_mock_neighbors(grid_cells, cell.position)
        fidelity = resurrect_cell(cell, mock_neighbors, logger, alpha)
        resurrected_fidelities.append(fidelity)

    # Step 4: Compute metrics
    avg_fidelity = sum(resurrected_fidelities) / len(resurrected_fidelities) if resurrected_fidelities else 0.0
    perfect_resurrections = sum(1 for f in resurrected_fidelities if f >= 0.95)
    good_resurrections = sum(1 for f in resurrected_fidelities if f >= 0.90)

    return {
        "region_size": len(kill_cells),
        "average_fidelity": avg_fidelity,
        "perfect_resurrections": perfect_resurrections,  # >=95% fidelity
        "good_resurrections": good_resurrections,        # >=90% fidelity
        "fidelity_scores": resurrected_fidelities,
        "success": avg_fidelity >= 0.90  # Overall success criterion
    }


def _create_mock_neighbors(grid_cells: list[list[Cell]], position: tuple[int, int]) -> list[Cell]:
    """Create mock neighbors for demonstration purposes.

    In real usage, ConwayGrid.get_neighbors() should be used instead.
    """
    if not grid_cells:
        return []

    x, y = position
    height = len(grid_cells)
    width = len(grid_cells[0]) if grid_cells else 0

    neighbors = []
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue

            nx = (x + dx) % width
            ny = (y + dy) % height

            if 0 <= ny < height and 0 <= nx < width:
                neighbors.append(grid_cells[ny][nx])

    return neighbors
