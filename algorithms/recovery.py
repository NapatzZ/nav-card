"""
Recovery algorithms for robot navigation.
"""
import random
import math
from .base_algorithm import BaseAlgorithm

class RandomWalkAlgorithm(BaseAlgorithm):
    """Random walk algorithm implementation for recovery situations."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize Random Walk algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.max_steps = 20        # Maximum steps for random walk
        self.step_length = 2       # Length of each step
        self.goal_bias = 0.2       # Probability of moving towards goal
        
    def plan_path(self):
        """Plan path using Random Walk algorithm."""
        print("Planning path with Random Walk algorithm...")
        self.path = []
        
        if not self.robot_pos:
            return
            
        current_row, current_col = self.robot_pos
        
        # Direction vectors: right, down, left, up, diagonals
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        path = []
        
        # Generate random walk path
        for _ in range(self.max_steps):
            # Decide whether to bias towards goal
            if self.goal_pos and random.random() < self.goal_bias:
                # Move towards goal
                goal_row, goal_col = self.goal_pos
                dr = 1 if goal_row > current_row else (-1 if goal_row < current_row else 0)
                dc = 1 if goal_col > current_col else (-1 if goal_col < current_col else 0)
                direction = (dr, dc)
            else:
                # Choose random direction
                direction = random.choice(directions)
            
            dr, dc = direction
            
            # Calculate next position with step length
            next_row = current_row + dr * self.step_length
            next_col = current_col + dc * self.step_length
            
            # Ensure next position is within bounds
            next_row = max(0, min(self.costmap.grid_height - 1, next_row))
            next_col = max(0, min(self.costmap.grid_width - 1, next_col))
            
            # Check if next position is valid (not an obstacle)
            if self.costmap.get_cell(next_row, next_col) == 0:
                # Generate intermediate points if step_length > 1
                if self.step_length > 1:
                    for i in range(1, self.step_length + 1):
                        # Interpolate point
                        interp_row = current_row + dr * i
                        interp_col = current_col + dc * i
                        
                        # Ensure point is within bounds
                        interp_row = max(0, min(self.costmap.grid_height - 1, interp_row))
                        interp_col = max(0, min(self.costmap.grid_width - 1, interp_col))
                        
                        # Check if interpolated point is valid
                        if self.costmap.get_cell(interp_row, interp_col) != 0:
                            # Stop at first obstacle
                            break
                        
                        path.append((interp_row, interp_col))
                else:
                    path.append((next_row, next_col))
                
                current_row, current_col = next_row, next_col
                
                # If goal reached, stop
                if self.goal_pos and (current_row, current_col) == self.goal_pos:
                    break
        
        # Set path
        self.path = path
        self.costmap.set_path(self.path)
        print(f"Random Walk path planned with {len(self.path)} steps")


class SpinRecoveryAlgorithm(BaseAlgorithm):
    """Spin recovery algorithm implementation for recovery situations."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize Spin Recovery algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.radius = 3            # Radius of the circular path
        self.num_points = 16       # Number of points in the circle
        self.scan_distance = 5     # Distance to scan for obstacles
        
    def plan_path(self):
        """Plan path using Spin Recovery algorithm."""
        print("Planning path with Spin Recovery algorithm...")
        self.path = []
        
        if not self.robot_pos:
            return
            
        current_row, current_col = self.robot_pos
        
        # First, collect information about surrounding obstacles
        closest_obstacle_dist = float('inf')
        closest_obstacle_dir = 0
        
        # Scan in 360 degrees
        for angle in range(0, 360, 10):
            angle_rad = math.radians(angle)
            
            # Check points along the ray
            for dist in range(1, self.scan_distance + 1):
                scan_row = int(current_row + dist * math.sin(angle_rad))
                scan_col = int(current_col + dist * math.cos(angle_rad))
                
                # Check if valid position
                if (0 <= scan_row < self.costmap.grid_height and 
                    0 <= scan_col < self.costmap.grid_width):
                    
                    # Check if obstacle
                    if self.costmap.get_cell(scan_row, scan_col) != 0:
                        # Found obstacle
                        if dist < closest_obstacle_dist:
                            closest_obstacle_dist = dist
                            closest_obstacle_dir = angle
                        break
        
        # Adjust radius based on closest obstacle
        if closest_obstacle_dist < float('inf'):
            # Reduce radius to avoid collision
            self.radius = min(self.radius, max(1, closest_obstacle_dist - 1))
        
        # Generate spiral path away from the closest obstacle
        path = []
        
        # Direction away from closest obstacle
        away_dir = (closest_obstacle_dir + 180) % 360
        away_dir_rad = math.radians(away_dir)
        
        # Choose direction for the spin (clockwise or counter-clockwise)
        # Base it on which direction has more free space
        clockwise_free = 0
        counterclockwise_free = 0
        
        for i in range(1, 5):
            # Check clockwise
            cw_angle = (closest_obstacle_dir + 90 * i) % 360
            cw_angle_rad = math.radians(cw_angle)
            cw_row = int(current_row + self.scan_distance * math.sin(cw_angle_rad))
            cw_col = int(current_col + self.scan_distance * math.cos(cw_angle_rad))
            
            if (0 <= cw_row < self.costmap.grid_height and 
                0 <= cw_col < self.costmap.grid_width and
                self.costmap.get_cell(cw_row, cw_col) == 0):
                clockwise_free += 1
            
            # Check counter-clockwise
            ccw_angle = (closest_obstacle_dir - 90 * i) % 360
            ccw_angle_rad = math.radians(ccw_angle)
            ccw_row = int(current_row + self.scan_distance * math.sin(ccw_angle_rad))
            ccw_col = int(current_col + self.scan_distance * math.cos(ccw_angle_rad))
            
            if (0 <= ccw_row < self.costmap.grid_height and 
                0 <= ccw_col < self.costmap.grid_width and
                self.costmap.get_cell(ccw_row, ccw_col) == 0):
                counterclockwise_free += 1
        
        # Decide direction
        spin_dir = 1 if clockwise_free >= counterclockwise_free else -1
        
        # Generate spiral path (increase radius gradually)
        for i in range(self.num_points):
            # Calculate angle for this point
            angle = (away_dir + spin_dir * i * 360 / self.num_points) % 360
            angle_rad = math.radians(angle)
            
            # Calculate position with gradually increasing radius
            current_radius = self.radius * (1 + i / (self.num_points * 2))
            row = int(current_row + current_radius * math.sin(angle_rad))
            col = int(current_col + current_radius * math.cos(angle_rad))
            
            # Ensure position is within bounds
            row = max(0, min(self.costmap.grid_height - 1, row))
            col = max(0, min(self.costmap.grid_width - 1, col))
            
            # Only add if not an obstacle
            if self.costmap.get_cell(row, col) == 0:
                path.append((row, col))
        
        # If we have a goal, add a path towards it after the spin
        if self.goal_pos and path:
            last_row, last_col = path[-1]
            goal_row, goal_col = self.goal_pos
            
            # Calculate direction to goal
            angle_to_goal = math.degrees(math.atan2(goal_row - last_row, goal_col - last_col))
            angle_to_goal_rad = math.radians(angle_to_goal)
            
            # Add intermediate points towards goal
            distance_to_goal = math.sqrt((goal_row - last_row)**2 + (goal_col - last_col)**2)
            num_steps = min(10, int(distance_to_goal))
            
            for i in range(1, num_steps + 1):
                # Interpolate
                fraction = i / num_steps
                row = int(last_row + fraction * (goal_row - last_row))
                col = int(last_col + fraction * (goal_col - last_col))
                
                # Ensure position is within bounds
                row = max(0, min(self.costmap.grid_height - 1, row))
                col = max(0, min(self.costmap.grid_width - 1, col))
                
                # Only add if not an obstacle
                if self.costmap.get_cell(row, col) == 0:
                    path.append((row, col))
                else:
                    # Stop at first obstacle
                    break
        
        # Set path
        self.path = path
        self.costmap.set_path(self.path)
        print(f"Spin Recovery path planned with {len(self.path)} steps")


# Dictionary mapping card names to algorithm classes
RECOVERY_ALGORITHMS = {
    'RandomWalk': RandomWalkAlgorithm,
    'SpinRecovery': SpinRecoveryAlgorithm
} 