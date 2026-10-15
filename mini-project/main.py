"""Conway's Game of Life on a fake monitor with a pluggable HDMI cable.

Live cells are 🚨 emojis. Click/drag on the screen to add cells, drag or click
the HDMI plug on the right side of the monitor to unplug it.
"""

import numpy as np
import matplotlib as mpl

# Free up keys we use ourselves and hide the toolbar so clicks reach the game.
for key in ("keymap.home", "keymap.back", "keymap.grid", "keymap.forward"):
    mpl.rcParams[key] = [k for k in mpl.rcParams[key] if k not in ("r", "c", "g", "v")]
mpl.rcParams["toolbar"] = "None"

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon, Rectangle  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

from life import GLIDER, Life  # noqa: E402
from sprites import make_alarm_sprite  # noqa: E402

ROWS, COLS, PX = 48, 64, 16
H, W = ROWS * PX, COLS * PX
HISTORY = 300
FRAME_MS = 40
SPEEDS = [10, 6, 4, 2, 1]  # animation frames per generation, slowest -> fastest

BG = "#14161c"
PANEL = "#1b1e26"
TEXT = "#d6d9e0"
MUTED = "#7d8390"
RED = "#ff5a5f"
AMBER = "#ffb703"
BLUE = "#4cc9f0"
GREEN = "#3ddc84"

PORT = np.array([14.05, 9.0])       # mouth of the HDMI port (scene coords)
UNPLUGGED = np.array([15.4, 7.4])   # where the plug rests when pulled out
SCREEN = (1.7, 5.1, 11.6, 8.7)      # x, y, w, h of the screen in scene coords (4:3)

AGE_UPPER = np.array([2, 3, 4, 6, 10, 18, 34, 66, 130])
AGE_LABELS = ["1", "2", "3", "4-5", "6-9", "10-17", "18-33", "34-65", "66-129", "130+"]
DVD_COLORS = [BLUE, AMBER, RED, GREEN, "#c77dff"]


def build_tiles(px):
    """Precompute uint8 tiles: empty cell, alarm cell, and alarm cell with red glow."""
    sprite = make_alarm_sprite(px)
    rgb, a = sprite[..., :3], sprite[..., 3:]
    y, x = np.mgrid[0:px, 0:px]
    base = np.ones((px, px, 3)) * np.array([11, 15, 22]) / 255
    edge = (x == 0) | (y == 0)
    base[edge] = np.array([20, 26, 36]) / 255  # faint grid lines
    r = np.hypot(x - (px - 1) / 2, y - (px - 1) / 2) / (px / 2)
    glow = base + np.clip(1 - r, 0, 1)[..., None] ** 1.5 * np.array([0.75, 0.08, 0.05])
    scan = np.where(y % 2 == 0, 1.0, 0.86)[..., None]  # CRT scanlines

    def finish(t):
        return (np.clip(t * scan, 0, 1) * 255).astype(np.uint8)

    alarm = rgb * a + base * (1 - a)
    alarm_glow = np.clip(rgb * 1.08, 0, 1) * a + glow * (1 - a)
    return finish(base), finish(alarm), finish(alarm_glow)


