"""
Path planning algorithms for robot navigation.
"""
import math
import random
import heapq
from .base_algorithm import BaseAlgorithm

class AStarAlgorithm(BaseAlgorithm):
    """A* algorithm implementation for path planning."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize A* algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.allow_diagonal = True  # Whether to allow diagonal movement
        self.heuristic = "euclidean"  # Heuristic type: "manhattan", "euclidean", "chebyshev"
        
    def plan_path(self):
        """Plan path using A* algorithm."""
        print("Planning path with A* algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        # Check if goal is valid (not an obstacle)
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        # Map to store costs from start
        g_score = {start: 0}
        
        # Map to store estimated total costs
        f_score = {start: self._heuristic(start, goal)}
        
        # Priority queue for open nodes
        open_set = [(f_score[start], start)]
        heapq.heapify(open_set)
        
        # Set of discovered nodes that need to be evaluated
        open_set_hash = {start}
        
        # Map to store parent nodes for reconstructing path
        came_from = {}
        
        # While there are nodes to explore
        while open_set_hash:
            # Get node with lowest f_score
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            # If goal is reached
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                
                # Set path
                self.path = path
                self.costmap.set_path(self.path)
                print(f"A* path planned with {len(self.path)} steps")
                return
            
            # Generate possible moves
            neighbors = self._get_neighbors(current)
            
            # Process each neighbor
            for neighbor in neighbors:
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + self._distance(current, neighbor)
                
                # If this path is better than previous one
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    # Update path and costs
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)
                    
                    # Add to open set if not already there
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # If we reach here, no path was found
        print("No path found with A* algorithm")
        return
        
    def _get_neighbors(self, pos):
        """Get valid neighboring positions."""
        row, col = pos
        neighbors = []
        
        # Direction vectors: right, down, left, up
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # Add diagonals if allowed
        if self.allow_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        # Check each direction
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            # Check if position is within bounds
            if (0 <= new_row < self.costmap.grid_height and 
                0 <= new_col < self.costmap.grid_width):
                
                # Check if position is not an obstacle
                if self.costmap.get_cell(new_row, new_col) == 0:
                    # For diagonal moves, also check that we can move horizontally and vertically
                    if abs(dr) == 1 and abs(dc) == 1:
                        # Check horizontal
                        if self.costmap.get_cell(row, col + dc) != 0:
                            continue
                        # Check vertical
                        if self.costmap.get_cell(row + dr, col) != 0:
                            continue
                    
                    neighbors.append((new_row, new_col))
        
        return neighbors
        
    def _heuristic(self, pos, goal):
        """Calculate heuristic value between positions."""
        row, col = pos
        goal_row, goal_col = goal
        
        if self.heuristic == "manhattan":
            # Manhattan distance
            return abs(row - goal_row) + abs(col - goal_col)
        elif self.heuristic == "chebyshev":
            # Chebyshev distance (allows diagonal movement at same cost)
            return max(abs(row - goal_row), abs(col - goal_col))
        else:
            # Default: Euclidean distance
            return math.sqrt((row - goal_row)**2 + (col - goal_col)**2)
            
    def _distance(self, pos1, pos2):
        """Calculate distance between positions."""
        row1, col1 = pos1
        row2, col2 = pos2
        
        # Calculate Euclidean distance
        return math.sqrt((row1 - row2)**2 + (col1 - col2)**2)


class RRTAlgorithm(BaseAlgorithm):
    """Rapidly-exploring Random Tree (RRT) algorithm implementation for path planning."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize RRT algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.max_iterations = 1000   # Maximum iterations for the algorithm
        self.step_size = 3           # Step size for extending tree
        self.goal_sample_rate = 0.1  # Probability of sampling goal
        self.goal_threshold = 5      # Distance threshold to consider goal reached
        
    def plan_path(self):
        """Plan path using RRT algorithm."""
        print("Planning path with RRT algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        # Check if goal is valid (not an obstacle)
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        # Initialize trees
        nodes = [start]  # List of nodes in the tree
        parent = {start: None}  # Dictionary mapping nodes to their parents
        
        # RRT loop
        for i in range(self.max_iterations):
            # Sample random point
            if random.random() < self.goal_sample_rate:
                # Sample goal with some probability
                random_point = goal
            else:
                # Sample random point from free space
                while True:
                    random_row = random.randint(0, self.costmap.grid_height - 1)
                    random_col = random.randint(0, self.costmap.grid_width - 1)
                    random_point = (random_row, random_col)
                    
                    # Check if point is not an obstacle
                    if self.costmap.get_cell(random_row, random_col) == 0:
                        break
            
            # Find nearest node in tree
            nearest_node = self._find_nearest(nodes, random_point)
            
            # Extend tree towards random point
            new_node = self._extend(nearest_node, random_point)
            
            # If extension was successful
            if new_node:
                # Add new node to tree
                nodes.append(new_node)
                parent[new_node] = nearest_node
                
                # Check if goal is reached
                if self._distance(new_node, goal) <= self.goal_threshold:
                    # Connect new node to goal if possible
                    if self._is_collision_free(new_node, goal):
                        nodes.append(goal)
                        parent[goal] = new_node
                        
                        # Reconstruct path
                        path = []
                        current = goal
                        while current is not None:
                            path.append(current)
                            current = parent[current]
                        path.reverse()
                        
                        # Smooth path
                        path = self._smooth_path(path)
                        
                        # Set path
                        self.path = path
                        self.costmap.set_path(self.path)
                        print(f"RRT path planned with {len(self.path)} steps after {i+1} iterations")
                        return
        
        # If we reach here, no path was found within iterations limit
        print("No path found with RRT algorithm within iteration limit")
        return
        
    def _find_nearest(self, nodes, point):
        """Find the nearest node in the tree to the given point."""
        nearest_node = nodes[0]
        min_dist = self._distance(nearest_node, point)
        
        for node in nodes[1:]:
            dist = self._distance(node, point)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
                
        return nearest_node
        
    def _extend(self, from_node, to_point):
        """Extend tree from node towards point."""
        # Calculate direction
        from_row, from_col = from_node
        to_row, to_col = to_point
        
        # Calculate distance
        dist = self._distance(from_node, to_point)
        
        # If distance is less than step size, use target point
        if dist <= self.step_size:
            new_node = to_point
        else:
            # Normalize direction vector
            dir_row = (to_row - from_row) / dist
            dir_col = (to_col - from_col) / dist
            
            # Calculate new node by moving step_size in direction
            new_row = int(from_row + dir_row * self.step_size)
            new_col = int(from_col + dir_col * self.step_size)
            
            # Ensure new node is within bounds
            new_row = max(0, min(self.costmap.grid_height - 1, new_row))
            new_col = max(0, min(self.costmap.grid_width - 1, new_col))
            
            new_node = (new_row, new_col)
        
        # Check if path is collision-free
        if self._is_collision_free(from_node, new_node):
            return new_node
        else:
            return None
            
    def _is_collision_free(self, from_node, to_node):
        """Check if path between nodes is collision-free."""
        from_row, from_col = from_node
        to_row, to_col = to_node
        
        # Bresenham's line algorithm to check points along the line
        dx = abs(to_col - from_col)
        dy = abs(to_row - from_row)
        sx = 1 if from_col < to_col else -1
        sy = 1 if from_row < to_row else -1
        err = dx - dy
        
        row, col = from_row, from_col
        
        while row != to_row or col != to_col:
            # Check if point is an obstacle
            if self.costmap.get_cell(row, col) != 0:
                return False
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                col += sx
            if e2 < dx:
                err += dx
                row += sy
                
            # Ensure point is within bounds
            if not (0 <= row < self.costmap.grid_height and 0 <= col < self.costmap.grid_width):
                return False
        
        # Check destination
        return self.costmap.get_cell(to_row, to_col) == 0
    
    def _smooth_path(self, path):
        """Smooth the path by removing unnecessary nodes."""
        if len(path) <= 2:
            return path
            
        # Start with the first point
        smoothed_path = [path[0]]
        current_index = 0
        
        while current_index < len(path) - 1:
            # Try to connect current point with points further along the path
            for i in range(len(path) - 1, current_index, -1):
                if self._is_collision_free(path[current_index], path[i]):
                    # Add this point to smoothed path
                    smoothed_path.append(path[i])
                    current_index = i
                    break
            else:
                # If no connection found, move to next point
                current_index += 1
                smoothed_path.append(path[current_index])
        
        return smoothed_path
    
    def _distance(self, pos1, pos2):
        """Calculate distance between positions."""
        row1, col1 = pos1
        row2, col2 = pos2
        
        # Calculate Euclidean distance
        return math.sqrt((row1 - row2)**2 + (col1 - col2)**2)


# Dictionary mapping card names to algorithm classes
PATH_PLANNING_ALGORITHMS = {
    'AStar': AStarAlgorithm,
    'RRT': RRTAlgorithm
} 