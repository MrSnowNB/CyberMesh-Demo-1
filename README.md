# CyberMesh Conway Demo

Interactive Conway's Game of Life with delta-driven color changes demonstrating CyberMesh 3-tier memory resurrection.

## Features

- **Conway's Game of Life**: Classic cellular automaton with B3/S23 rules
- **Color Manipulation**: Apply RGB deltas to cells for visual effects
- **CyberMesh Memory**: Perfect resurrection of killed cells using delta reconstruction
- **Interactive UI**: Real-time visualization with pygame
- **Delta Logging**: Atomic JSON logging of all operations

## Installation

### Core Installation (Required)
```bash
pip install -r requirements.txt
```

### With Visualization (Recommended)
```bash
pip install -r requirements-viz.txt
# Or with pip-tools
pip install -e .[visualizer]
```

### Development Installation (Full)
```bash
pip install -r requirements-dev.txt
# Or with pip-tools
pip install -e .[full]
```

## Usage

### Basic Usage
```bash
python -m src.main
```

### Custom Log Directory
```bash
python -m src.main --log-dir ./my_logs
```

### Help
```bash
python -m src.main --help
```

## Controls

- **Left Click**: Apply current delta to cell (or select for killing in kill mode)
- **K Key**: Toggle kill mode for region selection
- **UI Sliders**: Adjust RGB delta values (-255 to +255)
- **Buttons**:
  - Create Glider: Add glider pattern
  - Kill Region: Kill selected cells
  - Resurrect: Restore killed cells using CyberMesh memory
  - Reset Grid: Clear and restart

## Architecture

### Core Components
- `src/cell.py`: Individual cell with color and delta operations
- `src/conway.py`: 8×8 toroidal grid with Game of Life rules
- `src/delta.py`: Atomic JSON logging system
- `src/zombie.py`: CyberMesh memory resurrection protocol
- `src/visualizer.py`: Pygame interactive UI (optional)
- `src/main.py`: Command-line interface

### CyberMesh Memory System
1. **Delta Logging**: Every color change is logged atomically
2. **Kill Operation**: Cells marked dead but colors preserved
3. **Resurrection**: Neighbor aggregation + delta reconstruction
4. **Fidelity Tracking**: Cosine similarity measurement of success

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
ruff check src/ tests/
mypy src/
```

## Dependencies

### Required
- numpy: Array operations and color vectors

### Optional
- pygame: Interactive visualization
- pygame-gui: UI components for visualizer

### Development
- pytest: Unit testing
- ruff: Linting and formatting
- mypy: Type checking

## License

MIT License - see project files for details.
