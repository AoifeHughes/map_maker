import glob
import os

import pandas as pd
from PIL import Image

main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

pixel_image_dir = os.path.join(main_dir, "pixel_image")
hex_grid_dir = os.path.join(main_dir, "hex_grid")

# Use glob to find all PNG files in pixel_image directory
png_files = glob.glob(os.path.join(pixel_image_dir, "*.png"))

for image_path in png_files:
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    hex_csv_path = os.path.join(hex_grid_dir, f"{base_name}.csv")

    # Load the PNG file
    img = Image.open(image_path).convert("RGB")

    # Get image size
    width, height = img.size

    # Get pixel data
    pixels = list(img.getdata())

    # Convert to 2D grid of hex values
    hex_grid = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixels[y * width + x]
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            row.append(hex_color)
        hex_grid.append(row)

    # Save to CSV
    df = pd.DataFrame(hex_grid)
    df.to_csv(hex_csv_path, index=False, header=False)

    print(f"Saved {os.path.basename(hex_csv_path)}")
