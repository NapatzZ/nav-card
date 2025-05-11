"""
Costmap module for creating and managing occupancy grid maps.
"""
import pygame
import numpy as np
import os
from config import Config

class Costmap:
    """Class to manage occupancy grid maps for navigation visualization."""
    
    def __init__(self, rect_width=900, rect_height=460, resolution=20, pgm_path=None):
        """Initialize the costmap.
        
        Args:
            rect_width (int): Width of the grid area in pixels (should be 45 * resolution)
            rect_height (int): Height of the grid area in pixels (should be 23 * resolution)
            resolution (int): Size of each grid cell in pixels
            pgm_path (str, optional): Path to a PGM file to load as map
        """
        self.rect_width = rect_width
        self.rect_height = rect_height
        self.resolution = resolution
        
        # Calculate grid dimensions to fill the entire rectangle exactly
        # Calculate the resolution that fits perfectly into the rectangle
        self.grid_width = 45  # Fixed width of 45 cells
        self.grid_height = 23  # Fixed height of 23 cells
        
        # Adjust the resolution slightly to fit exactly
        self.actual_resolution_x = rect_width / self.grid_width
        self.actual_resolution_y = rect_height / self.grid_height
        
        # Initialize empty grid (0 = free, 1 = occupied)
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)
        
        # Colors for visualization
        self.free_color = (240, 240, 240)  # Light gray for free space
        self.occupied_color = (50, 50, 50)  # Dark gray for obstacles
        self.robot_color = (0, 0, 255)      # Blue for robot position
        self.path_color = (0, 255, 0)       # Green for path
        self.goal_color = (255, 0, 0)       # Red for goal
        
        # Robot position in grid coordinates
        self.robot_pos = None
        self.goal_pos = None
        self.start_pos = None  # เพิ่ม attribute สำหรับเก็บตำแหน่งเริ่มต้นของหุ่นยนต์
        self.path = []
        
        # Load map if path is provided
        if pgm_path and os.path.exists(pgm_path):
            self.load_pgm_map(pgm_path)
        else:
            self.reset_demo_map()
        
    def set_cell(self, row, col, value):
        """Set a cell in the grid to a specific value.
        
        Args:
            row (int): Row index
            col (int): Column index
            value (int): 0 for free, 1 for occupied
        """
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            self.grid[row, col] = value
    
    def get_cell(self, row, col):
        """Get the value of a cell in the grid.
        
        Args:
            row (int): Row index
            col (int): Column index
            
        Returns:
            int: Cell value (0 for free, 1 for occupied)
        """
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            return self.grid[row, col]
        return None
    
    def handle_click(self, row, col, is_robot_click=True):
        """Handle a click on the grid to place robot or goal.
        
        Args:
            row (int): Row index
            col (int): Column index
            is_robot_click (bool): If True, place robot, otherwise place goal
            
        Returns:
            bool: True if action was performed, False otherwise
        """
        if not (0 <= row < self.grid_height and 0 <= col < self.grid_width):
            return False
            
        # Check if the cell is free
        if self.grid[row, col] != 0:  # Not free
            return False
            
        if is_robot_click:
            # Set robot position
            self.set_robot_position(row, col)
        else:
            # Set goal position
            self.set_goal_position(row, col)
            
        return True
    
    def set_robot_position(self, row, col):
        """Set the current robot position.
        
        Args:
            row (int): Row index
            col (int): Column index
        """
        # Validate input to prevent crashes
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            self.robot_pos = (row, col)
            # บันทึกตำแหน่งเริ่มต้นเมื่อตั้งค่าตำแหน่งหุ่นยนต์ครั้งแรก
            if self.start_pos is None:
                self.start_pos = (row, col)
                print(f"[Costmap] Initial start position set to {self.start_pos}")
    
    def set_goal_position(self, row, col):
        """Set the goal position.
        
        Args:
            row (int): Row index
            col (int): Column index
        """
        # Validate input to prevent crashes
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            self.goal_pos = (row, col)
    
    def set_path(self, path):
        """Set the path from robot to goal.
        
        Args:
            path (list): List of (row, col) tuples representing the path
        """
        # Validate path to prevent crashes
        valid_path = []
        for pos in path:
            if len(pos) == 2:  # Check if pos is a valid tuple with 2 elements
                row, col = pos
                if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
                    valid_path.append(pos)
        self.path = valid_path
    
    def add_rectangle_obstacle(self, start_row, start_col, width, height):
        """Add a rectangular obstacle to the grid.
        
        Args:
            start_row (int): Starting row
            start_col (int): Starting column
            width (int): Width in cells
            height (int): Height in cells
        """
        # Validate input
        if (start_row < 0 or start_col < 0 or 
            start_row >= self.grid_height or start_col >= self.grid_width):
            return  # Skip if starting point is out of bounds
        
        for row in range(start_row, min(start_row + height, self.grid_height)):
            for col in range(start_col, min(start_col + width, self.grid_width)):
                self.set_cell(row, col, 1)
    
    def add_circular_obstacle(self, center_row, center_col, radius):
        """Add a circular obstacle to the grid.
        
        Args:
            center_row (int): Center row
            center_col (int): Center column
            radius (int): Radius in cells
        """
        # Validate input
        if (center_row < 0 or center_col < 0 or 
            center_row >= self.grid_height or center_col >= self.grid_width):
            return  # Skip if center point is out of bounds
        
        # Determine bounds of the circle with boundary checks
        row_start = max(0, center_row - radius)
        row_end = min(self.grid_height, center_row + radius + 1)
        col_start = max(0, center_col - radius)
        col_end = min(self.grid_width, center_col + radius + 1)
        
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if (row - center_row)**2 + (col - center_col)**2 <= radius**2:
                    self.set_cell(row, col, 1)
    
    def clear_grid(self):
        """Clear the grid (set all cells to free)."""
        self.grid.fill(0)
        
    def draw(self, surface, rect_start):
        """Draw the costmap on a surface.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            rect_start (tuple): (x, y) coordinates of the top-left corner
        """
        try:
            x_offset, y_offset = rect_start
            rect_width = self.rect_width
            rect_height = self.rect_height
            
            # Draw grid cells - using the exact calculated resolution
            for row in range(self.grid_height):
                for col in range(self.grid_width):
                    # Calculate cell position and size using the actual resolution
                    cell_rect = (
                        x_offset + col * self.actual_resolution_x,
                        y_offset + row * self.actual_resolution_y,
                        self.actual_resolution_x,
                        self.actual_resolution_y
                    )
                    
                    # Draw cell with appropriate color
                    if row < len(self.grid) and col < len(self.grid[row]):
                        if self.grid[row][col] == 0:
                            pygame.draw.rect(surface, self.free_color, cell_rect)
                        else:
                            pygame.draw.rect(surface, self.occupied_color, cell_rect)
                    else:
                        # Fallback for any out-of-bounds issues
                        pygame.draw.rect(surface, self.free_color, cell_rect)
                    
                    # Draw cell border (thinner for better appearance)
                    pygame.draw.rect(surface, (200, 200, 200), cell_rect, 1)
            
            # Draw path if it exists
            for pos in self.path:
                if pos != self.robot_pos and pos != self.goal_pos:  # Don't draw over robot/goal
                    if len(pos) == 2:  # Safety check
                        row, col = pos
                        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
                            # ตรวจสอบว่าเซลล์อยู่ในขอบเขตของแผนที่หรือไม่
                            path_rect = (
                                x_offset + col * self.actual_resolution_x + self.actual_resolution_x // 4,
                                y_offset + row * self.actual_resolution_y + self.actual_resolution_y // 4,
                                self.actual_resolution_x // 2,
                                self.actual_resolution_y // 2
                            )
                            pygame.draw.rect(surface, self.path_color, path_rect)
            
            # Draw robot position if it exists
            if self.robot_pos and len(self.robot_pos) == 2:
                row, col = self.robot_pos
                if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
                    # ตรวจสอบว่าหุ่นยนต์อยู่ในขอบเขตของแผนที่หรือไม่
                    robot_rect = (
                        x_offset + col * self.actual_resolution_x + self.actual_resolution_x // 4,
                        y_offset + row * self.actual_resolution_y + self.actual_resolution_y // 4,
                        self.actual_resolution_x // 2,
                        self.actual_resolution_y // 2
                    )
                    pygame.draw.rect(surface, self.robot_color, robot_rect)
            
            # Draw goal position if it exists
            if self.goal_pos and len(self.goal_pos) == 2:
                row, col = self.goal_pos
                if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
                    # ตรวจสอบว่าเป้าหมายอยู่ในขอบเขตของแผนที่หรือไม่
                    goal_rect = (
                        x_offset + col * self.actual_resolution_x + self.actual_resolution_x // 4,
                        y_offset + row * self.actual_resolution_y + self.actual_resolution_y // 4,
                        self.actual_resolution_x // 2,
                        self.actual_resolution_y // 2
                    )
                    pygame.draw.rect(surface, self.goal_color, goal_rect)
        
        except Exception as e:
            print(f"Error in drawing costmap: {e}")
            # Continue without crashing if there's an error
    
    def px_to_grid(self, px, py):
        """Convert pixel coordinates to grid coordinates.
        
        Args:
            px (int): X pixel coordinate
            py (int): Y pixel coordinate
            
        Returns:
            tuple: (row, col) grid coordinates
        """
        try:
            # Use the actual resolution for conversion
            col = max(0, min(self.grid_width - 1, int(px / self.actual_resolution_x)))
            row = max(0, min(self.grid_height - 1, int(py / self.actual_resolution_y)))
            return row, col
        except Exception as e:
            print(f"Error in px_to_grid conversion: {e}")
            # Return a safe default value
            return 0, 0
    
    def grid_to_px(self, row, col):
        """Convert grid coordinates to pixel coordinates.
        
        Args:
            row (int): Row index
            col (int): Column index
            
        Returns:
            tuple: (px, py) pixel coordinates (center of cell)
        """
        try:
            # Validate input
            row = max(0, min(self.grid_height - 1, row))
            col = max(0, min(self.grid_width - 1, col))
            
            # Use the actual resolution for conversion
            px = col * self.actual_resolution_x + self.actual_resolution_x // 2
            py = row * self.actual_resolution_y + self.actual_resolution_y // 2
            return px, py
        except Exception as e:
            print(f"Error in grid_to_px conversion: {e}")
            # Return a safe default value
            return 0, 0

    def reset_demo_map(self):
        """Reset the grid and create a demo map with obstacles."""
        try:
            self.clear_grid()
            
            # Add walls around the edges
            for col in range(self.grid_width):
                self.set_cell(0, col, 1)  # Top wall
                self.set_cell(self.grid_height - 1, col, 1)  # Bottom wall
            
            for row in range(self.grid_height):
                self.set_cell(row, 0, 1)  # Left wall
                self.set_cell(row, self.grid_width - 1, 1)  # Right wall
            
            # Add some obstacles
            self.add_rectangle_obstacle(5, 5, 5, 10)
            self.add_rectangle_obstacle(15, 15, 10, 5)
            self.add_circular_obstacle(10, 20, 3)
            
            # Set robot and goal
            self.set_robot_position(5, 2)
            self.set_goal_position(self.grid_height - 5, self.grid_width - 5)
        except Exception as e:
            print(f"Error in reset_demo_map: {e}")
            # Continue without crashing

    def load_pgm_map(self, pgm_path):
        """Load a map from a PGM file.
        
        Args:
            pgm_path (str): Path to the PGM file
            
        Returns:
            bool: True if map was loaded successfully, False otherwise
        """
        try:
            # Read the PGM file
            with open(pgm_path, 'rb') as f:
                # Read the header (P5 for grayscale PGM)
                header = f.readline().decode('utf-8').strip()
                
                if header != 'P5':
                    print(f"Error: {pgm_path} is not a valid PGM file (expected P5 header)")
                    return False
                
                # Skip comment lines
                line = f.readline().decode('utf-8').strip()
                while line.startswith('#'):
                    line = f.readline().decode('utf-8').strip()
                
                # Parse width and height
                width, height = [int(x) for x in line.split()]
                
                # Read max value (for grayscale)
                max_val = int(f.readline().decode('utf-8').strip())
                
                # Read pixel data
                data = f.read()
                
                # Convert data to numpy array
                if max_val <= 255:
                    # 8-bit grayscale
                    array = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
                else:
                    # 16-bit grayscale (rare)
                    array = np.frombuffer(data, dtype=np.uint16).reshape(height, width)
                
                # Convert to binary matrix (0 for free space, 1 for obstacles)
                # Assume that darker values (lower values) are obstacles
                threshold = max_val // 2
                binary_array = (array < threshold).astype(np.uint8)
                
                # Resize array to match our grid dimensions if necessary
                if binary_array.shape != (self.grid_height, self.grid_width):
                    print(f"Warning: Resizing map from {binary_array.shape} to {(self.grid_height, self.grid_width)}")
                    from scipy.ndimage import zoom
                    zoom_factors = (self.grid_height / binary_array.shape[0], 
                                    self.grid_width / binary_array.shape[1])
                    binary_array = zoom(binary_array, zoom_factors, order=0)
                    binary_array = (binary_array > 0.5).astype(np.uint8)  # Re-threshold after zoom
                
                # Update the grid
                self.grid = binary_array
                
                # ไม่ตั้งค่าตำแหน่งโดยอัตโนมัติอีกต่อไป เพื่อให้สามารถใช้ค่าจาก levels.csv ได้
                # ถ้ายังไม่มีการตั้งค่าตำแหน่งหุ่นยนต์และเป้าหมาย จึงค่อยเรียกใช้ 
                if self.robot_pos is None or self.goal_pos is None:
                    print(f"No robot or goal positions set, using default positions")
                    self.set_default_robot_and_goal_positions()
                
                print(f"Loaded map from {pgm_path} with dimensions {self.grid.shape}")
                return True
                
        except Exception as e:
            print(f"Error loading PGM file {pgm_path}: {e}")
            return False
            
    def set_default_robot_and_goal_positions(self):
        """
        Automatically set default positions for robot and goal on free spaces.
        Robot is placed at top-left free cell, goal at bottom-right free cell.
        """
        try:
            # Find a free space for robot (top-left)
            robot_placed = False
            for row in range(self.grid_height):
                if robot_placed:
                    break
                for col in range(self.grid_width):
                    if self.grid[row, col] == 0:  # Free space
                        self.robot_pos = (row, col)
                        self.start_pos = (row, col)  # กำหนดตำแหน่งเริ่มต้นของหุ่นยนต์
                        robot_placed = True
                        break
            
            # Find a free space for goal (bottom-right)
            goal_placed = False
            for row in range(self.grid_height - 1, -1, -1):
                if goal_placed:
                    break
                for col in range(self.grid_width - 1, -1, -1):
                    if self.grid[row, col] == 0:  # Free space
                        self.goal_pos = (row, col)
                        goal_placed = True
                        break
                        
            if robot_placed and goal_placed:
                print(f"Set default robot position at {self.robot_pos} and goal at {self.goal_pos}")
            else:
                print("Warning: Could not set default positions for robot and/or goal")
                
        except Exception as e:
            print(f"Error setting default positions: {e}")

    def reset(self):
        """
        Reset the costmap to its initial state.
        
        This clears the path and resets robot to its initial position.
        """
        # Clear the path
        self.path = []
        
        # ถ้ามีการกำหนดตำแหน่งเริ่มต้นของหุ่นยนต์ไว้ ให้รีเซ็ตกลับไปยังตำแหน่งนั้น
        if self.start_pos:
            prev_pos = self.robot_pos
            self.robot_pos = self.start_pos
            if prev_pos != self.start_pos:
                print(f"[Costmap] Robot position reset from {prev_pos} to start position {self.start_pos}")
        
        print("[Costmap] Path cleared, robot reset to initial position")