class App:
    def __init__(self, seed=None):
        self.life = Life(ROWS, COLS, seed=seed)
        self.life.randomize(0.22)
        self.rng = np.random.default_rng(seed)
        self.empty_tile, self.alarm_tile, self.glow_tile = build_tiles(PX)

        self.running = True
        self.speed = 2
        self.frame = 0
        self.paint = 0          # 0 none, 1 add, -1 erase
        self.mouse_cell = None

        self.plug_pos = PORT.copy()
        self.plug_home = True   # target is the port
        self.plug_target = PORT.copy()
        self.dragging = False
        self.drag_offset = np.zeros(2)
        self.drag_moved = 0.0
        self.was_connected = True
        self.static_frames = 0
        self.osd_frames = 30
        self.dvd_pos = np.array([W * 0.3, H * 0.4])
        self.dvd_vel = np.array([7.0, 5.0])
        self.dvd_color = 0

        self.gens, self.pops, self.births, self.deaths = [], [], [], []
        self.record()

        self.fig = plt.figure(figsize=(15, 8.5), facecolor=BG)
        if self.fig.canvas.manager:
            self.fig.canvas.manager.set_window_title("Game of Life - Alarm Edition")
        self.build_scene()
        self.build_graphs()

        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

    # ------------------------------------------------------------------ scene
    def build_scene(self):
        ax = self.scene = self.fig.add_axes([0, 0, 0.6, 1])
        ax.set_xlim(0, 18)
        ax.set_ylim(0, 17)
        ax.axis("off")

        ax.text(7.5, 15.9, "CONWAY'S GAME OF LIFE", ha="center", va="center",
                color=TEXT, fontsize=17, fontweight="bold", family="monospace")
        ax.text(7.5, 15.25, "fire alarm edition", ha="center", va="center",
                color=RED, fontsize=10, family="monospace")

        # stand
        ax.add_patch(Polygon([(6.8, 4.1), (8.2, 4.1), (8.5, 2.0), (6.5, 2.0)],
                             closed=True, fc="#2a2d35", ec="#3a3e48", zorder=1))
        ax.add_patch(FancyBboxPatch((4.6, 1.45), 5.8, 0.5, boxstyle="round,pad=0.08",
                                    fc="#2a2d35", ec="#3a3e48", zorder=1))

        # plug tip sits under the bezel so it vanishes "inside" the port when plugged
        self.tip = Rectangle((0, 0), 0.38, 0.5, fc="#c9ced6", ec="#8d939d", lw=0.8, zorder=1)
        ax.add_patch(self.tip)

        # bezel
        ax.add_patch(FancyBboxPatch((1.3, 4.3), 12.4, 10.1,
                                    boxstyle="round,pad=0.3,rounding_size=0.45",
                                    fc="#23262e", ec="#3d414c", lw=2, zorder=2))
        ax.add_patch(Rectangle((SCREEN[0] - 0.08, SCREEN[1] - 0.08), SCREEN[2] + 0.16,
                               SCREEN[3] + 0.16, fc="#050608", ec="none", zorder=2))
        ax.text(7.5, 4.55, "LIFETRON", ha="center", va="center", color="#6b717d",
                fontsize=9, fontweight="bold", family="monospace", zorder=3)
        self.led = Circle((12.9, 4.55), 0.12, fc=GREEN, ec="none", zorder=3)
        ax.add_patch(self.led)

        # HDMI port notch on the right edge
        ax.add_patch(Rectangle((PORT[0] - 0.25, PORT[1] - 0.34), 0.25, 0.68,
                               fc="#050505", ec="#555a64", lw=0.8, zorder=3))
        ax.text(PORT[0] - 0.5, PORT[1], "HDMI", rotation=90, ha="center", va="center",
                color="#6b717d", fontsize=6, family="monospace", zorder=3)

        # cable and plug body
        self.cable = PathPatch(Path([[0, 0]] * 4), fill=False, ec="#202227", lw=8,
                               capstyle="round", zorder=4)
        self.cable_shine = PathPatch(Path([[0, 0]] * 4), fill=False, ec="#4a4f59", lw=1.4,
                                     capstyle="round", zorder=4)
        self.relief = Rectangle((0, 0), 0.38, 0.42, fc="#2b2e35", ec="#40444e", zorder=5)
        self.housing = FancyBboxPatch((0, 0), 1.1, 0.8, boxstyle="round,pad=0.06",
                                      fc="#1b1d22", ec="#454955", lw=1.2, zorder=5)
        for p in (self.cable, self.cable_shine, self.relief, self.housing):
            ax.add_patch(p)
        self.plug_label = ax.text(0, 0, "HDMI", ha="center", va="center", color="#9aa0aa",
                                  fontsize=6.5, fontweight="bold", family="monospace", zorder=6)
        self.place_plug()

        ax.text(7.5, 0.95, "click/drag screen: add cells   right-drag: erase   "
                "drag or click the HDMI plug", ha="center", color=MUTED, fontsize=8.5,
                family="monospace")
        ax.text(7.5, 0.45, "space: pause   r: random   c: clear   g: glider   +/-: speed",
                ha="center", color=MUTED, fontsize=8.5, family="monospace")
        self.status = ax.text(7.5, 3.0, "", ha="center", va="center", color=TEXT,
                              fontsize=10, family="monospace", zorder=6,
                              bbox=dict(boxstyle="round,pad=0.5", fc="#0d0f14", ec="#2e323d"))

        # the screen itself
        sx = self.screen = ax.inset_axes(SCREEN, transform=ax.transData, zorder=3)
        sx.set_axis_off()
        self.image = sx.imshow(self.render_cells(), extent=(0, W, H, 0), aspect="auto",
                               interpolation="antialiased")
        self.no_signal = sx.text(*self.dvd_pos, "NO SIGNAL\nHDMI 1", ha="center",
                                 va="center", fontsize=15, fontweight="bold",
                                 family="monospace", color=BLUE, visible=False,
                                 bbox=dict(boxstyle="round,pad=0.6", fc="#000000",
                                           ec=BLUE, lw=2))
        self.osd = sx.text(W - 30, 40, "", ha="right", va="center", fontsize=12,
                           fontweight="bold", family="monospace", color="#e8ffe8",
                           bbox=dict(boxstyle="round,pad=0.35", fc="#000000aa", ec="none"))

    def place_plug(self):
        ox, oy = self.plug_pos
        self.tip.set_xy((ox - 0.38, oy - 0.25))
        self.housing.set_bounds(ox, oy - 0.4, 1.1, 0.8)
        self.relief.set_xy((ox + 1.1, oy - 0.21))
        self.plug_label.set_position((ox + 0.55, oy))
        start = (ox + 1.45, oy)
        path = Path([start, (ox + 2.8, oy), (17.4, 3.8), (17.8, -0.6)],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
        self.cable.set_path(path)
        self.cable_shine.set_path(path)

    # ----------------------------------------------------------------- graphs
    def style(self, ax, title):
        ax.set_facecolor(PANEL)
        ax.set_title(title, color=TEXT, fontsize=11, loc="left", family="monospace")
        ax.tick_params(colors=MUTED, labelsize=8)
        for s in ax.spines.values():
            s.set_color("#2e323d")
        ax.grid(color="#2a2e38", lw=0.6)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    def build_graphs(self):
        left, w, h = 0.655, 0.32, 0.22
        self.ax_pop = self.fig.add_axes([left, 0.71, w, h])
        self.ax_bd = self.fig.add_axes([left, 0.40, w, h])
        self.ax_age = self.fig.add_axes([left, 0.08, w, h])

        self.style(self.ax_pop, "Population (alive alarms)")
        (self.pop_line,) = self.ax_pop.plot([], [], color=RED, lw=1.8)

        self.style(self.ax_bd, "Births vs deaths per generation")
        (self.birth_line,) = self.ax_bd.plot([], [], color=AMBER, lw=1.4, label="births")
        (self.death_line,) = self.ax_bd.plot([], [], color=BLUE, lw=1.4, label="deaths")
        self.ax_bd.legend(loc="upper right", fontsize=8, facecolor=PANEL, edgecolor="#2e323d",
                          labelcolor=TEXT)

        self.style(self.ax_age, "How long current cells have survived")
        x = np.arange(len(AGE_LABELS))
        self.age_bars = self.ax_age.bar(x, np.ones(len(x)), color=RED, width=0.75)
        self.ax_age.set_yscale("log")
        self.ax_age.set_xticks(x, AGE_LABELS)
        self.ax_age.set_xlabel("age (generations)", color=MUTED, fontsize=8)
        self.ax_age.set_ylabel("cells", color=MUTED, fontsize=8)
        self.ax_age.grid(axis="x", visible=False)
        self.update_graphs()

    def record(self):
        self.gens.append(self.life.generation)
        self.pops.append(self.life.population)
        self.births.append(self.life.births)
        self.deaths.append(self.life.deaths)
        for lst in (self.gens, self.pops, self.births, self.deaths):
            del lst[:-HISTORY]

    def update_graphs(self):
        g = np.array(self.gens)
        x0 = g[0]
        x1 = max(g[-1], x0 + 20)
        self.pop_line.set_data(g, self.pops)
        self.ax_pop.set_xlim(x0, x1)
        self.ax_pop.set_ylim(0, max(self.pops) * 1.15 + 5)

        self.birth_line.set_data(g, self.births)
        self.death_line.set_data(g, self.deaths)
        self.ax_bd.set_xlim(x0, x1)
        self.ax_bd.set_ylim(0, max(max(self.births), max(self.deaths)) * 1.15 + 5)

        ages = self.life.age[self.life.grid == 1]
        counts = np.bincount(np.searchsorted(AGE_UPPER, ages, side="right"),
                             minlength=len(AGE_LABELS))
        for bar, n in zip(self.age_bars, counts):
            bar.set_height(n)
        self.ax_age.set_ylim(0.8, max(counts.max(), 1) * 2.5)

    # ----------------------------------------------------------------- screen
    def render_cells(self):
        alive = self.life.grid.astype(bool)[:, None, :, None, None]
        tile = self.glow_tile if (self.frame // 6) % 2 else self.alarm_tile
        buf = np.where(alive, tile[None, :, None], self.empty_tile[None, :, None])
        return buf.reshape(H, W, 3)

    def render_static(self):
        noise = self.rng.integers(0, 256, (H // 4, W // 4), dtype=np.uint8)
        noise = np.repeat(np.repeat(noise, 4, axis=0), 4, axis=1)
        return np.repeat(noise[..., None], 3, axis=2)

    @property
    def connected(self):
        return not self.dragging and np.hypot(*(self.plug_pos - PORT)) < 0.03

    def update_screen(self, connected):
        if connected != self.was_connected:
            self.was_connected = connected
            self.static_frames = 7
            if connected:
                self.osd_frames = 40

        self.no_signal.set_visible(False)
        if self.static_frames > 0:
            self.static_frames -= 1
            self.image.set_data(self.render_static())
        elif connected:
            self.image.set_data(self.render_cells())
        else:
            self.image.set_data(np.zeros((8, 8, 3), dtype=np.uint8))
            self.bounce_no_signal()

        if connected and not self.static_frames and (self.osd_frames > 0 or not self.running):
            self.osd.set_text("HDMI 1" if self.osd_frames > 0 else "PAUSED")
            self.osd.set_visible(True)
        else:
            self.osd.set_visible(False)
        self.osd_frames = max(0, self.osd_frames - 1)

        if connected:
            self.led.set_facecolor(GREEN)
        else:  # standby: slow amber blink
            self.led.set_facecolor(AMBER if (self.frame // 12) % 2 else "#4a3a10")

    def bounce_no_signal(self):
        margin = np.array([135.0, 70.0])
        self.dvd_pos += self.dvd_vel
        for i, hi in enumerate((W, H)):
            if not margin[i] <= self.dvd_pos[i] <= hi - margin[i]:
                self.dvd_vel[i] *= -1
                self.dvd_pos[i] = np.clip(self.dvd_pos[i], margin[i], hi - margin[i])
                self.dvd_color = (self.dvd_color + 1) % len(DVD_COLORS)
        c = DVD_COLORS[self.dvd_color]
        self.no_signal.set_position(self.dvd_pos)
        self.no_signal.set_color(c)
        self.no_signal.get_bbox_patch().set_edgecolor(c)
        self.no_signal.set_visible(True)

    # ------------------------------------------------------------------- loop
    def update(self, _=None):
        self.frame += 1
        if self.running and self.frame % SPEEDS[self.speed] == 0:
            self.life.step()
            self.record()

        if not self.dragging:
            self.plug_pos += (self.plug_target - self.plug_pos) * 0.3
            if np.hypot(*(self.plug_target - self.plug_pos)) < 0.01:
                self.plug_pos = self.plug_target.copy()
        self.place_plug()

        connected = self.connected
        self.update_screen(connected)
        self.update_graphs()

        state = "NO SIGNAL" if not connected else ("RUNNING" if self.running else "PAUSED")
        self.status.set_text(f"GEN {self.life.generation:>5}   POP {self.life.population:>4}"
                             f"   {state:<9}   SPEED {self.speed + 1}/{len(SPEEDS)}")
        return []

    # ----------------------------------------------------------------- events
    def scene_xy(self, event):
        return self.scene.transData.inverted().transform((event.x, event.y))

    def cell_at(self, event):
        # the screen is an inset axes, which event.inaxes never reports, so hit-test by hand
        x, y = self.screen.transData.inverted().transform((event.x, event.y))
        if 0 <= x < W and 0 <= y < H:
            r, c = int(y // PX), int(x // PX)
            return r, c
        return None

    def paint_to(self, a, b):
        """Paint every cell on the line a -> b so fast drags leave no gaps."""
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1])) + 1
        for r, c in zip(np.linspace(a[0], b[0], n).round(), np.linspace(a[1], b[1], n).round()):
            self.life.set(int(r), int(c), alive=self.paint > 0)

    def on_plug(self, event):
        return any(p.contains(event)[0] for p in (self.housing, self.relief, self.tip))

    def on_press(self, event):
        if event.button == 1 and self.on_plug(event):
            self.dragging = True
            self.drag_moved = 0.0
            self.drag_offset = self.scene_xy(event) - self.plug_pos
            return
        cell = self.cell_at(event)
        if cell and self.connected and event.button in (1, 3):
            self.paint = 1 if event.button == 1 else -1
            self.mouse_cell = cell
            self.paint_to(cell, cell)

    def on_motion(self, event):
        if self.dragging:
            new = self.scene_xy(event) - self.drag_offset
            new = np.clip(new, [PORT[0], 1.0], [17.0, 16.0])
            self.drag_moved += np.hypot(*(new - self.plug_pos))
            self.plug_pos = new
            return
        cell = self.cell_at(event)
        if cell:
            if self.paint and self.connected:
                self.paint_to(self.mouse_cell or cell, cell)
            self.mouse_cell = cell

    def on_release(self, event):
        self.paint = 0
        if not self.dragging:
            return
        self.dragging = False
        if self.drag_moved < 0.15:  # a click: toggle
            self.plug_home = not self.plug_home
            self.plug_target = (PORT if self.plug_home else UNPLUGGED).copy()
        elif np.hypot(*(self.plug_pos - PORT)) < 0.9:  # dropped near port: snap in
            self.plug_home = True
            self.plug_target = PORT.copy()
        else:  # dropped elsewhere: let it sag a little under gravity
            self.plug_home = False
            self.plug_target = np.array([self.plug_pos[0], max(1.0, self.plug_pos[1] - 0.7)])

    def on_key(self, event):
        k = event.key
        if k == " ":
            self.running = not self.running
        elif k == "r":
            self.life.randomize(0.22)
        elif k == "c":
            self.life.clear()
        elif k == "g":
            r, c = self.mouse_cell or (ROWS // 2, COLS // 2)
            self.life.stamp(GLIDER, r - 1, c - 1)
        elif k in ("+", "="):
            self.speed = min(self.speed + 1, len(SPEEDS) - 1)
        elif k in ("-", "_"):
            self.speed = max(self.speed - 1, 0)

    def run(self):
        self.anim = FuncAnimation(self.fig, self.update, interval=FRAME_MS,
                                  blit=False, cache_frame_data=False)
        plt.show()


if __name__ == "__main__":
    if plt.get_backend().lower() in ("agg", "pdf", "svg", "ps", "cairo", "template"):
        raise SystemExit("No interactive matplotlib backend found. On Debian/Ubuntu run "
                         "`sudo apt install python3-tk`, or `pip install pyqt6` in the venv.")
    App().run()
