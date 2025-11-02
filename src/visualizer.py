"""Pygame visualizer module for CyberMesh Conway Demo.

This module implements the interactive Pygame-based UI for the CyberMesh Conway Demo,
providing real-time visualization of the Conway grid with color manipulation capabilities.
"""

from typing import Optional, Tuple, List

from .conway import ConwayGrid
from .delta import DeltaLogger
from .zombie import demonstrate_zombie_protocol

# Import pygame modules (optional dependency)
try:
    import pygame
    import pygame_gui
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None
    pygame_gui = None


class Visualizer:
    """Pygame-based interactive visualizer for CyberMesh Conway Demo.

    Provides a complete UI for Conway's Game of Life with delta-driven color manipulation,
    including real-time grid rendering, interactive controls, and CyberMesh resurrection.
    """

    # Window configuration
    WINDOW_SIZE = (800, 600)
    GRID_SIZE = 8
    CELL_SIZE = 64  # 64x64 pixels per cell
    GRID_OFFSET = (50, 50)  # Top-left corner of grid

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREY = (128, 128, 128)
    DARK_GREY = (64, 64, 64)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    def __init__(self, grid: ConwayGrid, logger: DeltaLogger):
        """Initialize the Pygame visualizer.

        Args:
            grid: ConwayGrid instance to visualize
            logger: DeltaLogger for tracking operations
        """
        pygame.init()
        pygame.display.set_caption("CyberMesh Conway Demo")

        self.grid = grid
        self.logger = logger

        # Create window
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        self.clock = pygame.time.Clock()

        # UI Manager for pygame_gui
        self.ui_manager = pygame_gui.UIManager(self.WINDOW_SIZE)

        # Delta tuner values (-255 to +255)
        self.delta_r = 0
        self.delta_g = 0
        self.delta_b = 0

        # UI state
        self.selected_cells: List[Tuple[int, int]] = []
        self.kill_mode = False
        self.last_fidelity = 0.0

        # Create UI elements
        self._create_ui_elements()

        # Font for text rendering
        self.font = pygame.font.SysFont('Arial', 16)
        self.small_font = pygame.font.SysFont('Arial', 12)

    def _create_ui_elements(self):
        """Create all UI elements (sliders, buttons, etc.)."""
        # Delta tuner sliders
        self.delta_r_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(550, 50, 200, 30),
            start_value=0, value_range=(-255, 255),
            manager=self.ui_manager
        )
        self.delta_r_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(550, 20, 200, 25),
            text="ΔR (Red)",
            manager=self.ui_manager
        )

        self.delta_g_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(550, 100, 200, 30),
            start_value=0, value_range=(-255, 255),
            manager=self.ui_manager
        )
        self.delta_g_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(550, 70, 200, 25),
            text="ΔG (Green)",
            manager=self.ui_manager
        )

        self.delta_b_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(550, 150, 200, 30),
            start_value=0, value_range=(-255, 255),
            manager=self.ui_manager
        )
        self.delta_b_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(550, 120, 200, 25),
            text="ΔB (Blue)",
            manager=self.ui_manager
        )

        # Control buttons
        self.create_glider_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(550, 200, 200, 40),
            text="Create Glider",
            manager=self.ui_manager
        )

        self.kill_region_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(550, 250, 200, 40),
            text="Kill Region",
            manager=self.ui_manager
        )

        self.resurrect_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(550, 300, 200, 40),
            text="Resurrect",
            manager=self.ui_manager
        )

        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(550, 350, 200, 40),
            text="Reset Grid",
            manager=self.ui_manager
        )

    def run(self):
        """Main visualization loop."""
        running = True
        step_timer = 0
        STEP_INTERVAL = 100  # milliseconds between Conway steps

        while running:
            time_delta = self.clock.tick(60) / 1000.0  # 60 FPS
            step_timer += time_delta * 1000

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self._handle_click(event.pos)

                # Pass events to UI manager
                self.ui_manager.process_events(event)

            # Update UI
            self.ui_manager.update(time_delta)

            # Auto-step Conway every STEP_INTERVAL milliseconds
            if step_timer >= STEP_INTERVAL:
                self.grid.step()
                step_timer = 0

            # Render everything
            self._render()

            # Update display
            pygame.display.flip()

        pygame.quit()

    def _handle_click(self, pos: Tuple[int, int]):
        """Handle mouse click at given position."""
        grid_x, grid_y = self._screen_to_grid(pos)

        if 0 <= grid_x < self.GRID_SIZE and 0 <= grid_y < self.GRID_SIZE:
            if self.kill_mode:
                # Add to selection for killing
                cell_pos = (grid_x, grid_y)
                if cell_pos in self.selected_cells:
                    self.selected_cells.remove(cell_pos)
                else:
                    self.selected_cells.append(cell_pos)
            else:
                # Apply current delta to clicked cell
                cell = self.grid.get_cell(grid_x, grid_y)
                import numpy as np
                delta = np.array([self.delta_r, self.delta_g, self.delta_b], dtype=np.int8)
                cell.apply_delta(delta)
                self.logger.log_delta(cell.position, delta, pygame.time.get_ticks() / 1000.0, cell.color_vector)

    def _screen_to_grid(self, screen_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert screen coordinates to grid coordinates."""
        screen_x, screen_y = screen_pos
        grid_x = (screen_x - self.GRID_OFFSET[0]) // self.CELL_SIZE
        grid_y = (screen_y - self.GRID_OFFSET[1]) // self.CELL_SIZE
        return grid_x, grid_y

    def _render(self):
        """Render the entire visualization."""
        self.screen.fill(self.BLACK)

        # Render grid
        self._render_grid()

        # Render UI elements
        self.ui_manager.draw_ui(self.screen)

        # Render status overlay
        self._render_status_overlay()

        # Render selected cells (for kill mode)
        if self.kill_mode:
            self._render_selection_overlay()

    def _render_grid(self):
        """Render the 8×8 Conway grid with cell colors."""
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                cell = self.grid.cells[y][x]

                # Cell rectangle
                rect_x = self.GRID_OFFSET[0] + x * self.CELL_SIZE
                rect_y = self.GRID_OFFSET[1] + y * self.CELL_SIZE
                rect = pygame.Rect(rect_x, rect_y, self.CELL_SIZE, self.CELL_SIZE)

                # Cell color (RGB from numpy array)
                color = tuple(cell.color_vector)

                # Add border for alive cells
                if cell.alive:
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, self.WHITE, rect, 2)  # White border
                else:
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, self.DARK_GREY, rect, 1)  # Subtle border

    def _render_status_overlay(self):
        """Render status information overlay."""
        # Background for status area
        status_rect = pygame.Rect(50, 550, 700, 40)
        pygame.draw.rect(self.screen, self.DARK_GREY, status_rect)
        pygame.draw.rect(self.screen, self.WHITE, status_rect, 1)

        # Status text
        status_text = (
            f"Gen: {self.grid.generation} | "
            f"Alive: {self.grid.alive_count} | "
            f"Log Size: {self.logger.get_log_size()} | "
            ".2f"
        )

        text_surface = self.font.render(status_text, True, self.WHITE)
        self.screen.blit(text_surface, (60, 560))

        # Delta preview
        delta_text = f"Current Δ: ({self.delta_r}, {self.delta_g}, {self.delta_b})"
        delta_surface = self.small_font.render(delta_text, True, self.GREY)
        self.screen.blit(delta_surface, (550, 400))

        # Instructions
        if self.kill_mode:
            instr_text = "KILL MODE: Click cells to select region, then click 'Kill Region'"
        else:
            instr_text = "Click cells to apply current delta | Hold for kill mode"

        instr_surface = self.small_font.render(instr_text, True, self.GREY)
        self.screen.blit(instr_surface, (50, 525))

    def _render_selection_overlay(self):
        """Render overlay showing selected cells for killing."""
        for x, y in self.selected_cells:
            rect_x = self.GRID_OFFSET[0] + x * self.CELL_SIZE
            rect_y = self.GRID_OFFSET[1] + y * self.CELL_SIZE
            rect = pygame.Rect(rect_x, rect_y, self.CELL_SIZE, self.CELL_SIZE)

            # Red overlay for selected cells
            overlay = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE))
            overlay.set_alpha(128)  # Semi-transparent
            overlay.fill(self.RED)
            self.screen.blit(overlay, (rect_x, rect_y))

    def update_delta_values(self):
        """Update delta values from slider positions."""
        self.delta_r = int(self.delta_r_slider.get_current_value())
        self.delta_g = int(self.delta_g_slider.get_current_value())
        self.delta_b = int(self.delta_b_slider.get_current_value())

    def handle_ui_events(self, event):
        """Handle pygame_gui events."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.create_glider_button:
                self.grid.create_glider(2, 2)  # Create glider in center area

            elif event.ui_element == self.kill_region_button:
                if self.selected_cells:
                    # Convert coordinates to cell objects
                    cells_to_kill = []
                    for x, y in self.selected_cells:
                        cells_to_kill.append(self.grid.get_cell(x, y))

                    # Demonstrate zombie protocol
                    result = demonstrate_zombie_protocol(
                        self.grid.cells, self.logger, self.selected_cells
                    )
                    self.last_fidelity = result.get("average_fidelity", 0.0)

                    # Clear selection
                    self.selected_cells = []
                    self.kill_mode = False

            elif event.ui_element == self.resurrect_button:
                # Resurrect any dead cells in the grid (simple resurrection)
                for row in self.grid.cells:
                    for cell in row:
                        if not cell.alive:
                            # Simple resurrection with grey color
                            cell.alive = True
                            cell.reset_color()

            elif event.ui_element == self.reset_button:
                self.grid.reset()
                self.logger.clear_log()
                self.selected_cells = []
                self.kill_mode = False
                self.last_fidelity = 0.0

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:  # 'K' key toggles kill mode
                self.kill_mode = not self.kill_mode
                self.selected_cells = []


def create_demo_visualizer() -> Visualizer:
    """Create a visualizer with demo grid and logger for testing."""
    from .conway import ConwayGrid
    from .delta import DeltaLogger
    import tempfile
    import pathlib

    # Create temp logger
    temp_dir = pathlib.Path(tempfile.mkdtemp())
    logger = DeltaLogger(log_path=temp_dir / "demo_log.json")

    # Create grid with some initial pattern
    grid = ConwayGrid()
    grid.create_glider(2, 2)  # Add a glider

    return Visualizer(grid, logger)


if __name__ == "__main__":
    # Demo mode
    visualizer = create_demo_visualizer()
    visualizer.run()
