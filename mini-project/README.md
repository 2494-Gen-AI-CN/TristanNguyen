# Game of Life: Fire Alarm Edition 🚨

Conway's Game of Life on a fake monitor, built with matplotlib and numpy. Live cells are 🚨 emojis, and the monitor has an HDMI cable you can unplug. Three live graphs track population, births vs deaths, and how long the current cells have survived.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

matplotlib needs a GUI backend. On Debian/Ubuntu, install Tk with `sudo apt install python3-tk`, or run `.venv/bin/pip install pyqt6` instead.

## Controls

| Input | Action |
| --- | --- |
| Left click / drag on screen | Add cells |
| Right click / drag on screen | Erase cells |
| Click the HDMI plug | Unplug / plug back in |
| Drag the HDMI plug | Pull it out; drop it near the port to snap it in |
| `space` | Pause / resume |
| `r` / `c` | Randomize / clear |
| `g` | Drop a glider at the mouse |
| `+` / `-` | Speed up / slow down |

While the cable is unplugged, the monitor shows a bouncing NO SIGNAL box and the power LED blinks amber. The simulation keeps running "inside the computer", so the graphs keep updating.

## Files

- `life.py`: the simulation (numpy, toroidal B3/S23, tracks cell ages)
- `sprites.py`: renders the 🚨 emoji into a sprite with Pillow, with a hand-drawn fallback if no emoji font is found
- `main.py`: the monitor, HDMI cable, graphs, and input handling
