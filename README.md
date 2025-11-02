# CyberMesh Conway Demo

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Conway's Game of Life with delta-driven color changes, demonstrating CyberMesh 3-tier memory module capabilities without simulation.

## 🎯 Features

- **8×8 Toroidal Grid**: Conway's Game of Life with seamless boundary wrapping
- **Delta-Driven Colors**: Apply RGB deltas to cells with real-time visualization
- **Interactive UI**: Click cells to paint, adjust delta tuner, create patterns
- **CyberMesh Memory**: Kill regions and resurrect with >90% color fidelity
- **Delta Logging**: Complete audit trail of all color changes
- **60-Second Demo**: Automated showcase of all capabilities

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10 or 3.11
- **System Dependencies**:
  - macOS: `brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf`
  - Ubuntu: `sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev`
  - Windows WSL2: SDL2 libraries (included in WSL Ubuntu packages)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MrSnowNB/CyberMesh-Demo-1.git
   cd CyberMesh-Demo-1
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # OR
   venv\Scripts\activate.bat  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Validate setup**
   ```bash
   python -c "import pygame; pygame.init(); print('✅ Pygame OK')"
   pytest tests/ -q  # If tests exist
   ```

### Running the Demo

```bash
python src/main.py
```

**Controls:**
- **Create Glider**: Click button to spawn green glider pattern
- **Delta Tuner**: Adjust RGB sliders (-255 to +255)
- **Paint Mode**: Click any cell to apply current delta
- **Kill Region**: Drag to select area, click "Kill Region"
- **Resurrect**: Click "Resurrect" to reconstruct colors from neighbors + delta history
- **Exit**: Close window or press Ctrl+C

## 📊 Success Criteria

- ✅ Grid initializes with grey cells (R=128, G=128, B=128)
- ✅ Conway B3/S23 rules execute correctly on toroidal grid
- ✅ "Create Glider" applies green delta (+0, +100, +0) to cells
- ✅ Delta tuner allows user adjustment of [ΔR, ΔG, ΔB]
- ✅ Click cells to apply current delta values
- ✅ Delta log (`logs/delta_log.json`) records every operation with timestamp
- ✅ Kill region → Resurrect from neighbor aggregate + delta log
- ✅ Fidelity meter shows >90% color reconstruction accuracy
- ✅ 60-second demo video demonstrates all features

## 🏗️ Project Structure

```
cybermesh-conway-demo/
├── src/                    # Source code
│   ├── cell.py            # Cell class with color vectors
│   ├── conway.py          # Conway rules + toroidal grid
│   ├── delta.py           # Delta operations + logging
│   ├── zombie.py          # Kill/resurrect logic
│   ├── visualizer.py      # Pygame UI
│   └── main.py            # Entry point
├── tests/                 # Unit tests
├── logs/                  # Runtime delta logs
├── demo/                  # Demo video output
├── PROJECT-PLAN.md        # Detailed project plan
├── REPLICATION-NOTES.md   # Setup instructions
├── TASK-LOG.md           # Atomic task tracking
├── TROUBLESHOOTING.md    # Known issues + fixes
└── requirements.txt      # Python dependencies
```

## 🧪 Development

### Validation Gates

```bash
# Unit tests
pytest tests/ -v --cov=src

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Manual testing (see TASK-LOG.md Task 3.3)
```

### Pre-flight Validation

Run before development sessions:
```bash
chmod +x validate_setup.sh
./validate_setup.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run validation: `pytest && ruff check && mypy`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Conway's Game of Life - John Horton Conway
- CyberMesh 3-tier memory architecture
- Pygame community for the excellent SDL2 bindings

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/MrSnowNB/CyberMesh-Demo-1/issues)
- **Documentation**: See `PROJECT-PLAN.md`, `REPLICATION-NOTES.md`, `TROUBLESHOOTING.md`

---

**Status**: Planning Phase Complete - Ready for Build Phase
**Version**: 1.0.0
**Maintainer**: Mark Snow Jr.
