"""
Collision avoidance algorithms for robot navigation.
"""
import math
from .base_algorithm import BaseAlgorithm

class BugAlgorithm(BaseAlgorithm):
    """Bug algorithm implementation for obstacle avoidance."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize Bug algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.mode = "move_to_goal"  # Initial mode: directly move to goal
        self.hit_point = None       # Point where obstacle was hit
        self.closest_point = None   # Point closest to goal while following obstacle
        self.min_dist_to_goal = float('inf')  # Minimum distance to goal
        self.follow_dir = 0         # Direction to follow obstacle (0: right, 1: left)
        self.steps_following = 0    # Steps spent in follow mode
        
    def plan_path(self):
        """Plan path using Bug algorithm."""
        print("Planning path with Bug algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Maximum steps to prevent infinite loops
        max_steps = self.costmap.grid_width * self.costmap.grid_height
        
        current_pos = (start_row, start_col)
        path = [current_pos]
        
        # Direction vectors: right, down, left, up
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # Track visited positions to avoid cycles
        visited = set()
        
        for _ in range(max_steps):
            if current_pos == self.goal_pos:
                # Goal reached
                break
                
            curr_row, curr_col = current_pos
            
            if self.mode == "move_to_goal":
                # Calculate direction to goal
                dr = 1 if goal_row > curr_row else (-1 if goal_row < curr_row else 0)
                dc = 1 if goal_col > curr_col else (-1 if goal_col < curr_col else 0)
                
                # Next position
                next_row, next_col = curr_row + dr, curr_col + dc
                next_pos = (next_row, next_col)
                
                # Check if next position is valid
                if (0 <= next_row < self.costmap.grid_height and 
                    0 <= next_col < self.costmap.grid_width):
                    
                    if self.costmap.get_cell(next_row, next_col) == 0:  # Free space
                        # Move to next position
                        current_pos = next_pos
                        path.append(current_pos)
                    else:
                        # Hit obstacle, switch to follow mode
                        self.mode = "follow_obstacle"
                        self.hit_point = current_pos
                        self.closest_point = current_pos
                        self.min_dist_to_goal = self._distance(curr_row, curr_col, goal_row, goal_col)
                        self.follow_dir = 0  # Start following to the right
                        self.steps_following = 0
                else:
                    # Out of bounds, switch to follow mode
                    self.mode = "follow_obstacle"
                    self.hit_point = current_pos
                    self.closest_point = current_pos
                    self.min_dist_to_goal = self._distance(curr_row, curr_col, goal_row, goal_col)
                    self.follow_dir = 0
                    self.steps_following = 0
            
            elif self.mode == "follow_obstacle":
                self.steps_following += 1
                
                # Check if we can go back to "move_to_goal" mode
                curr_dist_to_goal = self._distance(curr_row, curr_col, goal_row, goal_col)
                
                if curr_dist_to_goal < self.min_dist_to_goal:
                    # Found a closer point to goal
                    self.closest_point = current_pos
                    self.min_dist_to_goal = curr_dist_to_goal
                
                # If we're back at hit point and have moved around, try direct path again
                if (current_pos == self.hit_point and self.steps_following > 8):
                    # Try going back to move_to_goal mode
                    self.mode = "move_to_goal"
                    continue
                
                # Try to follow the obstacle boundary
                # First, look in direction perpendicular to follow direction
                perp_dir = (self.follow_dir + 1) % 4
                dr, dc = directions[perp_dir]
                
                perp_row, perp_col = curr_row + dr, curr_col + dc
                
                # Check if that's an obstacle
                perp_is_obstacle = (
                    not (0 <= perp_row < self.costmap.grid_height and 
                         0 <= perp_col < self.costmap.grid_width) or
                    self.costmap.get_cell(perp_row, perp_col) != 0
                )
                
                if not perp_is_obstacle:
                    # No obstacle perpendicular, turn toward obstacle
                    self.follow_dir = (self.follow_dir + 1) % 4
                    next_pos = (perp_row, perp_col)
                else:
                    # Try moving forward along obstacle
                    forward_dir = self.follow_dir
                    dr, dc = directions[forward_dir]
                    
                    forward_row, forward_col = curr_row + dr, curr_col + dc
                    
                    # Check if forward is free
                    forward_is_free = (
                        0 <= forward_row < self.costmap.grid_height and 
                        0 <= forward_col < self.costmap.grid_width and
                        self.costmap.get_cell(forward_row, forward_col) == 0
                    )
                    
                    if forward_is_free:
                        # Move forward
                        next_pos = (forward_row, forward_col)
                    else:
                        # Turn away from obstacle
                        self.follow_dir = (self.follow_dir - 1) % 4
                        continue  # Try again after turning
                
                # Move to next position
                if next_pos not in visited:
                    current_pos = next_pos
                    path.append(current_pos)
                    visited.add(next_pos)
                elif len(visited) > 100:
                    # If we're stuck in a cycle, try to break it
                    self.follow_dir = (self.follow_dir + 1) % 4
                    # Jump to move_to_goal from closest point
                    current_pos = self.closest_point
                    path.append(current_pos)
                    self.mode = "move_to_goal"
                    visited.clear()
            
            # Check if we've made enough steps or are stuck
            if len(path) > max_steps / 2:
                break
        
        # Add goal to path if not already included
        if path[-1] != self.goal_pos:
            path.append(self.goal_pos)
        
        # Skip starting position
        self.path = path[1:]
        self.costmap.set_path(self.path)
        print(f"Bug algorithm path planned with {len(self.path)} steps")
    
    def _distance(self, row1, col1, row2, col2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((row2 - row1)**2 + (col2 - col1)**2)


class VFHAlgorithm(BaseAlgorithm):
    """Vector Field Histogram algorithm implementation."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize VFH algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.sector_size = 20    # Angle size of each sector in degrees
        self.num_sectors = 360 // self.sector_size  # Number of sectors
        self.safety_distance = 3  # Minimum distance to obstacles
        self.window_size = 5     # Window size for smoothing histogram
        
    def plan_path(self):
        """Plan path using Vector Field Histogram algorithm."""
        print("Planning path with VFH algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Maximum steps to prevent infinite loops
        max_steps = int(self._distance(start_row, start_col, goal_row, goal_col) * 3)
        max_steps = min(max_steps, self.costmap.grid_width * self.costmap.grid_height // 4)
        
        current_pos = (start_row, start_col)
        path = [current_pos]
        
        for _ in range(max_steps):
            if current_pos == self.goal_pos or self._distance(*current_pos, goal_row, goal_col) < 2:
                # Goal reached or close enough
                break
                
            curr_row, curr_col = current_pos
            
            # Calculate histogram of obstacle density
            histogram = self._calculate_histogram(curr_row, curr_col)
            
            # Smooth the histogram
            smoothed = self._smooth_histogram(histogram)
            
            # Find candidate valleys
            valleys = self._find_valleys(smoothed)
            
            # Select best direction
            best_dir = self._select_direction(valleys, curr_row, curr_col, goal_row, goal_col)
            
            if best_dir is None:
                # No valid direction found
                print("VFH algorithm: No valid direction found")
                break
            
            # Convert direction to movement
            angle_rad = math.radians(best_dir * self.sector_size)
            dr = int(round(math.sin(angle_rad)))
            dc = int(round(math.cos(angle_rad)))
            
            # Ensure at least one coordinate changes
            if dr == 0 and dc == 0:
                dr = 0
                dc = 1
            
            # Calculate next position
            next_row, next_col = curr_row + dr, curr_col + dc
            next_pos = (next_row, next_col)
            
            # Check if valid
            if (0 <= next_row < self.costmap.grid_height and 
                0 <= next_col < self.costmap.grid_width and
                self.costmap.get_cell(next_row, next_col) == 0):
                
                # Move to next position
                current_pos = next_pos
                path.append(current_pos)
            else:
                # Try to find another direction
                alternative_dirs = sorted(valleys, key=lambda d: abs((d * self.sector_size) - best_dir))
                found_alt = False
                
                for alt_dir in alternative_dirs[1:]:  # Skip the best dir we just tried
                    angle_rad = math.radians(alt_dir * self.sector_size)
                    dr = int(round(math.sin(angle_rad)))
                    dc = int(round(math.cos(angle_rad)))
                    
                    # Ensure at least one coordinate changes
                    if dr == 0 and dc == 0:
                        continue
                    
                    # Calculate next position
                    next_row, next_col = curr_row + dr, curr_col + dc
                    next_pos = (next_row, next_col)
                    
                    # Check if valid
                    if (0 <= next_row < self.costmap.grid_height and 
                        0 <= next_col < self.costmap.grid_width and
                        self.costmap.get_cell(next_row, next_col) == 0):
                        
                        # Move to next position
                        current_pos = next_pos
                        path.append(current_pos)
                        found_alt = True
                        break
                
                if not found_alt:
                    # Still no valid direction, we're stuck
                    print("VFH algorithm: Stuck, no valid direction found")
                    break
        
        # Add goal to path if not already included and not too far
        if path[-1] != self.goal_pos and self._distance(*path[-1], goal_row, goal_col) < 10:
            path.append(self.goal_pos)
        
        # Skip starting position
        self.path = path[1:]
        self.costmap.set_path(self.path)
        print(f"VFH path planned with {len(self.path)} steps")
    
    def _calculate_histogram(self, row, col):
        """Calculate histogram of obstacle density around current position."""
        histogram = [0] * self.num_sectors
        
        # Check cells around current position
        scan_radius = 5
        
        for r in range(max(0, row - scan_radius), min(self.costmap.grid_height, row + scan_radius + 1)):
            for c in range(max(0, col - scan_radius), min(self.costmap.grid_width, col + scan_radius + 1)):
                if self.costmap.get_cell(r, c) != 0:  # Obstacle
                    # Calculate angle to obstacle
                    dy = r - row
                    dx = c - col
                    angle = math.degrees(math.atan2(dy, dx))
                    
                    # Ensure angle is within [0, 360)
                    angle = (angle + 360) % 360
                    
                    # Calculate sector
                    sector = int(angle / self.sector_size)
                    
                    # Calculate distance
                    distance = math.sqrt(dy**2 + dx**2)
                    
                    # Add to histogram (closer obstacles have higher impact)
                    if distance <= self.safety_distance:
                        histogram[sector] = float('inf')  # Completely blocked
                    else:
                        # Add impact inversely proportional to distance
                        histogram[sector] += 1 / (distance - self.safety_distance)
        
        return histogram
    
    def _smooth_histogram(self, histogram):
        """Apply smoothing to the histogram."""
        smoothed = [0] * self.num_sectors
        half_window = self.window_size // 2
        
        for i in range(self.num_sectors):
            # Calculate weighted average of surrounding sectors
            total = 0
            weight_sum = 0
            
            for j in range(-half_window, half_window + 1):
                idx = (i + j) % self.num_sectors
                weight = self.window_size - abs(j)
                
                total += histogram[idx] * weight
                weight_sum += weight
            
            smoothed[i] = total / weight_sum if weight_sum > 0 else 0
        
        return smoothed
    
    def _find_valleys(self, histogram):
        """Find valleys (low obstacle density) in the histogram."""
        threshold = sum(histogram) / len(histogram) * 0.5
        valleys = []
        
        for i in range(self.num_sectors):
            if histogram[i] < threshold and histogram[i] < float('inf'):
                valleys.append(i)
        
        # If no valleys found, take the sector with minimum value
        if not valleys and any(h < float('inf') for h in histogram):
            valleys = [min(range(self.num_sectors), key=lambda i: histogram[i])]
        
        return valleys
    
    def _select_direction(self, valleys, curr_row, curr_col, goal_row, goal_col):
        """Select best direction from candidate valleys."""
        if not valleys:
            return None
            
        # Calculate desired direction towards goal
        angle_to_goal = math.degrees(math.atan2(goal_row - curr_row, goal_col - curr_col))
        # Ensure angle is within [0, 360)
        angle_to_goal = (angle_to_goal + 360) % 360
        
        # Find closest valley to desired direction
        desired_sector = int(angle_to_goal / self.sector_size)
        
        return min(valleys, key=lambda v: min(
            abs(v - desired_sector),
            abs(v - desired_sector + self.num_sectors),
            abs(v - desired_sector - self.num_sectors)
        ))
    
    def _distance(self, row1, col1, row2, col2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((row2 - row1)**2 + (col2 - col1)**2)


# Dictionary mapping card names to algorithm classes
COLLISION_AVOIDANCE_ALGORITHMS = {
    'BUG': BugAlgorithm,
    'VFH': VFHAlgorithm
} 