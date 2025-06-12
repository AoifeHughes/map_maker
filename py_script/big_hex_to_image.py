import os

import pandas as pd
from PIL import Image

main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

big_hex_csv_path = os.path.join(main_dir, "made_maps/expanded_map.csv")
output_image_path = os.path.join(main_dir, "made_maps/expanded_map.png")


def csv_to_image(csv_path, output_path):
    # Load the CSV file
    hex_grid = pd.read_csv(csv_path, header=None).values

    # Get dimensions
    height, width = hex_grid.shape

    # Create an image
    img = Image.new("RGB", (width, height))

    # Populate the image with pixel data
    for y in range(height):
        for x in range(width):
            hex_color = hex_grid[y, x]
            # Convert hex color to RGB tuple
            rgb_color = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
            img.putpixel((x, y), rgb_color)

    # Save the image
    img.save(output_path)
    print(f"Saved image to {output_path}")


if __name__ == "__main__":
    csv_to_image(big_hex_csv_path, output_image_path)
