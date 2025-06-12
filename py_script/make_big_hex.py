import glob
import os

import numpy as np
import pandas as pd

main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

base_map_path = os.path.join(main_dir, "made_maps/base_map.csv")
output_path = os.path.join(main_dir, "made_maps/big_key.csv")

hex_grid_dir = os.path.join(main_dir, "hex_grid")

# Mapping from numeric values to labels
value_to_label = {0: "w", 1: "g", 2: "f", 3: "l"}


def process_base_map(base_map):
    rows, cols = base_map.shape
    result = []

    # Iterate through the grid in 2x2 blocks
    for i in range(rows - 1):
        row = []
        for j in range(cols - 1):
            # Extract the corner values
            top_left = base_map[i, j]
            top_right = base_map[i, j + 1]
            bottom_left = base_map[i + 1, j]
            bottom_right = base_map[i + 1, j + 1]

            # Map values to labels and combine into a string
            corner_string = (
                value_to_label[top_left]
                + value_to_label[top_right]
                + value_to_label[bottom_right]
                + value_to_label[bottom_left]
            )
            row.append(corner_string)
        result.append(row)

    return result


def load_hex_grids():
    hex_grids = {}
    # Iterate through all CSV files in the hex_grid directory
    for file_path in glob.glob(os.path.join(hex_grid_dir, "*.csv")):
        key_name = os.path.basename(file_path)[:-4]  # Remove the .csv extension
        # Load the 20x20 grid from the CSV file
        grid = pd.read_csv(file_path, header=None).values.tolist()
        # Store the grid in the dictionary with the file name as the key
        hex_grids[key_name] = grid
    return hex_grids


def expand_key_grid(key_grid, hex_grids):
    expanded_grid = []
    for key_row in key_grid:
        # For each row in the key grid, expand it into 20 rows
        expanded_rows = [[] for _ in range(20)]
        for key in key_row:
            # Get the 20x20 grid for the current key
            sub_grid = hex_grids[key + "1"]
            # Append each row of the sub-grid to the corresponding expanded row
            for i in range(20):
                expanded_rows[i].extend(sub_grid[i])
        # Add the expanded rows to the final grid
        expanded_grid.extend(expanded_rows)
    return expanded_grid


if __name__ == "__main__":
    # Load the base map
    base_map = np.loadtxt(base_map_path, delimiter=",", dtype=int)

    # Process the base map to generate the key grid
    key_grid = process_base_map(base_map)

    # Save the result to a CSV file
    df = pd.DataFrame(key_grid)
    df.to_csv(output_path, index=False, header=False)

    print(f"Saved processed grid to {output_path}")

    # Load all hex grids into a dictionary
    hex_grids = load_hex_grids()

    # Expand the key grid into a larger grid
    expanded_grid = expand_key_grid(key_grid, hex_grids)

    # Save the expanded grid to a new CSV file
    expanded_output_path = os.path.join(main_dir, "made_maps/expanded_map.csv")
    pd.DataFrame(expanded_grid).to_csv(expanded_output_path, index=False, header=False)

    print(f"Saved expanded grid to {expanded_output_path}")
