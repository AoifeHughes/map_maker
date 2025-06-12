import json
import os
import glob
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image
import numpy as np

# Get main directory path
main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.abspath(os.path.join(main_dir, "..", "data"))
output_dir = os.path.join(main_dir, "..", "output_visuals")
hex_grid_dir = os.path.join(main_dir, "hex_grid")
pixel_image_dir = os.path.join(main_dir, "pixel_image")

# Terrain type mappings
TERRAIN_MAPPING = {
    "ocean": "w",      # Water (w)
    "open_land": "g",  # Grass (g) 
    "forest": "f",     # Forest (f)
    "lava": "g"        # Lava -> grass background, volcano sprite overlay
}

def load_player_sprite():
    """Load the player sprite from pixel_image directory."""
    player_path = os.path.join(pixel_image_dir, "player.png")
    if os.path.exists(player_path):
        return Image.open(player_path).convert("RGBA")
    else:
        # Create a fallback if player.png doesn't exist
        fallback = Image.new("RGBA", (20, 20), (255, 215, 0, 255))  # Gold square
        return fallback


def load_volcano_sprite():
    """Load the volcano sprite from pixel_image directory."""
    volcano_path = os.path.join(pixel_image_dir, "volcano.png")
    if os.path.exists(volcano_path):
        return Image.open(volcano_path).convert("RGBA")
    else:
        # Create a fallback if volcano.png doesn't exist
        fallback = Image.new("RGBA", (20, 20), (255, 100, 0, 255))  # Orange square
        return fallback


def load_rip_sprite():
    """Load the RIP sprite from pixel_image directory."""
    rip_path = os.path.join(pixel_image_dir, "rip.png")
    if os.path.exists(rip_path):
        return Image.open(rip_path).convert("RGBA")
    else:
        # Create a fallback if rip.png doesn't exist  
        fallback = Image.new("RGBA", (20, 20), (128, 128, 128, 255))  # Gray square
        return fallback


def ensure_directory_exists(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def clear_output_directory():
    """Clear existing frames from output directory."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    ensure_directory_exists(output_dir)


def find_latest_simulation_file():
    """Find the most recent complete_simulation JSON file."""
    pattern = os.path.join(data_dir, "complete_simulation_*.json")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No simulation files found in {data_dir}")
    return max(files, key=os.path.getctime)


def load_simulation_data(filepath):
    """Load and parse simulation JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)


def png_to_hex_grid(png_path):
    """Convert a PNG image to hex color grid format."""
    img = Image.open(png_path).convert('RGB')
    width, height = img.size
    
    hex_grid = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
            row.append(hex_color)
        hex_grid.append(row)
    
    return hex_grid


def load_hex_grids():
    """Load all hex grid patterns from CSV and PNG files."""
    hex_grids = {}
    
    # Load existing CSV files
    for file_path in glob.glob(os.path.join(hex_grid_dir, "*.csv")):
        key_name = os.path.basename(file_path)[:-4]  # Remove the .csv extension
        # Load the 20x20 grid from the CSV file
        grid = pd.read_csv(file_path, header=None).values.tolist()
        # Store the grid in the dictionary with the file name as the key
        hex_grids[key_name] = grid
    
    # Load new PNG files and convert to hex format
    png_grid_dir = os.path.join(main_dir, "hex_grid_png")
    if os.path.exists(png_grid_dir):
        for file_path in glob.glob(os.path.join(png_grid_dir, "*.png")):
            key_name = os.path.basename(file_path)[:-4]  # Remove the .png extension
            # Convert PNG to hex grid format
            grid = png_to_hex_grid(file_path)
            # Store the grid in the dictionary with the file name as the key
            hex_grids[key_name] = grid
            print(f"Loaded PNG pattern: {key_name}")
    
    return hex_grids


def extract_board_data(game_state):
    """Extract board dimensions and terrain data from game state."""
    board = game_state["board"]
    height, width = board["dimensions"]
    
    # Initialize terrain grid with terrain letters
    terrain_grid = np.full((height, width), 'g', dtype='U1')  # Default to grass
    
    # Fill terrain data
    for cell in board["cells"]:
        row, col = cell["position"]
        land_type = cell["land_type"]
        terrain_grid[row, col] = TERRAIN_MAPPING[land_type]
    
    return terrain_grid


