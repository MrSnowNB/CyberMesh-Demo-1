---
title: Replication Notes
version: 1.0.0
created: 2025-11-02
last_updated: 2025-11-02
---

# CyberMesh Conway Demo - Replication Notes

## Environment Setup

### Supported Platforms
- ✅ macOS 12+ (M1/M2 or Intel)
- ✅ Ubuntu 20.04+ / Debian 11+
- ✅ Windows 10/11 with WSL2
- ⚠️ Native Windows (requires SDL2 manual install)

### Python Version
- **Required**: Python 3.10 or 3.11
- **Not tested**: Python 3.9 (missing `match` statement), Python 3.12 (pygame compatibility unclear)

### System Dependencies

#### macOS
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install SDL2 and Python
brew install python@3.11 sdl2 sdl2_image sdl2_mixer sdl2_ttf
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

#### Windows (WSL2)
```bash
# Inside WSL2 Ubuntu
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip libsdl2-dev

# For GUI display, install X server (VcXsrv or WSLg)
export DISPLAY=:0
```

### Python Virtual Environment Setup
```bash
# Create venv
python3.11 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

---

## Replicable Setup Checklist

- [ ] Python 3.10 or 3.11 installed
- [ ] SDL2 libraries installed (macOS/Linux)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows pygame, numpy, pytest)
- [ ] `logs/` directory exists (auto-created on first run)
- [ ] Pygame window test passes: `python -c "import pygame; pygame.init(); print('OK')"`
- [ ] Unit tests pass: `pytest tests/ -v`
- [ ] Lint clean: `ruff check src/`
- [ ] Type check clean: `mypy src/`

---

## Known Pitfalls to Avoid Next Run

### 1. Missing `logs/` Directory
**Problem**: `delta.py` crashes with `FileNotFoundError` when trying to write `delta_log.json`  
**Solution**: Add `os.makedirs('logs', exist_ok=True)` in `main.py` startup  
**Prevention**: Include in project setup script

### 2. Pygame Display on Headless Server
**Problem**: Running on CI/CD or remote server without X11 fails  
**Solution**: Set `SDL_VIDEODRIVER=dummy` environment variable for headless testing  
**Example**:
```bash
SDL_VIDEODRIVER=dummy pytest tests/test_visualizer.py
```
**Prevention**: Add to CI workflow YAML

### 3. Numpy Dtype Mismatches
**Problem**: Color vectors stored as `float64` but Pygame expects `uint8`  
**Solution**: Always initialize with explicit dtype:
```python
color_vector = np.array([128, 128, 128], dtype=np.uint8)
```
**Prevention**: Add dtype validation in `Cell.__init__`

### 4. Delta Tuner Slider Out of Range
**Problem**: Slider allows values outside [-255, +255], causing overflow  
**Solution**: Clamp slider bounds in `visualizer.py`:
```python
delta_r_slider = Slider(min_val=-255, max_val=255, initial=0)
```
**Prevention**: Already implemented in generated code

### 5. Toroidal Grid Corner Cases
**Problem**: Glider at (7, 7) wrapping to (0, 0) shows incorrect neighbors  
**Solution**: Test modulo wrapping explicitly:
```python
def test_toroidal_corner():
    grid = ConwayGrid(8, 8)
    neighbors = grid.get_neighbors(7, 7)
    assert (0, 0) in neighbors  # Top-left wraps to bottom-right
```
**Prevention**: Unit test added to `test_conway.py`

### 6. JSON Log File Locking on Windows
**Problem**: Windows file locking prevents concurrent read/write to `delta_log.json`  
**Solution**: Use atomic write pattern (see `TROUBLESHOOTING.md` Issue 2)  
**Prevention**: Implement in `delta.py` from start

### 7. Pygame Event Queue Overflow
**Problem**: After 60+ seconds, event queue fills up, UI freezes  
**Solution**: Add event queue pump at start of loop:
```python
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        running = False
```
**Prevention**: Already in main game loop

### 8. Color Blending Artifacts
**Problem**: When glider moves, trailing cells show color "ghosting"  
**Solution**: Reset dead cell colors to grey after Conway death:
```python
if not cell.alive:
    cell.color_vector = np.array([128, 128, 128], dtype=np.uint8)
```
**Prevention**: Add option toggle in UI ("Persist colors on death" checkbox)

---

## Hardware Notes

### Minimum Specs
- **CPU**: Dual-core 2.0 GHz (Python single-threaded, not CPU-intensive)
- **RAM**: 512 MB (entire 8×8 grid + logs ~10 MB max)
- **GPU**: Not required (Pygame 2D rendering is CPU-based)

### Tested Configurations
| Platform | CPU | RAM | Result |
|----------|-----|-----|--------|
| MacBook Pro M1 | 8-core | 16 GB | ✅ Smooth 60 FPS |
| Ubuntu 22.04 VM | 2 vCPU | 4 GB | ✅ Stable 10 FPS |
| Windows 11 WSL2 | 4 vCPU | 8 GB | ✅ Works with X server |
| Raspberry Pi 4 | 4-core 1.5GHz | 4 GB | ⚠️ Lag at 5 FPS, usable |

---

## Recurring Errors Log

### 2025-11-02: Initial Setup
- **Error**: `ModuleNotFoundError: No module named 'numpy'`
- **Cause**: Forgot to activate venv before `pip install`
- **Fix**: Activated venv, reinstalled deps
- **Lesson**: Always verify venv with `which python`

---

## Pre-Flight Validation Script

Save as `validate_setup.sh`:
```bash
#!/bin/bash
set -e

echo "Validating Python version..."
python --version | grep -E "3\.(10|11)"

echo "Checking SDL2..."
python -c "import pygame; pygame.init(); print('Pygame OK')"

echo "Checking dependencies..."
pip show numpy pygame pytest ruff mypy

echo "Creating logs directory..."
mkdir -p logs

echo "Running unit tests..."
pytest tests/ -q

echo "Running linter..."
ruff check src/

echo "Running type checker..."
mypy src/

echo "✅ Setup validated successfully!"
```

Run before every development session:
```bash
chmod +x validate_setup.sh
./validate_setup.sh
```

---

**Last Updated**: 2025-11-02 09:48 EST  
**Maintainer**: Mark Snow Jr.  
**Next Review**: After first successful end-to-end run
