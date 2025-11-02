"""Main entry point for CyberMesh Conway Demo.

This module provides the command-line interface and initializes the Pygame
visualizer for the CyberMesh Conway demonstration.
"""

import argparse
import pathlib
import sys

from .conway import ConwayGrid
from .delta import DeltaLogger
from .visualizer import Visualizer


def main():
    """Main entry point for the CyberMesh Conway Demo."""
    parser = argparse.ArgumentParser(
        description="CyberMesh Conway Demo - Interactive Conway's Game of Life with delta-driven color changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                    # Run with default settings
  python -m src.main --log-dir ./logs   # Specify custom log directory
  python -m src.main --help             # Show this help message

Controls:
  Left Click: Apply current delta to cell (or select for killing in kill mode)
  K Key: Toggle kill mode for region selection
  UI Buttons: Create glider, kill region, resurrect, reset grid
  Sliders: Adjust RGB delta values (-255 to +255)
        """
    )

    parser.add_argument(
        "--log-dir",
        type=pathlib.Path,
        default=pathlib.Path("logs"),
        help="Directory for delta log files (default: logs/)"
    )

    parser.add_argument(
        "--grid-size",
        type=int,
        choices=[8],
        default=8,
        help="Grid size (currently only 8x8 supported)"
    )

    parser.add_argument(
        "--no-auto-step",
        action="store_true",
        help="Disable automatic Conway stepping (manual only)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="CyberMesh Conway Demo v1.0.0"
    )

    args = parser.parse_args()

    # Validate pygame availability
    try:
        import pygame
        import pygame_gui
    except ImportError as e:
        print("Error: pygame is required to run the visualizer.", file=sys.stderr)
        print("Install with: pip install -r requirements-viz.txt", file=sys.stderr)
        print("Or: pip install -e .[visualizer]", file=sys.stderr)
        sys.exit(1)

    try:
        # Create components
        print("Initializing CyberMesh Conway Demo...")
        print(f"Log directory: {args.log_dir}")

        # Ensure log directory exists
        args.log_dir.mkdir(exist_ok=True)

        # Create grid and logger
        grid = ConwayGrid()
        logger = DeltaLogger(log_path=args.log_dir / "delta_log.json")

        # Add initial glider for demonstration
        grid.create_glider(2, 2)
        print("Created initial glider pattern")

        # Create and run visualizer
        visualizer = Visualizer(grid, logger)

        print("Starting visualizer...")
        print("Controls:")
        print("  - Click cells to apply delta (or select for killing)")
        print("  - Press 'K' to toggle kill mode")
        print("  - Use sliders to adjust RGB delta values")
        print("  - Use buttons for glider creation, killing, resurrection")
        print("  - Close window to exit")

        visualizer.run()

        print("Demo completed successfully!")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running demo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
