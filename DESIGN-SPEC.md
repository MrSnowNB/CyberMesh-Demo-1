---
title: Core Data Structures Design Specification
version: 1.0.0
created: 2025-11-02
last_updated: 2025-11-02
---

# CyberMesh Conway Demo - Core Data Structures Design

## Overview

This document specifies the core data structures for the CyberMesh Conway Demo, ensuring type safety, performance, and clear interfaces between modules.

## 1. Cell Class (`src/cell.py`)

### Schema

```python
class Cell:
    """Represents a single cell in the Conway grid with color state."""

    # Core attributes
    alive: bool
    position: tuple[int, int]  # (x, y) coordinates, 0-7 range
    color_vector: np.ndarray[np.uint8]  # Shape: (3,) - [R, G, B]

    # CyberMesh memory attributes
    ema_aggregate: np.ndarray[np.uint8]  # Exponential moving average of neighbor colors
    last_updated: float  # Timestamp of last delta application

    def __init__(self, x: int, y: int) -> None:
        """Initialize cell at position (x,y) with default grey color."""
        pass

    def apply_delta(self, delta: np.ndarray[np.int8]) -> None:
        """Apply RGB delta to color_vector with clipping to [0, 255]."""
        pass

    def reset_color(self) -> None:
        """Reset color to default grey (128, 128, 128)."""
        pass

    def __repr__(self) -> str:
        """Debug representation: Cell(3,4,alive=True,[128,128,128])."""
        pass
```

### Constraints

- **Color Range**: All RGB values ∈ [0, 255]
- **Position Range**: x, y ∈ [0, 7]
- **Delta Range**: ΔR, ΔG, ΔB ∈ [-255, +255] (applied with clipping)
- **Memory**: ~64 bytes per cell (bool + tuple + 3×uint8 + 3×uint8 + float)

### Invariants

- `color_vector` always has dtype `np.uint8`
- `ema_aggregate` always has dtype `np.uint8`
- Position coordinates never change after initialization
- Color values are always clipped to valid range

## 2. Conway Grid Class (`src/conway.py`)

### Schema

```python
class ConwayGrid:
    """8×8 toroidal Conway's Game of Life grid."""

    # Core attributes
    width: int = 8
    height: int = 8
    cells: list[list[Cell]]  # 8×8 grid

    # Game state
    generation: int = 0
    alive_count: int = 0

    def __init__(self) -> None:
        """Initialize 8×8 grid with all cells dead and grey."""
        pass

    def step(self) -> None:
        """Execute one Conway generation (B3/S23 rules)."""
        pass

    def get_neighbors(self, x: int, y: int) -> list[Cell]:
        """Return Moore neighborhood (8 cells) with toroidal wrapping."""
        pass

    def get_cell(self, x: int, y: int) -> Cell:
        """Get cell at (x,y) with toroidal wrapping."""
        pass

    def reset(self) -> None:
        """Reset all cells to dead state with grey color."""
        pass

    def create_glider(self, x: int, y: int) -> None:
        """Create glider pattern centered at (x,y) with green delta."""
        pass

    def kill_region(self, cells: list[Cell]) -> None:
        """Mark cells as dead, preserve colors for resurrection."""
        pass
```

### Conway Rules (B3/S23)

- **Birth (B3)**: Dead cell becomes alive if exactly 3 live neighbors
- **Survival (S23)**: Live cell stays alive if 2 or 3 live neighbors
- **Death**: All other cases result in dead cell

### Toroidal Wrapping

```python
def toroidal_coord(coord: int) -> int:
    """Convert coordinate to toroidal range [0, 7]."""
    return coord % 8
```

### Neighbor Topology (Moore 3×3)

```
Cell at (x,y) has 8 neighbors:
(x-1,y-1) (x-1,y) (x-1,y+1)
(x,  y-1)    .    (x,  y+1)
(x+1,y-1) (x+1,y) (x+1,y+1)
```

All coordinates wrapped toroidally.