def process_terrain_to_patterns(terrain_grid):
    """Convert terrain grid to 2x2 pattern keys like the map_maker system."""
    rows, cols = terrain_grid.shape
    result = []

    # Iterate through the grid in 2x2 blocks (same as make_big_hex.py)
    for i in range(rows - 1):
        row = []
        for j in range(cols - 1):
            # Extract the corner values
            top_left = terrain_grid[i, j]
            top_right = terrain_grid[i, j + 1]
            bottom_left = terrain_grid[i + 1, j]
            bottom_right = terrain_grid[i + 1, j + 1]

            # Combine into a pattern string (same order as make_big_hex.py)
            pattern_string = top_left + top_right + bottom_right + bottom_left
            row.append(pattern_string)
        result.append(row)

    return result


def expand_pattern_grid(pattern_grid, hex_grids):
    """Expand pattern grid using 20x20 hex grid templates with transformation support."""
    expanded_grid = []
    for pattern_row in pattern_grid:
        # For each row in the pattern grid, expand it into 20 rows
        expanded_rows = [[] for _ in range(20)]
        for pattern in pattern_row:
            # Get the 20x20 grid for the current pattern
            pattern_key = pattern + "1"  # Add the "1" suffix
            
            if pattern_key in hex_grids:
                # Direct match found
                sub_grid = hex_grids[pattern_key]
            elif pattern in PATTERN_TRANSFORMATIONS:
                # Use transformation mapping for missing patterns
                canonical_name, transform_func = PATTERN_TRANSFORMATIONS[pattern]
                
                if canonical_name in hex_grids:
                    # Load canonical pattern and transform it
                    base_grid = hex_grids[canonical_name]
                    
                    if transform_func is None:
                        # No transformation needed
                        sub_grid = base_grid
                    else:
                        # Convert hex grid to PIL Image, transform, then back to hex grid
                        img = hex_grid_to_image(base_grid)
                        transformed_img = transform_func(img)
                        sub_grid = image_to_hex_grid(transformed_img)
                else:
                    print(f"Warning: Canonical pattern {canonical_name} not found for {pattern}")
                    sub_grid = create_fallback_grid(pattern)
            else:
                # Legacy fallback strategy for missing patterns
                print(f"Warning: No transformation found for pattern {pattern}")
                sub_grid = create_fallback_grid(pattern)
            
            # Append each row of the sub-grid to the corresponding expanded row
            for i in range(20):
                expanded_rows[i].extend(sub_grid[i])
        # Add the expanded rows to the final grid
        expanded_grid.extend(expanded_rows)
    return expanded_grid


def hex_grid_to_image(hex_grid):
    """Convert a hex color grid to PIL Image."""
    height = len(hex_grid)
    width = len(hex_grid[0]) if height > 0 else 0
    
    img = Image.new('RGB', (width, height))
    for y in range(height):
        for x in range(width):
            hex_color = hex_grid[y][x]
            if hex_color.startswith('#'):
                hex_color = hex_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            img.putpixel((x, y), (r, g, b))
    
    return img


def image_to_hex_grid(img):
    """Convert PIL Image to hex color grid."""
    width, height = img.size
    hex_grid = []
    
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
            row.append(hex_color)
        hex_grid.append(row)
    
    return hex_grid


def create_fallback_grid(pattern):
    """Create a fallback grid for missing patterns."""
    if "l" in pattern:
        # If pattern contains lava, use red color as fallback
        return [["#FF6B35"] * 20] * 20  # Red/orange for lava
    else:
        # Default fallback to grass
        return [["#A8E61D"] * 20] * 20  # Light green for grass


def save_pattern_grid_csv(pattern_grid, filepath):
    """Save pattern grid to CSV file (like big_key.csv in make_big_hex.py)."""
    df = pd.DataFrame(pattern_grid)
    df.to_csv(filepath, index=False, header=False)
    print(f"Saved pattern grid to {filepath}")


def save_expanded_grid_csv(expanded_grid, filepath):
    """Save expanded grid to CSV file (like expanded_map.csv in make_big_hex.py)."""
    df = pd.DataFrame(expanded_grid)
    df.to_csv(filepath, index=False, header=False)
    print(f"Saved expanded grid to {filepath}")


def rotate_pattern_90(pattern):
    """Rotate a 2x2 pattern 90 degrees clockwise."""
    # Original: AB  ->  CA
    #           CD      DB
    return pattern[2] + pattern[0] + pattern[3] + pattern[1]


