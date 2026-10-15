"""Conway's Game of Life simulation, pure numpy."""

import numpy as np

GLIDER = np.array([[0, 1, 0],
                   [0, 0, 1],
                   [1, 1, 1]], dtype=np.uint8)


class Life:
    def __init__(self, rows=48, cols=64, seed=None):
        self.rows, self.cols = rows, cols
        self.rng = np.random.default_rng(seed)
        self.grid = np.zeros((rows, cols), dtype=np.uint8)
        self.age = np.zeros((rows, cols), dtype=np.int32)
        self.generation = 0
        self.births = 0
        self.deaths = 0

    @property
    def population(self):
        return int(self.grid.sum())

    def neighbours(self):
        g = self.grid
        n = np.zeros_like(g, dtype=np.uint8)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    n += np.roll(np.roll(g, dr, axis=0), dc, axis=1)
        return n

    def step(self):
        n = self.neighbours()
        alive = self.grid == 1
        new = (n == 3) | (alive & (n == 2))
        self.births = int((new & ~alive).sum())
        self.deaths = int((alive & ~new).sum())
        self.age = np.where(new, self.age + 1, 0)
        self.grid = new.astype(np.uint8)
        self.generation += 1
        return self.births, self.deaths

    def randomize(self, p=0.2):
        self.grid = (self.rng.random((self.rows, self.cols)) < p).astype(np.uint8)
        self.age = self.grid.astype(np.int32)

    def clear(self):
        self.grid[:] = 0
        self.age[:] = 0

    def set(self, r, c, alive=True):
        r %= self.rows
        c %= self.cols
        self.grid[r, c] = 1 if alive else 0
        if alive:
            self.age[r, c] = max(self.age[r, c], 1)
        else:
            self.age[r, c] = 0

    def stamp(self, pattern, r, c):
        h, w = pattern.shape
        rr = (np.arange(h) + r) % self.rows
        cc = (np.arange(w) + c) % self.cols
        self.grid[np.ix_(rr, cc)] |= pattern
        self.age[np.ix_(rr, cc)] = np.maximum(self.age[np.ix_(rr, cc)], pattern)
