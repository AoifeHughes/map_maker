import os
import shutil
from itertools import product
from PIL import Image

# Get main directory path
main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pixel_image_dir = os.path.join(main_dir, "pixel_image")

# Terrain types
terrain_types = ['w', 'g', 'f', 'l']  # water, grass, forest, lava

def generate_lava_patterns():
    """Generate all pattern combinations that include lava."""
    
    # Check if volcano.png exists
    volcano_path = os.path.join(pixel_image_dir, "volcano.png")
    if not os.path.exists(volcano_path):
        print("Error: volcano.png not found in pixel_image directory")
        return
    
    # Load the volcano image
    volcano_img = Image.open(volcano_path)
    
    # Generate all 4-character combinations that include at least one 'l'
    all_patterns = [''.join(p) for p in product(terrain_types, repeat=4)]
    lava_patterns = [p for p in all_patterns if 'l' in p]
    
    print(f"Generating {len(lava_patterns)} lava pattern images...")
    
    generated_count = 0
    for pattern in lava_patterns:
        pattern_filename = f"{pattern}1.png"
        pattern_path = os.path.join(pixel_image_dir, pattern_filename)
        
        # Only create if it doesn't already exist
        if not os.path.exists(pattern_path):
            # For now, use the volcano image for all lava patterns
            # In the future, this could be more sophisticated
            volcano_img.save(pattern_path)
            generated_count += 1
            print(f"Created {pattern_filename}")
    
    print(f"Generated {generated_count} new lava pattern images")
    
    # Now generate the hex grids for these new patterns
    print("Generating hex grids from new lava patterns...")
    os.system(f"cd {main_dir} && python py_script/generate_hex.py")
    
    print("Lava pattern generation complete!")

if __name__ == "__main__":
    generate_lava_patterns()