def rotate_pattern_180(pattern):
    """Rotate a 2x2 pattern 180 degrees."""
    # Original: AB  ->  DC
    #           CD      BA
    return pattern[3] + pattern[2] + pattern[1] + pattern[0]


def rotate_pattern_270(pattern):
    """Rotate a 2x2 pattern 270 degrees clockwise."""
    # Original: AB  ->  BD
    #           CD      AC
    return pattern[1] + pattern[3] + pattern[0] + pattern[2]


def flip_pattern_horizontal(pattern):
    """Flip a 2x2 pattern horizontally."""
    # Original: AB  ->  BA
    #           CD      DC
    return pattern[1] + pattern[0] + pattern[3] + pattern[2]


def flip_pattern_vertical(pattern):
    """Flip a 2x2 pattern vertically."""
    # Original: AB  ->  CD
    #           CD      AB
    return pattern[2] + pattern[3] + pattern[0] + pattern[1]


def transform_image_90(img):
    """Rotate image 90 degrees clockwise."""
    return img.transpose(Image.ROTATE_270)


def transform_image_180(img):
    """Rotate image 180 degrees."""
    return img.transpose(Image.ROTATE_180)


def transform_image_270(img):
    """Rotate image 270 degrees clockwise."""
    return img.transpose(Image.ROTATE_90)


def transform_image_flip_h(img):
    """Flip image horizontally."""
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def transform_image_flip_v(img):
    """Flip image vertically."""
    return img.transpose(Image.FLIP_TOP_BOTTOM)


# Pattern mapping: maps any pattern to its canonical form and required transformation
PATTERN_TRANSFORMATIONS = {
    # Water-Forest patterns - Group 1: fffw canonical
    "fffw": ("fffw1", None),
    "ffwf": ("fffw1", transform_image_270),  # Fixed: was 90, should be 270
    "fwff": ("fffw1", transform_image_180),
    "wfff": ("fffw1", transform_image_90),   # Fixed: was 270, should be 90
    
    # Group 2: ffww canonical
    "ffww": ("ffww1", None),
    "fwfw": ("ffww1", transform_image_90),
    "wfwf": ("ffww1", transform_image_180),
    "wwff": ("ffww1", transform_image_270),
    
    # Group 3: fwwf canonical
    "fwwf": ("fwwf1", None),
    "wffw": ("fwwf1", transform_image_180),
    
    # Group 4: fwww canonical
    "fwww": ("fwww1", None),
    "wfww": ("fwww1", transform_image_90),
    "wwfw": ("fwww1", transform_image_180),
    "wwwf": ("fwww1", transform_image_270),
    
    # Mixed patterns - Group 5: ffgw canonical
    "ffgw": ("ffgw1", None),
    "ffwg": ("ffgw1", transform_image_flip_h),
    "fgfw": ("ffgw1", transform_image_90),
    "fwgf": ("ffgw1", transform_image_flip_v),
    "gffw": ("ffgw1", transform_image_270),
    "gfwf": ("ffgw1", transform_image_180),
    "wffg": ("ffgw1", transform_image_flip_h),
    "wfgf": ("ffgw1", None),  # Same as ffgw rotated differently
    
    # Group 6: fggw canonical  
    "fggw": ("fggw1", None),
    "fgwg": ("fggw1", transform_image_90),
    "fwgg": ("fggw1", transform_image_180),
    "gwgf": ("fggw1", transform_image_270),
    
    # Group 7: fgwf canonical
    "fgwf": ("fgwf1", None),
    "gwff": ("fgwf1", transform_image_90),
    "wfgf": ("fgwf1", transform_image_180),
    "gffw": ("fgwf1", transform_image_270),
    
    # Group 8: fgwg canonical
    "fgwg": ("fgwg1", None),
    "gfgw": ("fgwg1", transform_image_90),
    "wgfg": ("fgwg1", transform_image_180),
    "gwgf": ("fgwg1", transform_image_270),
    "gfwg": ("fgwg1", transform_image_flip_h),
    "wgff": ("fgwg1", transform_image_flip_v),
    "gfgw": ("fgwg1", None),  # Already covered
    "wggf": ("fgwg1", transform_image_flip_h),
    
    # Group 9: fgww canonical
    "fgww": ("fgww1", None),
    "gfww": ("fgww1", transform_image_flip_h),
    "gwfw": ("fgww1", transform_image_90),
    "gwwf": ("fgww1", transform_image_flip_v),
    "wfgw": ("fgww1", transform_image_180),
    "wfwg": ("fgww1", transform_image_270),
    "wgfw": ("fgww1", None),  # Same pattern rotated
    "wwgf": ("fgww1", transform_image_flip_h),
    
    # Group 10: fwwg canonical
    "fwwg": ("fwwg1", None),
    "gwfw": ("fwwg1", transform_image_90),
    "wgwf": ("fwwg1", transform_image_180),
    "wwfg": ("fwwg1", transform_image_270),
}


