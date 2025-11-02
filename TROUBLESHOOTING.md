---
title: Troubleshooting Guide
version: 1.0.0
created: 2025-11-02
last_updated: 2025-11-02
---

# CyberMesh Conway Demo - Troubleshooting

## Known Issues & Fixes

### Issue 1: Pygame Window Not Rendering
**Context**: Running `python src/main.py` on macOS or Linux  
**Symptom**: Black screen or no window appears  
**Error Snippet**:
```
pygame.error: No available video device
```
**Probable Cause**: Missing SDL2 libraries or running in headless environment  
**Quick Fix**:
```bash
# macOS
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

# Ubuntu/Debian
sudo apt-get install python3-pygame libsdl2-dev
```
**Permanent Fix**: Add dependency check in `main.py` startup with clear error message  
**Prevention**: Document SDL2 requirement in `REPLICATION-NOTES.md`, add to CI pre-flight checks

---

### Issue 2: Delta Log JSON Corruption
**Context**: After 100+ delta applications  
**Symptom**: `delta_log.json` fails to parse with `json.JSONDecodeError`  
**Error Snippet**:
```python
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 523 column 4
```
**Probable Cause**: Concurrent writes without file locking, incomplete flush on crash  
**Quick Fix**: Delete `logs/delta_log.json` and restart  
**Permanent Fix**: Implement atomic writes using temp file + rename pattern:
```python
import json, os, tempfile

def atomic_json_write(data, filepath):
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath))
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, filepath)  # Atomic on POSIX
```
**Prevention**: Add log rotation (keep last 1000 entries), validate JSON integrity on startup

---

### Issue 3: Color Overflow After Multiple Deltas
**Context**: User applies +100 green delta 3+ times to same cell  
**Symptom**: Cell color wraps to black or negative values  
**Error Snippet**:
```python
pygame.error: invalid color argument (300, 128, 128)
```
**Probable Cause**: No clipping after delta application  
**Quick Fix**: Add clipping in `delta.py`:
```python
def apply_delta(color, delta):
    return [max(0, min(255, c + d)) for c, d in zip(color, delta)]
```
**Permanent Fix**: Already implemented in generated code  
**Prevention**: Unit test with extreme delta values (±1000)

---

### Issue 4: Toroidal Wrapping Edge Cases
**Context**: Glider reaches grid boundary  
**Symptom**: Glider disappears or crashes with IndexError  
**Error Snippet**:
```python
IndexError: list index out of range
```
**Probable Cause**: Incorrect modulo arithmetic in neighbor calculation  
**Quick Fix**: Ensure all index operations use `% GRID_SIZE`:
```python
def get_cell(x, y):
    return grid[x % GRID_SIZE][y % GRID_SIZE]
```
**Permanent Fix**: Already implemented with toroidal wrapping tests  
**Prevention**: Unit test all 4 corners and 4 edges with glider patterns

---

### Issue 5: Zombie Resurrection Fidelity <90%
**Context**: After killing 2×2 region and resurrecting  
**Symptom**: Fidelity meter shows 65-80% instead of >90%  
**Probable Cause**: Insufficient delta history or stale neighbor aggregates  
**Quick Fix**: Increase checkpoint frequency (every 5 ticks → every 2 ticks)  
**Permanent Fix**: Implement exponential moving average for neighbor aggregates:
```python
def compute_aggregate(cell, neighbors):
    static_agg = mean([n.color_vector for n in neighbors])
    cell.ema_agg = 0.9 * cell.ema_agg + 0.1 * static_agg
    return cell.ema_agg
```
**Prevention**: Add fidelity threshold test in `test_zombie.py`

---

### Issue 6: Pygame Event Loop Lag
**Context**: After 60+ seconds of continuous running  
**Symptom**: UI becomes unresponsive, mouse clicks delayed  
**Probable Cause**: Too many events in queue, no event pump rate limiting  
**Quick Fix**: Add frame rate cap:
```python
clock = pygame.time.Clock()
while running:
    clock.tick(10)  # Max 10 FPS
```
**Permanent Fix**: Already implemented with 10 FPS cap  
**Prevention**: Monitor event queue length, add profiling

---

### Issue 7: Type Errors with NumPy Arrays
**Context**: Running `mypy src/`  
**Symptom**: Type errors on array operations  
**Error Snippet**:
```
error: Unsupported operand types for + ("List[int]" and "ndarray")
```
**Probable Cause**: Mixing Python lists and NumPy arrays without explicit conversion  
**Quick Fix**: Use NumPy arrays consistently:
```python
color_vector: np.ndarray = np.array([128, 128, 128], dtype=np.uint8)
```
**Permanent Fix**: Add type hints with `npt.NDArray[np.uint8]`  
**Prevention**: Enable strict mode in `mypy.ini`, use `numpy.typing`

---

## Escalation Protocol
If issue persists after trying Quick Fix:
1. Capture full error trace: `python src/main.py 2>&1 | tee error.log`
2. Update this document with new details
3. Open `ISSUE.md` with reproduction steps
4. Halt and request human input

---

**Last Updated**: 2025-11-02 09:48 EST  
**Maintainer**: Mark Snow Jr.
