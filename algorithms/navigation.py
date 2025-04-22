"""
Navigation algorithms for robot path planning.
"""
import random
import math
from .base_algorithm import BaseAlgorithm

class AStarAlgorithm(BaseAlgorithm):
    """A* Search algorithm implementation."""
    
    def plan_path(self):
        """Plan path using A* algorithm."""
        print("Planning path with A* algorithm...")
        self.path = []
        
        # Simple implementation for demonstration
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Use A* algorithm to find path
        open_set = [(start_row, start_col)]
        came_from = {}
        g_score = {(start_row, start_col): 0}
        f_score = {(start_row, start_col): self._heuristic(start_row, start_col, goal_row, goal_col)}
        
        while open_set:
            # Find node with lowest f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            if current == (goal_row, goal_col):
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                
                # Reverse path (from start to goal)
                path.reverse()
                
                # Skip the first position (robot's current position)
                self.path = path[1:]
                self.costmap.set_path(self.path)
                print(f"A* path planned with {len(self.path)} steps")
                return
            
            open_set.remove(current)
            curr_row, curr_col = current
            
            # Check neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor_row, neighbor_col = curr_row + dr, curr_col + dc
                neighbor = (neighbor_row, neighbor_col)
                
                # Skip invalid or occupied cells
                if not (0 <= neighbor_row < self.costmap.grid_height and 
                        0 <= neighbor_col < self.costmap.grid_width):
                    continue
                    
                if self.costmap.get_cell(neighbor_row, neighbor_col) != 0:  # Not free
                    continue
                
                # Diagonal movement costs more
                move_cost = 1.4 if abs(dr) + abs(dc) == 2 else 1.0
                tentative_g = g_score.get(current, float('inf')) + move_cost
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor_row, neighbor_col, goal_row, goal_col)
                    
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        
        # No path found
        print("A* algorithm: No path found")
        
    def _heuristic(self, row1, col1, row2, col2):
        """Calculate heuristic distance between two points.
        
        Args:
            row1, col1: First point coordinates
            row2, col2: Second point coordinates
            
        Returns:
            float: Euclidean distance between points
        """
        return math.sqrt((row2 - row1)**2 + (col2 - col1)**2)