def extract_player_positions(game_state):
    """Extract player positions from game state."""
    players = game_state["players"]
    positions = []
    
    for player in players:
        if player.get("alive", False):  # Only show alive players
            pos = player["location"]
            positions.append((pos[0], pos[1]))
    
    return positions


def track_death_locations_up_to_frame(simulation_data, current_frame):
    """Track locations where players died up to the current frame."""
    death_locations = set()
    
    # Keep track of player states across frames
    previous_players = {}
    
    # Only process frames up to and including the current frame
    for frame_idx, game_state in enumerate(simulation_data[:current_frame + 1]):
        current_players = {}
        
        for i, player in enumerate(game_state["players"]):
            # Use the list index as player ID since 'id' field is missing
            player_id = i
            current_alive = player.get("alive", False)
            current_pos = tuple(player["location"])
            
            # Check if this player was alive before and is now dead
            if player_id in previous_players:
                prev_alive, prev_pos = previous_players[player_id]
                if prev_alive and not current_alive:
                    # Player died - record the location where they died
                    death_locations.add(prev_pos)
            
            current_players[player_id] = (current_alive, current_pos)
        
        previous_players = current_players
    
    return list(death_locations)


def extract_lava_positions(game_state):
    """Extract lava/volcano positions from game state."""
    board = game_state["board"]
    lava_positions = []
    
    for cell in board["cells"]:
        if cell["land_type"] == "lava":
            row, col = cell["position"]
            lava_positions.append((row, col))
    
    return lava_positions


def scale_positions(positions, scale_factor=20):
    """Scale positions from simulation grid to expanded image coordinates."""
    scaled_positions = []
    for row, col in positions:
        # Each simulation cell becomes a 20x20 block
        # Place sprite in center of their block
        scaled_row = row * scale_factor + scale_factor // 2
        scaled_col = col * scale_factor + scale_factor // 2
        scaled_positions.append((scaled_row, scaled_col))
    return scaled_positions


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_frame_image(terrain_grid, player_positions, lava_positions, death_locations, frame_number, hex_grids, player_sprite, volcano_sprite, rip_sprite):
    """Create a single frame image with high-resolution terrain, players, volcanoes, and graves."""
    # Convert terrain to patterns and expand using hex grids
    pattern_grid = process_terrain_to_patterns(terrain_grid)
    
    # Save pattern grid as CSV (like big_key.csv)
    pattern_csv_path = os.path.join(output_dir, f"frame_{frame_number:03d}_pattern_grid.csv")
    save_pattern_grid_csv(pattern_grid, pattern_csv_path)
    
    # Expand using hex grids
    expanded_grid = expand_pattern_grid(pattern_grid, hex_grids)
    
    # Save expanded grid as CSV (like expanded_map.csv)
    expanded_csv_path = os.path.join(output_dir, f"frame_{frame_number:03d}_expanded_grid.csv")
    save_expanded_grid_csv(expanded_grid, expanded_csv_path)
    
    # Get dimensions of the expanded grid
    height = len(expanded_grid)
    width = len(expanded_grid[0]) if height > 0 else 0
    
    # Create RGB image
    img = Image.new("RGB", (width, height))
    
    # Fill terrain colors from hex grid
    for y in range(height):
        for x in range(width):
            hex_color = expanded_grid[y][x]
            rgb_color = hex_to_rgb(hex_color)
            img.putpixel((x, y), rgb_color)
    
    # Convert to RGBA for alpha blending with sprites
    img = img.convert("RGBA")
    
    # Scale and overlay volcano sprites first (bottom layer)
    scaled_volcanoes = scale_positions(lava_positions)
    
    for row, col in scaled_volcanoes:
        # Calculate position to center the sprite on the scaled position
        sprite_width, sprite_height = volcano_sprite.size
        paste_x = col - sprite_width // 2
        paste_y = row - sprite_height // 2
        
        # Make sure the sprite is within bounds
        if (paste_x + sprite_width > 0 and paste_x < width and 
            paste_y + sprite_height > 0 and paste_y < height):
            
            # Paste the volcano sprite with alpha blending
            img.paste(volcano_sprite, (paste_x, paste_y), volcano_sprite)
    
    # Scale and overlay RIP sprites (middle layer)
    scaled_graves = scale_positions(death_locations)
    
    for row, col in scaled_graves:
        # Calculate position to center the sprite on the scaled position
        sprite_width, sprite_height = rip_sprite.size
        paste_x = col - sprite_width // 2
        paste_y = row - sprite_height // 2
        
        # Make sure the sprite is within bounds
        if (paste_x + sprite_width > 0 and paste_x < width and 
            paste_y + sprite_height > 0 and paste_y < height):
            
            # Paste the RIP sprite with alpha blending
            img.paste(rip_sprite, (paste_x, paste_y), rip_sprite)
    
    # Scale and overlay player sprites (top layer - appear on top of everything)
    scaled_players = scale_positions(player_positions)
    
    for row, col in scaled_players:
        # Calculate position to center the sprite on the scaled position
        sprite_width, sprite_height = player_sprite.size
        paste_x = col - sprite_width // 2
        paste_y = row - sprite_height // 2
        
        # Make sure the sprite is within bounds
        if (paste_x + sprite_width > 0 and paste_x < width and 
            paste_y + sprite_height > 0 and paste_y < height):
            
            # Paste the player sprite with alpha blending
            img.paste(player_sprite, (paste_x, paste_y), player_sprite)
    
    # Convert back to RGB for saving
    final_img = Image.new("RGB", img.size, (255, 255, 255))
    final_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
    
    # Save frame
    frame_filename = f"frame_{frame_number:03d}.png"
    frame_path = os.path.join(output_dir, frame_filename)
    final_img.save(frame_path)
    
    return frame_path


