import os

import numpy as np

main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

base_map_path = os.path.join(main_dir, "made_maps/base_map.csv")

GRID_SIZE = 40


def initialize_grid(size):
    grid = np.ones((size, size), dtype=int)  # Start with grass
    grid[0, :] = 0
    grid[-1, :] = 0
    grid[:, 0] = 0
    grid[:, -1] = 0
    # Randomly seed some water and forest inside using a single random int call
    innervals = np.random.randint(0, 3, size=(size - 2, size - 2))
    # Set only 0 (water) and 2 (forest), leave 1 (grass) as is
    grid[1:-1, 1:-1] = innervals
    return grid


def smooth(grid):
    smoothed_grid = grid.copy()
    for i in range(1, grid.shape[0] - 1):
        for j in range(1, grid.shape[1] - 1):
            neighbors = [
                grid[i - 1, j - 1],
                grid[i - 1, j],
                grid[i - 1, j + 1],
                grid[i, j - 1],
                grid[i, j + 1],
                grid[i + 1, j - 1],
                grid[i + 1, j],
                grid[i + 1, j + 1],
            ]
            most_common = max(set(neighbors), key=neighbors.count)
            if neighbors.count(most_common) >= 5:
                smoothed_grid[i, j] = most_common
    return smoothed_grid


def no_0_touch_2(grid):
    updated_grid = grid.copy()
    for i in range(1, grid.shape[0] - 1):
        for j in range(1, grid.shape[1] - 1):
            if grid[i, j] == 2:
                neighbors = [
                    grid[i - 1, j - 1],
                    grid[i - 1, j],
                    grid[i - 1, j + 1],
                    grid[i, j - 1],
                    grid[i, j + 1],
                    grid[i + 1, j - 1],
                    grid[i + 1, j],
                    grid[i + 1, j + 1],
                ]
                if 0 in neighbors:
                    updated_grid[i, j] = 1
    return updated_grid


if __name__ == "__main__":
    grid = initialize_grid(GRID_SIZE)
    for _ in range(3):
        grid = smooth(grid)
    grid = no_0_touch_2(grid)
    # Save as CSV
    np.savetxt(base_map_path, grid, fmt="%d", delimiter=",")