## 3. Delta Operations (`src/delta.py`)

### Schema

```python
class DeltaLogger:
    """Atomic JSON logging of all delta operations."""

    # Configuration
    log_path: pathlib.Path = pathlib.Path("logs/delta_log.json")
    max_entries: int = 1000

    # State
    entries: list[dict] = []

    def __init__(self) -> None:
        """Load existing log or create empty."""
        pass

    def log_delta(self, cell_id: tuple[int, int],
                  delta: np.ndarray[np.int8],
                  timestamp: float) -> None:
        """Append delta operation to log with atomic write."""
        pass

    def get_recent_deltas(self, cell_id: tuple[int, int],
                         count: int = 10) -> list[dict]:
        """Return last N delta operations for cell."""
        pass

    def clear_log(self) -> None:
        """Reset delta log (for testing)."""
        pass

def apply_delta_to_cells(cells: list[Cell],
                        delta: np.ndarray[np.int8],
                        logger: DeltaLogger) -> None:
    """Apply delta to multiple cells with logging."""
    pass
```

### Delta Log JSON Schema

```json
{
  "version": "1.0.0",
  "entries": [
    {
      "timestamp": 1730572800.123,
      "cell_id": [3, 4],
      "delta": [0, 100, 0],
      "result_color": [128, 228, 128]
    }
  ]
}
```

### Atomic Write Pattern

```python
def atomic_json_write(data: dict, filepath: pathlib.Path) -> None:
    """Write JSON atomically to prevent corruption."""
    fd, temp_path = tempfile.mkstemp(dir=filepath.parent)
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, filepath)
```

## 4. Zombie Protocol (`src/zombie.py`)

### Schema

```python
def compute_neighbor_aggregate(cell: Cell, neighbors: list[Cell]) -> np.ndarray[np.uint8]:
    """Compute color aggregate from live neighbors."""
    pass

def resurrect_cell(cell: Cell, neighbors: list[Cell], logger: DeltaLogger) -> float:
    """Resurrect dead cell using neighbor aggregate + delta history.

    Returns: fidelity score (0.0 to 1.0)
    """
    pass

def compute_fidelity(original: np.ndarray[np.uint8],
                    reconstructed: np.ndarray[np.uint8]) -> float:
    """Cosine similarity between original and reconstructed colors."""
    pass
```

### Resurrection Algorithm

1. **Neighbor Aggregate**: Mean color of all 8 neighbors (weighted by distance?)
2. **Delta Reconstruction**: Apply recent deltas for this cell from log
3. **Fidelity Check**: Cosine similarity between original and reconstructed colors
4. **Threshold**: >90% fidelity required for success

### Cosine Similarity Formula

```python
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity ∈ [0, 1]."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot_product / (norm_a * norm_b)
```

## 5. Visualizer Interface (`src/visualizer.py`)

### Schema

```python
class Visualizer:
    """Pygame-based UI for Conway grid interaction."""

    # Configuration
    window_size: tuple[int, int] = (800, 600)
    grid_size: int = 8
    cell_size: int = 64  # 64×64 pixels per cell

    # UI State
    delta_tuner: tuple[int, int, int] = (0, 0, 0)  # Current ΔR, ΔG, ΔB
    selected_cells: set[tuple[int, int]] = set()
    kill_mode: bool = False

    def __init__(self, grid: ConwayGrid) -> None:
        """Initialize Pygame window and UI elements."""
        pass

    def render(self) -> None:
        """Draw grid, UI controls, and status overlay."""
        pass

    def handle_click(self, pos: tuple[int, int]) -> None:
        """Process mouse click at pixel position."""
        pass

    def update_delta_tuner(self, delta: tuple[int, int, int]) -> None:
        """Update current delta values from UI sliders."""
        pass

    def get_fidelity_display(self) -> str:
        """Return fidelity percentage string for UI."""
        pass
```

### UI Layout