def visualize_simulation(simulation_file=None):
    """Main function to create visualization frames from simulation data."""
    print("Starting simulation visualization...")
    
    # Find simulation file if not provided
    if simulation_file is None:
        simulation_file = find_latest_simulation_file()
    
    print(f"Using simulation file: {simulation_file}")
    
    # Load simulation data, hex grids, and sprites
    simulation_data = load_simulation_data(simulation_file)
    hex_grids = load_hex_grids()
    player_sprite = load_player_sprite()
    volcano_sprite = load_volcano_sprite()
    rip_sprite = load_rip_sprite()
    print(f"Loaded {len(simulation_data)} game states")
    print(f"Loaded {len(hex_grids)} hex grid patterns")
    print(f"Loaded player sprite: {player_sprite.size}")
    print(f"Loaded volcano sprite: {volcano_sprite.size}")
    print(f"Loaded RIP sprite: {rip_sprite.size}")
    
    # Clear and prepare output directory
    clear_output_directory()
    print(f"Output directory prepared: {output_dir}")
    
    # Process each game state
    generated_frames = []
    for i, game_state in enumerate(simulation_data):
        # Extract terrain, player, and lava data
        terrain_grid = extract_board_data(game_state)
        player_positions = extract_player_positions(game_state)
        lava_positions = extract_lava_positions(game_state)
        
        # Track death locations up to this frame only
        death_locations = track_death_locations_up_to_frame(simulation_data, i)
        
        # Create frame image using hex grids and sprites
        frame_path = create_frame_image(terrain_grid, player_positions, lava_positions, death_locations, i, hex_grids, player_sprite, volcano_sprite, rip_sprite)
        generated_frames.append(frame_path)
        
        print(f"Generated frame {i:03d}: {len(player_positions)} players, {len(lava_positions)} volcanoes, {len(death_locations)} graves")
    
    print(f"\nVisualization complete!")
    print(f"Generated {len(generated_frames)} frames in {output_dir}")
    print(f"Frames: frame_000.png to frame_{len(generated_frames)-1:03d}.png")
    print(f"Each frame is high-resolution using 20x20 pixel art patterns")
    
    return generated_frames


if __name__ == "__main__":
    try:
        visualize_simulation()
    except Exception as e:
        print(f"Error during visualization: {e}")
        raise