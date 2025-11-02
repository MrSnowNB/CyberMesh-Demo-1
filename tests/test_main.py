"""Unit tests for main module."""

import pytest
from unittest.mock import patch, Mock
import sys
import pathlib

# Check pygame availability for test skipping
try:
    import pygame
    import pygame_gui
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from src.main import main


@pytest.mark.skipif(not PYGAME_AVAILABLE, reason="Pygame not available")
class TestMain:
    """Test cases for main module functions."""

    def test_main_help(self):
        """Test that main shows help without error."""
        with patch('sys.argv', ['main.py', '--help']), \
             patch('sys.stdout') as mock_stdout, \
             patch('sys.stderr') as mock_stderr, \
             patch('sys.exit') as mock_exit:

            # Should exit with code 0 for --help
            mock_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_main_version(self):
        """Test that main shows version without error."""
        with patch('sys.argv', ['main.py', '--version']), \
             patch('sys.stdout') as mock_stdout, \
             patch('sys.stderr') as mock_stderr, \
             patch('sys.exit') as mock_exit:

            # Should exit with code 0 for --version
            mock_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_main_pygame_missing(self):
        """Test that main exits gracefully when pygame is missing."""
        # Mock import to raise ImportError
        def mock_import(name, *args, **kwargs):
            if name in ['pygame', 'pygame_gui']:
                raise ImportError(f"No module named '{name}'")
            return __builtins__['__import__'](name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import), \
             patch('sys.argv', ['main.py']), \
             patch('sys.stderr') as mock_stderr, \
             patch('sys.exit') as mock_exit:

            mock_exit.side_effect = SystemExit(1)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            # Check that error message was printed
            mock_stderr.write.assert_called()
            error_calls = [call for call in mock_stderr.write.call_args_list
                          if "pygame is required" in str(call)]
            assert len(error_calls) > 0

    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.display.set_caption')
    @patch('pygame.time.Clock')
    @patch('pygame_gui.UIManager')
    @patch('pygame.font.SysFont')
    @patch('pygame.time.get_ticks', return_value=1000)
    def test_main_initialization(self, mock_ticks, mock_font, mock_ui_manager,
                                mock_clock, mock_set_caption, mock_set_mode, mock_init):
        """Test main initialization with mocked pygame."""
        # Mock the visualizer run method to avoid actual pygame loop
        with patch('src.main.Visualizer') as mock_visualizer_class, \
             patch('sys.argv', ['main.py']), \
             patch('sys.stdout') as mock_stdout:

            mock_visualizer = Mock()
            mock_visualizer_class.return_value = mock_visualizer

            # Mock successful run (doesn't hang)
            mock_visualizer.run.return_value = None

            # Should complete without error
            main()

            # Check that visualizer was created and run
            mock_visualizer_class.assert_called_once()
            mock_visualizer.run.assert_called_once()

            # Check that initialization messages were printed
            stdout_calls = mock_stdout.write.call_args_list
            init_messages = [call for call in stdout_calls if "Initializing" in str(call)]
            assert len(init_messages) > 0

    def test_main_custom_log_dir(self):
        """Test main with custom log directory."""
        custom_log_dir = pathlib.Path("custom_logs")

        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame_gui.UIManager'), \
             patch('pygame.font.SysFont'), \
             patch('pygame.time.get_ticks', return_value=1000), \
             patch('src.main.Visualizer') as mock_visualizer_class, \
             patch('sys.argv', ['main.py', '--log-dir', str(custom_log_dir)]), \
             patch('sys.stdout'):

            mock_visualizer = Mock()
            mock_visualizer_class.return_value = mock_visualizer
            mock_visualizer.run.return_value = None

            main()

            # Check that DeltaLogger was created with custom path
            from src.delta import DeltaLogger
            from src.conway import ConwayGrid

            # The visualizer constructor should have been called with a logger
            # that has the custom log path
            call_args = mock_visualizer_class.call_args
            grid_arg, logger_arg = call_args[0]

            assert isinstance(grid_arg, ConwayGrid)
            assert isinstance(logger_arg, DeltaLogger)
            assert str(custom_log_dir) in str(logger_arg.log_path) or str(logger_arg.log_path).startswith(str(custom_log_dir))
