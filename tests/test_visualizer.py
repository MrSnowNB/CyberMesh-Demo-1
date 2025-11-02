"""Unit tests for visualizer module."""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from src.conway import ConwayGrid
from src.delta import DeltaLogger
import pathlib
import tempfile

# Try to import pygame, skip tests if not available
try:
    import pygame
    import pygame_gui
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None
    pygame_gui = None

from src.visualizer import Visualizer


@pytest.mark.skipif(not PYGAME_AVAILABLE, reason="Pygame not available")
class TestVisualizer:
    """Test cases for Visualizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp())
        self.log_path = self.temp_dir / "test_viz_log.json"

        # Create mock grid and logger
        self.grid = ConwayGrid()
        self.logger = DeltaLogger(log_path=self.log_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_initialization(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test visualizer initialization."""
        # Mock pygame components
        mock_screen = Mock()
        mock_set_mode.return_value = mock_screen
        mock_clock_instance = Mock()
        mock_clock.return_value = mock_clock_instance

        visualizer = Visualizer(self.grid, self.logger)

        # Check basic attributes
        assert visualizer.grid == self.grid
        assert visualizer.logger == self.logger
        assert visualizer.delta_r == 0
        assert visualizer.delta_g == 0
        assert visualizer.delta_b == 0
        assert visualizer.selected_cells == []
        assert not visualizer.kill_mode
        assert visualizer.last_fidelity == 0.0

        # Check window configuration
        assert visualizer.WINDOW_SIZE == (800, 600)
        assert visualizer.GRID_SIZE == 8
        assert visualizer.CELL_SIZE == 64
        assert visualizer.GRID_OFFSET == (50, 50)

    def test_screen_to_grid_conversion(self):
        """Test conversion from screen coordinates to grid coordinates."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer(self.grid, self.logger)

            # Test center of cells
            assert visualizer._screen_to_grid((50 + 32, 50 + 32)) == (0, 0)  # Cell (0,0)
            assert visualizer._screen_to_grid((50 + 96, 50 + 96)) == (1, 1)  # Cell (1,1)
            assert visualizer._screen_to_grid((50 + 512, 50 + 512)) == (8, 8)  # Beyond grid

            # Test edge cases
            assert visualizer._screen_to_grid((50, 50)) == (0, 0)  # Top-left corner
            assert visualizer._screen_to_grid((49, 49)) == (-1, -1)  # Outside grid

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_update_delta_values(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test updating delta values from sliders."""
        # Mock slider objects
        mock_r_slider = Mock()
        mock_r_slider.get_current_value.return_value = 100
        mock_g_slider = Mock()
        mock_g_slider.get_current_value.return_value = -50
        mock_b_slider = Mock()
        mock_b_slider.get_current_value.return_value = 25

        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer(self.grid, self.logger)

            # Manually set slider mocks
            visualizer.delta_r_slider = mock_r_slider
            visualizer.delta_g_slider = mock_g_slider
            visualizer.delta_b_slider = mock_b_slider

            visualizer.update_delta_values()

            assert visualizer.delta_r == 100
            assert visualizer.delta_g == -50
            assert visualizer.delta_b == 25

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_handle_click_normal_mode(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test click handling in normal mode (apply delta)."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'), \
             patch('pygame.time.get_ticks', return_value=1000):

            visualizer = Visualizer(self.grid, self.logger)

            # Set delta values
            visualizer.delta_r = 10
            visualizer.delta_g = 20
            visualizer.delta_b = 30

            # Click on cell (0,0)
            click_pos = (50 + 32, 50 + 32)  # Center of cell (0,0)
            visualizer._handle_click(click_pos)

            # Check that delta was applied to the cell
            cell = visualizer.grid.get_cell(0, 0)
            expected_color = np.array([138, 148, 158], dtype=np.uint8)  # 128 + [10,20,30]
            assert np.array_equal(cell.color_vector, expected_color)

            # Check that it was logged
            assert visualizer.logger.get_log_size() == 1

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_handle_click_kill_mode(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test click handling in kill mode (select cells)."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer(self.grid, self.logger)

            # Enable kill mode
            visualizer.kill_mode = True

            # Click on cell (0,0)
            click_pos = (50 + 32, 50 + 32)
            visualizer._handle_click(click_pos)

            assert (0, 0) in visualizer.selected_cells

            # Click again to deselect
            visualizer._handle_click(click_pos)
            assert (0, 0) not in visualizer.selected_cells

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_handle_ui_events_create_glider(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test UI event handling for create glider button."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer(self.grid, self.logger)

            # Mock button press event
            mock_button = Mock()
            visualizer.create_glider_button = mock_button

            mock_event = Mock()
            mock_event.type = pygame_gui.UI_BUTTON_PRESSED
            mock_event.ui_element = mock_button

            visualizer.handle_ui_events(mock_event)

            # Check that glider was created
            assert visualizer.grid.alive_count == 5  # Glider has 5 cells

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    def test_handle_ui_events_reset(self, mock_font, mock_ui_manager, mock_clock, mock_set_mode, mock_set_caption, mock_init):
        """Test UI event handling for reset button."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer(self.grid, self.logger)

            # Add some state to reset
            visualizer.grid.create_glider(2, 2)
            visualizer.logger.log_delta((0, 0), np.array([1, 0, 0], dtype=np.int8), 1.0, np.array([129, 128, 128], dtype=np.uint8))
            visualizer.selected_cells = [(1, 1), (2, 2)]
            visualizer.kill_mode = True
            visualizer.last_fidelity = 0.95

            # Mock reset button
            mock_button = Mock()
            visualizer.reset_button = mock_button

            mock_event = Mock()
            mock_event.type = pygame_gui.UI_BUTTON_PRESSED
            mock_event.ui_element = mock_button

            visualizer.handle_ui_events(mock_event)

            # Check reset state
            assert visualizer.grid.generation == 0
            assert visualizer.grid.alive_count == 0
            assert visualizer.logger.get_log_size() == 0
            assert visualizer.selected_cells == []
            assert not visualizer.kill_mode
            assert visualizer.last_fidelity == 0.0

    def test_create_demo_visualizer(self):
        """Test demo visualizer creation."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'):

            visualizer = Visualizer.create_demo_visualizer()

            assert isinstance(visualizer, Visualizer)
            assert isinstance(visualizer.grid, ConwayGrid)
            assert isinstance(visualizer.logger, DeltaLogger)
            # Demo should have a glider
            assert visualizer.grid.alive_count == 5


# Integration test that requires pygame display (marked as slow)
@pytest.mark.slow
class TestVisualizerIntegration:
    """Integration tests that require pygame display (run separately)."""

    @pytest.mark.skipif(not PYGAME_AVAILABLE or (pygame and not pygame.display.get_init()), reason="Requires pygame display")
    def test_full_initialization(self):
        """Test full visualizer initialization with pygame display."""
        # This would require a display environment
        # visualizer = Visualizer(ConwayGrid(), DeltaLogger())
        # assert visualizer.screen is not None
        pass