class RRTAlgorithm(BaseAlgorithm):
    """Rapidly-exploring Random Tree algorithm."""
    
    def plan_path(self):
        """Plan path using RRT algorithm."""
        print("Planning path with RRT algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Implementation for demonstration (simplified RRT)
        max_iterations = 1000
        goal_sample_rate = 0.2
        step_size = 3
        
        # Tree as dictionary: vertex -> parent
        tree = {self.robot_pos: None}
        
        for _ in range(max_iterations):
            # Sample random point or goal
            if random.random() < goal_sample_rate:
                sample = (goal_row, goal_col)
            else:
                sample_row = random.randint(0, self.costmap.grid_height - 1)
                sample_col = random.randint(0, self.costmap.grid_width - 1)
                sample = (sample_row, sample_col)
            
            # Find nearest node in tree
            nearest = min(tree.keys(), key=lambda n: 
                          (n[0] - sample[0])**2 + (n[1] - sample[1])**2)
            
            # Steer towards sample
            angle = math.atan2(sample[0] - nearest[0], sample[1] - nearest[1])
            new_row = int(nearest[0] + step_size * math.sin(angle))
            new_col = int(nearest[1] + step_size * math.cos(angle))
            
            # Ensure within bounds
            new_row = max(0, min(self.costmap.grid_height - 1, new_row))
            new_col = max(0, min(self.costmap.grid_width - 1, new_col))
            new_node = (new_row, new_col)
            
            # Check if valid
            if self.costmap.get_cell(new_row, new_col) != 0:  # Not free
                continue
                
            # Add to tree
            tree[new_node] = nearest
            
            # Check if reached goal region
            if (new_row - goal_row)**2 + (new_col - goal_col)**2 < step_size**2:
                # Reconstruct path
                path = [new_node]
                current = new_node
                while tree[current] is not None:
                    current = tree[current]
                    path.append(current)
                    
                # Reverse to get path from start to goal
                path.reverse()
                
                # Add goal as final point if needed
                if path[-1] != self.goal_pos:
                    path.append(self.goal_pos)
                
                # Skip starting position
                self.path = path[1:]
                self.costmap.set_path(self.path)
                print(f"RRT path planned with {len(self.path)} steps")
                return
        
        print("RRT algorithm: No path found within iteration limit")
  

class DijkstraAlgorithm(BaseAlgorithm):
    """Dijkstra's algorithm implementation."""
    
    def plan_path(self):
        """Plan path using Dijkstra's algorithm."""
        print("Planning path with Dijkstra algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Implementation of Dijkstra's algorithm
        open_set = [(start_row, start_col)]
        came_from = {}
        g_score = {(start_row, start_col): 0}
        
        while open_set:
            # Find node with lowest g_score
            current = min(open_set, key=lambda pos: g_score.get(pos, float('inf')))
            
            if current == (goal_row, goal_col):
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                
                # Reverse path (from start to goal)
                path.reverse()
                
                # Skip the first position (robot's current position)
                self.path = path[1:]
                self.costmap.set_path(self.path)
                print(f"Dijkstra path planned with {len(self.path)} steps")
                return
            
            open_set.remove(current)
            curr_row, curr_col = current
            
            # Check neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor_row, neighbor_col = curr_row + dr, curr_col + dc
                neighbor = (neighbor_row, neighbor_col)
                
                # Skip invalid or occupied cells
                if not (0 <= neighbor_row < self.costmap.grid_height and 
                        0 <= neighbor_col < self.costmap.grid_width):
                    continue
                    
                if self.costmap.get_cell(neighbor_row, neighbor_col) != 0:  # Not free
                    continue
                
                # Diagonal movement costs more
                move_cost = 1.4 if abs(dr) + abs(dc) == 2 else 1.0
                tentative_g = g_score.get(current, float('inf')) + move_cost
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        
        # No path found
        print("Dijkstra algorithm: No path found")


class GreedySearchAlgorithm(BaseAlgorithm):
    """Greedy Best-First Search algorithm implementation."""
    
    def plan_path(self):
        """Plan path using Greedy Best-First Search."""
        print("Planning path with Greedy Search algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Implementation of Greedy Best-First Search
        open_set = [(start_row, start_col)]
        came_from = {}
        h_score = {(start_row, start_col): self._heuristic(start_row, start_col, goal_row, goal_col)}
        
        while open_set:
            # Find node with lowest h_score (closest to goal)
            current = min(open_set, key=lambda pos: h_score.get(pos, float('inf')))
            
            if current == (goal_row, goal_col):
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                
                # Reverse path (from start to goal)
                path.reverse()
                
                # Skip the first position (robot's current position)
                self.path = path[1:]
                self.costmap.set_path(self.path)
                print(f"Greedy Search path planned with {len(self.path)} steps")
                return
            
            open_set.remove(current)
            curr_row, curr_col = current
            
            # Check neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor_row, neighbor_col = curr_row + dr, curr_col + dc
                neighbor = (neighbor_row, neighbor_col)
                
                # Skip invalid or occupied cells
                if not (0 <= neighbor_row < self.costmap.grid_height and 
                        0 <= neighbor_col < self.costmap.grid_width):
                    continue
                    
                if self.costmap.get_cell(neighbor_row, neighbor_col) != 0:  # Not free
                    continue
                
                if neighbor not in came_from:
                    # New node discovered
                    came_from[neighbor] = current
                    h_score[neighbor] = self._heuristic(neighbor_row, neighbor_col, goal_row, goal_col)
                    open_set.append(neighbor)
        
        # No path found
        print("Greedy Search algorithm: No path found")
        
    def _heuristic(self, row1, col1, row2, col2):
        """Calculate heuristic distance between two points.
        
        Args:
            row1, col1: First point coordinates
            row2, col2: Second point coordinates
            
        Returns:
            float: Euclidean distance between points
        """
        return math.sqrt((row2 - row1)**2 + (col2 - col1)**2)


class WallFollowingAlgorithm(BaseAlgorithm):
    """Wall Following algorithm implementation."""
    
    def plan_path(self):
        """Plan path using Wall Following algorithm."""
        print("Planning path with Wall Following algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Implementation of simplified Wall Following
        # Direction vectors: right, down, left, up
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        current_dir = 0  # Start moving right
        
        current_pos = (start_row, start_col)
        visited = {current_pos}
        path = [current_pos]
        max_steps = self.costmap.grid_width * self.costmap.grid_height
        
        for _ in range(max_steps):
            # Try to turn left first (follow wall on left)
            left_dir = (current_dir - 1) % 4
            left_dr, left_dc = directions[left_dir]
            left_row, left_col = current_pos[0] + left_dr, current_pos[1] + left_dc
            left_pos = (left_row, left_col)
            
            # Check if can move left
            can_move_left = (0 <= left_row < self.costmap.grid_height and 
                             0 <= left_col < self.costmap.grid_width and
                             self.costmap.get_cell(left_row, left_col) == 0)
            
            if can_move_left:
                # Turn left and move
                current_dir = left_dir
                current_pos = left_pos
            else:
                # Try to move forward
                forward_dr, forward_dc = directions[current_dir]
                forward_row, forward_col = current_pos[0] + forward_dr, current_pos[1] + forward_dc
                forward_pos = (forward_row, forward_col)
                
                can_move_forward = (0 <= forward_row < self.costmap.grid_height and 
                                    0 <= forward_col < self.costmap.grid_width and
                                    self.costmap.get_cell(forward_row, forward_col) == 0)
                
                if can_move_forward:
                    # Move forward
                    current_pos = forward_pos
                else:
                    # Turn right
                    current_dir = (current_dir + 1) % 4
                    continue  # Try again from new direction
            
            # Add to path if not visited
            if current_pos not in visited:
                path.append(current_pos)
                visited.add(current_pos)
            
            # Check if reached goal region
            if ((current_pos[0] - goal_row)**2 + (current_pos[1] - goal_col)**2 < 4 or
                len(path) > max_steps / 2):
                # Add goal to path
                if current_pos != self.goal_pos:
                    path.append(self.goal_pos)
                
                # Skip starting position
                self.path = path[1:]
                self.costmap.set_path(self.path)
                print(f"Wall Following path planned with {len(self.path)} steps")
                return
        
        print("Wall Following algorithm: No path found within step limit")


class DWAAlgorithm(BaseAlgorithm):
    """Dynamic Window Approach algorithm implementation."""
    
    def plan_path(self):
        """Plan path using Dynamic Window Approach."""
        print("Planning path with DWA algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start_row, start_col = self.robot_pos
        goal_row, goal_col = self.goal_pos
        
        # Implementation of simplified DWA (Direct path with obstacle avoidance)
        current_pos = (start_row, start_col)
        path = [current_pos]
        max_steps = int(((goal_row - start_row)**2 + (goal_col - start_col)**2)**0.5 * 2)
        
        # Direction to goal
        angle_to_goal = math.atan2(goal_row - start_row, goal_col - start_col)
        
        for _ in range(max_steps):
            # Current position
            curr_row, curr_col = current_pos
            
            # Check if reached goal region
            if (curr_row - goal_row)**2 + (curr_col - goal_col)**2 < 2:
                break
                
            # Search for best next step
            best_score = float('-inf')
            best_pos = None
            
            # Sample velocities in different directions
            for angle_offset in [-0.5, -0.3, -0.1, 0, 0.1, 0.3, 0.5]:
                angle = angle_to_goal + angle_offset
                
                # Calculate movement
                dr = int(round(math.sin(angle)))
                dc = int(round(math.cos(angle)))
                
                # Ensure at least one coordinate changes
                if dr == 0 and dc == 0:
                    dr = 0
                    dc = 1
                
                # Check candidate position
                candidate_row, candidate_col = curr_row + dr, curr_col + dc
                candidate_pos = (candidate_row, candidate_col)
                
                # Skip invalid or occupied cells
                if not (0 <= candidate_row < self.costmap.grid_height and 
                        0 <= candidate_col < self.costmap.grid_width):
                    continue
                    
                if self.costmap.get_cell(candidate_row, candidate_col) != 0:  # Not free
                    continue
                
                # Calculate score: distance to obstacle - distance to goal
                min_obstacle_dist = float('inf')
                
                # Check surrounding for obstacles
                for r in range(max(0, candidate_row - 2), min(self.costmap.grid_height, candidate_row + 3)):
                    for c in range(max(0, candidate_col - 2), min(self.costmap.grid_width, candidate_col + 3)):
                        if self.costmap.get_cell(r, c) != 0:  # Obstacle
                            dist = ((r - candidate_row)**2 + (c - candidate_col)**2)**0.5
                            min_obstacle_dist = min(min_obstacle_dist, dist)
                
                # Distance to goal
                goal_dist = ((candidate_row - goal_row)**2 + (candidate_col - goal_col)**2)**0.5
                
                # Score: higher is better
                # Weight obstacle avoidance more than goal seeking
                score = min_obstacle_dist - 0.5 * goal_dist
                
                if score > best_score:
                    best_score = score
                    best_pos = candidate_pos
            
            # No valid move found
            if best_pos is None:
                print("DWA algorithm: Stuck, no valid move found")
                break
                
            # Update position and add to path
            current_pos = best_pos
            path.append(current_pos)
        
        # Add goal to path if not reached
        if path[-1] != self.goal_pos:
            path.append(self.goal_pos)
        
        # Skip starting position
        self.path = path[1:]
        self.costmap.set_path(self.path)
        print(f"DWA path planned with {len(self.path)} steps")


# Dictionary mapping card names to algorithm classes
NAVIGATION_ALGORITHMS = {
    'AStar': AStarAlgorithm,
    'RRT': RRTAlgorithm,
    'Dijkstra': DijkstraAlgorithm,
    'GreedySearch': GreedySearchAlgorithm,
    'WallFollowing': WallFollowingAlgorithm,
    'DWA': DWAAlgorithm
} 