```
┌─────────────────────────────────────┐
│ Conway Grid (512×512)    Status:   │
│ ┌─────────────────────┐  Gen: 42   │
│ │ 8×8 Cell Grid       │  Alive: 23 │
│ │                     │  Fidelity: │
│ │                     │  94.2%     │
│ └─────────────────────┘             │
├─────────────────────────────────────┤
│ Delta Tuner:                        │
│ R: ░░░░░░░░ 0    G: ░░░░░░░░ 0      │
│ B: ░░░░░░░░ 0                       │
│                                     │
│ [Create Glider] [Kill Region] [Resurrect] │
└─────────────────────────────────────┘
```

## 6. Main Entry Point (`src/main.py`)

### Schema

```python
def main() -> None:
    """Initialize and run the CyberMesh Conway Demo."""

    # Initialize components
    grid = ConwayGrid()
    logger = DeltaLogger()
    visualizer = Visualizer(grid)

    # Create logs directory
    pathlib.Path("logs").mkdir(exist_ok=True)

    # Main game loop
    clock = pygame.time.Clock()
    running = True

    while running:
        # Cap at 10 FPS
        clock.tick(10)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                visualizer.handle_click(event.pos)

        # Conway step
        grid.step()

        # Render
        visualizer.render()
        pygame.display.flip()

    # Cleanup
    pygame.quit()
```

## 7. Type Definitions

### Common Types

```python
from typing import TypeAlias

ColorVector: TypeAlias = np.ndarray[np.uint8]  # Shape: (3,)
DeltaVector: TypeAlias = np.ndarray[np.int8]   # Shape: (3,)
CellID: TypeAlias = tuple[int, int]           # (x, y) coordinates
Timestamp: TypeAlias = float                   # Unix timestamp
```

### NumPy Type Hints

```python
import numpy.typing as npt

color_vector: npt.NDArray[np.uint8]
delta_vector: npt.NDArray[np.int8]
```

## 8. Memory and Performance Budget

### Per-Frame Budget

- **Target FPS**: 10 (100ms per frame)
- **Conway Step**: <10ms (8×8 grid, simple rules)
- **Rendering**: <20ms (512×512 pixels)
- **UI Updates**: <5ms
- **Logging**: <5ms (atomic writes)
- **Buffer**: 60ms for variability

### Memory Usage

- **Grid**: 8×8×64 bytes = ~4KB
- **Delta Log**: 1000×~100 bytes = ~100KB
- **Pygame Surfaces**: ~1MB
- **Total**: <2MB (well within limits)

## 9. Error Handling

### Expected Exceptions

- `FileNotFoundError`: Missing logs directory (create automatically)
- `json.JSONDecodeError`: Corrupted delta log (reset to empty)
- `pygame.error`: SDL2 initialization failure (graceful exit with message)
- `IndexError`: Invalid coordinates (clamp to valid range)

### Validation Functions

```python
def validate_color_vector(color: np.ndarray) -> bool:
    """Return True if color is valid uint8 array."""
    return (color.dtype == np.uint8 and
            color.shape == (3,) and
            np.all((color >= 0) & (color <= 255)))

def validate_coordinates(x: int, y: int) -> bool:
    """Return True if coordinates are in [0, 7]."""
    return 0 <= x < 8 and 0 <= y < 8
```

---

## Validation Checklist

- [ ] Cell class schema matches implementation requirements
- [ ] Conway rules correctly specified (B3/S23)
- [ ] Toroidal wrapping defined for all edge cases
- [ ] Delta log JSON schema complete with all fields
- [ ] Zombie resurrection algorithm clearly defined
- [ ] UI layout matches success criteria
- [ ] Type hints comprehensive and correct
- [ ] Memory/performance budgets realistic
- [ ] Error handling covers known failure modes

---

**Status**: Ready for implementation
**Next**: Generate source files (`cell.py`, `conway.py`, etc.)
**Maintainer**: Mark Snow Jr.
**Version**: 1.0.0
