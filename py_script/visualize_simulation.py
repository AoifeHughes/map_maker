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


def load_hex_grids():
    """Load all hex grid patterns from CSV files."""
    hex_grids = {}
    # Iterate through all CSV files in the hex_grid directory
    for file_path in glob.glob(os.path.join(hex_grid_dir, "*.csv")):
        key_name = os.path.basename(file_path)[:-4]  # Remove the .csv extension
        # Load the 20x20 grid from the CSV file
        grid = pd.read_csv(file_path, header=None).values.tolist()
        # Store the grid in the dictionary with the file name as the key
        hex_grids[key_name] = grid
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

    # Iterate through the grid in 2x2 blocks
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
    """Expand pattern grid using 20x20 hex grid templates."""
    expanded_grid = []
    for pattern_row in pattern_grid:
        # For each row in the pattern grid, expand it into 20 rows
        expanded_rows = [[] for _ in range(20)]
        for pattern in pattern_row:
            # Get the 20x20 grid for the current pattern
            pattern_key = pattern + "1"  # Add the "1" suffix
            if pattern_key in hex_grids:
                sub_grid = hex_grids[pattern_key]
            else:
                # Fallback strategy for missing patterns
                if "l" in pattern:
                    # If pattern contains lava but no exact match, try to find a similar lava pattern
                    fallback_keys = [k for k in hex_grids.keys() if "l" in k]
                    if fallback_keys:
                        sub_grid = hex_grids[fallback_keys[0]]
                    else:
                        # If no lava patterns exist, use a red color as fallback
                        sub_grid = [["#FF6B35"] * 20] * 20  # Red/orange for lava
                else:
                    # Default fallback to grass
                    sub_grid = hex_grids.get("gggg1", [["#A8E61D"] * 20] * 20)
            
            # Append each row of the sub-grid to the corresponding expanded row
            for i in range(20):
                expanded_rows[i].extend(sub_grid[i])
        # Add the expanded rows to the final grid
        expanded_grid.extend(expanded_rows)
    return expanded_grid


def extract_player_positions(game_state):
    """Extract player positions from game state."""
    players = game_state["players"]
    positions = []
    
    for player in players:
        if player.get("alive", False):  # Only show alive players
            pos = player["location"]
            positions.append((pos[0], pos[1]))
    
    return positions


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


def create_frame_image(terrain_grid, player_positions, lava_positions, frame_number, hex_grids, player_sprite, volcano_sprite):
    """Create a single frame image with high-resolution terrain, players, and volcanoes."""
    # Convert terrain to patterns and expand using hex grids
    pattern_grid = process_terrain_to_patterns(terrain_grid)
    expanded_grid = expand_pattern_grid(pattern_grid, hex_grids)
    
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
    
    # Scale and overlay volcano sprites first (so players appear on top)
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
    
    # Scale and overlay player sprites (on top of everything)
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
    print(f"Loaded {len(simulation_data)} game states")
    print(f"Loaded {len(hex_grids)} hex grid patterns")
    print(f"Loaded player sprite: {player_sprite.size}")
    print(f"Loaded volcano sprite: {volcano_sprite.size}")
    
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
        
        # Create frame image using hex grids and sprites
        frame_path = create_frame_image(terrain_grid, player_positions, lava_positions, i, hex_grids, player_sprite, volcano_sprite)
        generated_frames.append(frame_path)
        
        print(f"Generated frame {i:03d}: {len(player_positions)} players, {len(lava_positions)} volcanoes")
    
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