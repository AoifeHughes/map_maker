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
    # Randomly seed terrain inside using a single random int call
    # 0 = water, 1 = grass, 2 = forest, 3 = lava
    innervals = np.random.randint(0, 4, size=(size - 2, size - 2))
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


def separate_incompatible_terrain(grid):
    """Ensure incompatible terrain types don't touch directly."""
    updated_grid = grid.copy()
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
            
            # Forests shouldn't touch water (original rule)
            if grid[i, j] == 2 and 0 in neighbors:
                updated_grid[i, j] = 1
            
            # Lava shouldn't touch water directly (creates steam/problems)
            if grid[i, j] == 3 and 0 in neighbors:
                updated_grid[i, j] = 1
                
    return updated_grid


if __name__ == "__main__":
    grid = initialize_grid(GRID_SIZE)
    for _ in range(3):
        grid = smooth(grid)
    grid = separate_incompatible_terrain(grid)
    # Save as CSV
    np.savetxt(base_map_path, grid, fmt="%d", delimiter=",")
