"""
Script to create a random PGM map file for testing the costmap.
"""
import numpy as np
import os
import random

def create_random_pgm(width=907, height=455, obstacle_density=0.2):
    """Create a random PGM file with randomly placed obstacles.
    
    Args:
        width (int): Width of the image (default: 907 to match the game)
        height (int): Height of the image (default: 455 to match the game)
        obstacle_density (float): Percentage of area covered by obstacles (0.0-1.0)
    """
    print("Creating random PGM map file...")
    
    # Create empty image array (255 = white/free space)
    img = np.ones((height, width), dtype=np.uint8) * 255
    print(f"Created image array of shape {img.shape}")
    
    # Add border (0 = black/obstacle)
    border_size = 5
    img[0:border_size, :] = 0  # Top border
    img[-border_size:, :] = 0  # Bottom border
    img[:, 0:border_size] = 0  # Left border
    img[:, -border_size:] = 0  # Right border
    
    # Add random rectangular obstacles
    num_rectangles = int((width * height * obstacle_density) / 2000)  # Adjust based on map size
    print(f"Adding {num_rectangles} random rectangular obstacles...")
    
    for _ in range(num_rectangles):
        # Random size (smaller is more common)
        rect_width = random.randint(20, 100)
        rect_height = random.randint(20, 100)
        
        # Random position (ensure it's fully within the map with border)
        x = random.randint(border_size + 5, width - rect_width - border_size - 5)
        y = random.randint(border_size + 5, height - rect_height - border_size - 5)
        
        # Draw rectangle
        img[y:y+rect_height, x:x+rect_width] = 0
    
    # Add random circular obstacles
    num_circles = int((width * height * obstacle_density) / 3000)  # Adjust based on map size
    print(f"Adding {num_circles} random circular obstacles...")
    
    for _ in range(num_circles):
        # Random radius (smaller is more common)
        radius = random.randint(10, 50)
        
        # Random position (ensure it's fully within the map with border)
        center_x = random.randint(border_size + radius + 5, width - radius - border_size - 5)
        center_y = random.randint(border_size + radius + 5, height - radius - border_size - 5)
        
        # Draw circle
        for y in range(max(0, center_y - radius), min(height, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(width, center_x + radius + 1)):
                if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                    img[y, x] = 0
    
    # Add random noise (small dots)
    noise_density = obstacle_density / 10  # Lower density for noise
    noise_mask = np.random.random((height, width)) < noise_density
    # Don't place noise near the borders
    noise_mask[0:border_size+10, :] = False
    noise_mask[-border_size-10:, :] = False
    noise_mask[:, 0:border_size+10] = False
    noise_mask[:, -border_size-10:] = False
    img[noise_mask] = 0
    
    print("Added random obstacles to the image")
    
    # Ensure robot starting area is clear (bottom left corner)
    clear_radius = 50
    start_x, start_y = border_size + clear_radius, height - border_size - clear_radius
    for y in range(max(0, start_y - clear_radius), min(height, start_y + clear_radius + 1)):
        for x in range(max(0, start_x - clear_radius), min(width, start_x + clear_radius + 1)):
            if (x - start_x)**2 + (y - start_y)**2 <= clear_radius**2:
                img[y, x] = 255  # Clear area
    
    # Ensure goal area is clear (top right corner)
    clear_radius = 50
    goal_x, goal_y = width - border_size - clear_radius, border_size + clear_radius
    for y in range(max(0, goal_y - clear_radius), min(height, goal_y + clear_radius + 1)):
        for x in range(max(0, goal_x - clear_radius), min(width, goal_x + clear_radius + 1)):
            if (x - goal_x)**2 + (y - goal_y)**2 <= clear_radius**2:
                img[y, x] = 255  # Clear area
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    print("Ensured data directory exists")
    
    # Write PGM file (binary format P5)
    file_path = os.path.join("data", "map.pgm")
    print(f"Writing PGM file to: {os.path.abspath(file_path)}")
    
    try:
        with open(file_path, "wb") as f:
            # Write header
            f.write(b"P5\n")
            f.write(f"# Random map for navigation\n".encode())
            f.write(f"{width} {height}\n".encode())
            f.write(b"255\n")  # Max value
            
            # Write image data
            f.write(img.tobytes())
        
        print(f"Created random PGM file: {file_path} ({width}x{height})")
        
        # Verify file was created
        if os.path.exists(file_path):
            print(f"File exists with size: {os.path.getsize(file_path)} bytes")
        else:
            print(f"File was not created!")
    except Exception as e:
        print(f"Error creating PGM file: {e}")

if __name__ == "__main__":
    # Create a random map with 20% obstacle density
    create_random_pgm(obstacle_density=0.2) 