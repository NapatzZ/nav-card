"""
Interactive PGM Map Builder using PyGame.
Allows users to create costmaps by clicking and dragging to place obstacles.
Enlarged display for better visibility.
"""
import pygame
import numpy as np
import os
import sys
import time

class PGMMapBuilder:
    """Interactive map builder using PyGame to create PGM costmaps."""
    
    def __init__(self, width=45, height=23, cell_size=20):
        """
        Initialize the map builder.
        
        Args:
            width (int): Width of the map in cells (45 pixels)
            height (int): Height of the map in cells (23 pixels)
            cell_size (int): Size of each cell in pixels for display (20 for enlarged view)
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size  # Enlarged cell size for better visibility
        
        # Colors
        self.WHITE = (255, 255, 255)  # Free space
        self.BLACK = (0, 0, 0)        # Obstacle
        self.GRAY = (200, 200, 200)   # Grid lines
        self.RED = (255, 0, 0)        # Border indicator
        self.GREEN = (0, 255, 0)      # Start area
        self.BLUE = (0, 0, 255)       # Goal area
        
        # Initialize grid array (255 = white/free, 0 = black/obstacle)
        self.grid = np.ones((height, width), dtype=np.uint8) * 255
        
        # Border size (in cells) - for small map
        self.border_size = 2
        
        # Create border (always black obstacles)
        self.create_borders()
        
        # Track mouse state
        self.mouse_pressed = False
        self.current_mode = self.BLACK  # Default drawing mode is obstacle
        
        # Area tracking - adjusted for smaller map
        self.start_area = {"x": self.border_size + 5, "y": height - self.border_size - 5, "radius": 3}
        self.goal_area = {"x": width - self.border_size - 5, "y": self.border_size + 5, "radius": 3}
        
        # Initialize PyGame
        pygame.init()
        self.screen_width = width * cell_size
        self.screen_height = height * cell_size
        
        # Set the window size with a minimum size
        window_width = max(self.screen_width, 800)
        window_height = max(self.screen_height, 600)
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(f"PGM Map Builder (45x23) - Cell Size: {cell_size}px")
        
        # Font for UI
        self.font = pygame.font.SysFont('Arial', 18)
        
        # Instructions display time
        self.show_instructions = True
        self.instruction_fade_time = time.time() + 15  # Show for 15 seconds
        
        # Grid display toggle
        self.show_grid = True
        
        # Zoom and pan functionality
        self.zoom_level = 1.0
        self.pan_offset_x = (window_width - self.screen_width) // 2
        self.pan_offset_y = (window_height - self.screen_height) // 2
    
    def create_borders(self):
        """Create solid black borders around the map."""
        # Top border
        self.grid[:self.border_size, :] = 0
        # Bottom border
        self.grid[-self.border_size:, :] = 0
        # Left border
        self.grid[:, :self.border_size] = 0
        # Right border
        self.grid[:, -self.border_size:] = 0
    
    def is_within_bounds(self, x, y):
        """Check if given coordinates are within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_border(self, x, y):
        """Check if given coordinates are in the border area."""
        return (x < self.border_size or x >= self.width - self.border_size or
                y < self.border_size or y >= self.height - self.border_size)
    
    def toggle_cell(self, x, y):
        """Toggle a cell between free space and obstacle, respecting borders."""
        if self.is_within_bounds(x, y) and not self.is_border(x, y):
            if self.current_mode == self.BLACK:
                self.grid[y, x] = 0  # Set obstacle
            else:
                self.grid[y, x] = 255  # Set free space
    
    def screen_to_grid(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates."""
        grid_x = (screen_x - self.pan_offset_x) // self.cell_size
        grid_y = (screen_y - self.pan_offset_y) // self.cell_size
        return int(grid_x), int(grid_y)
    
    def draw_areas(self):
        """Draw start and goal areas."""
        # Draw start area
        start_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.draw.circle(
            start_surface, 
            (*self.GREEN[:3], 100),  # Semi-transparent green
            (self.start_area["x"] * self.cell_size, self.start_area["y"] * self.cell_size),
            self.start_area["radius"] * self.cell_size
        )
        self.screen.blit(start_surface, (self.pan_offset_x, self.pan_offset_y))
        
        # Draw goal area
        goal_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.draw.circle(
            goal_surface, 
            (*self.BLUE[:3], 100),  # Semi-transparent blue
            (self.goal_area["x"] * self.cell_size, self.goal_area["y"] * self.cell_size),
            self.goal_area["radius"] * self.cell_size
        )
        self.screen.blit(goal_surface, (self.pan_offset_x, self.pan_offset_y))
    
    def draw_grid(self):
        """Draw the grid with obstacles and free space."""
        # Create a surface for the grid
        grid_surface = pygame.Surface((self.screen_width, self.screen_height))
        grid_surface.fill(self.GRAY)
        
        # Draw all cells
        for y in range(self.height):
            for x in range(self.width):
                cell_color = self.WHITE if self.grid[y, x] == 255 else self.BLACK
                
                # Highlight border cells in a different color
                if self.is_border(x, y):
                    cell_color = self.BLACK
                
                # Draw filled cell
                pygame.draw.rect(
                    grid_surface,
                    cell_color,
                    (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                )
                
                # Draw cell border if grid is enabled
                if self.show_grid:
                    pygame.draw.rect(
                        grid_surface,
                        self.GRAY,
                        (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size),
                        1  # border width
                    )
        
        # Blit the grid surface onto the screen
        self.screen.blit(grid_surface, (self.pan_offset_x, self.pan_offset_y))
    
    def draw_instructions(self):
        """Draw instructions on the screen."""
        if not self.show_instructions:
            return
            
        # Create instruction text surfaces
        instruction_width = 500
        instruction_height = 250
        instruction_bg = pygame.Surface((instruction_width, instruction_height), pygame.SRCALPHA)
        instruction_bg.fill((0, 0, 0, 180))  # Semi-transparent background
        
        instructions = [
            "Left Click: Draw/Erase obstacles",
            "E: Switch between Draw (Black) and Erase (White)",
            "G: Toggle grid lines",
            "S: Save map as 'map.pgm'", 
            "R: Reset map (keep borders)",
            "C: Clear all obstacles (keep borders)",
            "H: Show this help",
            "ESC/Q: Quit"
        ]
        
        # Position in the center of the screen
        screen_width, screen_height = self.screen.get_size()
        x_pos = (screen_width - instruction_width) // 2
        y_pos = (screen_height - instruction_height) // 2
        
        # Draw the background
        self.screen.blit(instruction_bg, (x_pos, y_pos))
        
        # Draw header
        header = self.font.render("MAP BUILDER CONTROLS", True, self.WHITE)
        self.screen.blit(header, (x_pos + (instruction_width - header.get_width()) // 2, y_pos + 10))
        
        # Draw each line of instructions
        for i, text in enumerate(instructions):
            text_surface = self.font.render(text, True, self.WHITE)
            self.screen.blit(text_surface, (x_pos + 20, y_pos + 40 + i * 25))
        
        # Timer to hide instructions
        if time.time() > self.instruction_fade_time:
            self.show_instructions = False
    
    def draw_mode_indicator(self):
        """Draw the current mode indicator."""
        mode_text = "Mode: Drawing Obstacles" if self.current_mode == self.BLACK else "Mode: Erasing Obstacles"
        text_surface = self.font.render(mode_text, True, self.BLACK, self.WHITE)
        self.screen.blit(text_surface, (20, 20))
        
        # Draw map dimensions info
        dims_text = f"Map Size: {self.width}x{self.height} | Border: {self.border_size}"
        dims_surface = self.font.render(dims_text, True, self.BLACK, self.WHITE)
        self.screen.blit(dims_surface, (20, 50))
        
        # Draw grid toggle status
        grid_text = "Grid: ON" if self.show_grid else "Grid: OFF"
        grid_surface = self.font.render(grid_text, True, self.BLACK, self.WHITE)
        self.screen.blit(grid_surface, (20, 80))
    
    def draw_coordinates(self):
        """Draw coordinates on screen to help with navigation."""
        screen_width, screen_height = self.screen.get_size()
        
        # Get mouse position and convert to grid coordinates
        mouse_pos = pygame.mouse.get_pos()
        grid_x, grid_y = self.screen_to_grid(*mouse_pos)
        
        # Only show if mouse is within grid bounds
        if self.is_within_bounds(grid_x, grid_y):
            coord_text = f"Cell: ({grid_x}, {grid_y})"
            text_surface = self.font.render(coord_text, True, self.BLACK, self.WHITE)
            self.screen.blit(text_surface, (screen_width - text_surface.get_width() - 20, 20))
    
    def draw(self):
        """Update the display."""
        self.screen.fill((150, 150, 150))  # Background color
        self.draw_grid()
        self.draw_areas()
        self.draw_mode_indicator()
        self.draw_coordinates()
        self.draw_instructions()
        pygame.display.flip()
    
    def save_map(self):
        """Save the map as a PGM file."""
        # Ensure borders are 100% black before saving
        self.create_borders()
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save the PGM file
        file_path = os.path.join("data", "map.pgm")
        
        try:
            with open(file_path, "wb") as f:
                # Write header
                f.write(b"P5\n")
                f.write(f"# Interactive PGM map\n".encode())
                f.write(f"{self.width} {self.height}\n".encode())
                f.write(b"255\n")  # Max value
                
                # Write image data
                f.write(self.grid.tobytes())
            
            print(f"Saved PGM file: {os.path.abspath(file_path)}")
            
            # Flash message on screen
            message = self.font.render(f"Map saved as {file_path}", True, self.GREEN, self.BLACK)
            screen_width = self.screen.get_size()[0]
            self.screen.blit(message, ((screen_width - message.get_width()) // 2, 120))
            pygame.display.flip()
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Error saving PGM file: {e}")
            
            # Flash error message
            message = self.font.render(f"Error saving map: {str(e)[:30]}", True, self.RED, self.BLACK)
            screen_width = self.screen.get_size()[0]
            self.screen.blit(message, ((screen_width - message.get_width()) // 2, 120))
            pygame.display.flip()
            time.sleep(1.5)
    
    def reset_map(self):
        """Reset the map to empty with just the borders."""
        # Reset to all white
        self.grid = np.ones((self.height, self.width), dtype=np.uint8) * 255
        # Add borders back
        self.create_borders()
    
    def clear_obstacles(self):
        """Clear all obstacles except the borders."""
        # Set everything to free space
        self.grid = np.ones((self.height, self.width), dtype=np.uint8) * 255
        # Re-create the borders
        self.create_borders()
        
    def run(self):
        """Main loop for the map builder."""
        running = True
        clock = pygame.time.Clock()
        
        print("=== PGM Map Builder ===")
        print("Left Click: Draw/Erase obstacles")
        print("E: Switch between Draw (Black) and Erase (White)")
        print("G: Toggle grid lines")
        print("S: Save map as 'map.pgm'")
        print("R: Reset map (keep borders)")
        print("C: Clear all obstacles (keep borders)")
        print("H: Show help")
        print("ESC/Q: Quit")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_s:
                        self.save_map()
                    elif event.key == pygame.K_r:
                        self.reset_map()
                    elif event.key == pygame.K_c:
                        self.clear_obstacles()
                    elif event.key == pygame.K_e:
                        # Toggle between draw and erase mode
                        self.current_mode = self.WHITE if self.current_mode == self.BLACK else self.BLACK
                    elif event.key == pygame.K_h:
                        # Show instructions again
                        self.show_instructions = True
                        self.instruction_fade_time = time.time() + 15
                    elif event.key == pygame.K_g:
                        # Toggle grid lines
                        self.show_grid = not self.show_grid
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.mouse_pressed = True
                        # Convert mouse position to grid coordinates
                        grid_x, grid_y = self.screen_to_grid(*event.pos)
                        if self.is_within_bounds(grid_x, grid_y):
                            self.toggle_cell(grid_x, grid_y)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left click
                        self.mouse_pressed = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.mouse_pressed:
                        # Convert mouse position to grid coordinates
                        grid_x, grid_y = self.screen_to_grid(*event.pos)
                        if self.is_within_bounds(grid_x, grid_y):
                            self.toggle_cell(grid_x, grid_y)
            
            # Update the display
            self.draw()
            
            # Cap the frame rate
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    print("Starting PGM Map Builder...")
    # Use 45x23 dimensions with enlarged cell size (20px) for better visibility
    map_builder = PGMMapBuilder(width=45, height=23, cell_size=20)
    map_builder.run()