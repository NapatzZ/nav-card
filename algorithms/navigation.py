"""
Navigation algorithms for robot path planning.

This module implements various path planning algorithms:
- A* (A-Star)
- RRT (Rapidly-exploring Random Tree)
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- Dijkstra's Algorithm
"""
import random
import math
import heapq
from .base_algorithm import BaseAlgorithm

class AStarAlgorithm(BaseAlgorithm):
    """
    A* algorithm implementation for path planning.
    
    A* is an informed search algorithm that uses a heuristic function to estimate
    the cost to reach the goal. It combines the advantages of both Dijkstra's
    algorithm and greedy best-first search.
    
    Attributes:
        allow_diagonal (bool): Whether to allow diagonal movement
        heuristic (str): Type of heuristic to use ("manhattan", "euclidean", "chebyshev")
    """
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """
        Initialize A* algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.allow_diagonal = True
        self.heuristic = "euclidean"
        
    def plan_path(self):
        """
        Plan path using A* algorithm.
        
        The algorithm:
        1. Starts from the robot position
        2. Explores neighboring cells using a priority queue
        3. Uses heuristic function to estimate cost to goal
        4. Reconstructs path when goal is reached
        """
        print("Planning path with A* algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        open_set = [(f_score[start], start)]
        heapq.heapify(open_set)
        open_set_hash = {start}
        came_from = {}
        
        while open_set_hash:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                
                self.path = path
                self.costmap.set_path(self.path)
                print(f"A* path planned with {len(self.path)} steps")
                return
            
            neighbors = self._get_neighbors(current)
            
            for neighbor in neighbors:
                tentative_g_score = g_score[current] + self._distance(current, neighbor)
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        print("No path found with A* algorithm")
        return
        
    def _get_neighbors(self, pos):
        """
        Get valid neighboring positions.
        
        Args:
            pos (tuple): Current position (row, col)
            
        Returns:
            list: List of valid neighboring positions
        """
        row, col = pos
        neighbors = []
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        if self.allow_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < self.costmap.grid_height and 
                0 <= new_col < self.costmap.grid_width):
                
                if self.costmap.get_cell(new_row, new_col) == 0:
                    if abs(dr) == 1 and abs(dc) == 1:
                        if self.costmap.get_cell(row, col + dc) != 0:
                            continue
                        if self.costmap.get_cell(row + dr, col) != 0:
                            continue
                    
                    neighbors.append((new_row, new_col))
        
        return neighbors
        
    def _heuristic(self, pos, goal):
        """
        Calculate heuristic value between positions.
        
        Args:
            pos (tuple): Current position (row, col)
            goal (tuple): Goal position (row, col)
            
        Returns:
            float: Heuristic value
        """
        row, col = pos
        goal_row, goal_col = goal
        
        if self.heuristic == "manhattan":
            return abs(row - goal_row) + abs(col - goal_col)
        elif self.heuristic == "chebyshev":
            return max(abs(row - goal_row), abs(col - goal_col))
        else:
            return math.sqrt((row - goal_row)**2 + (col - goal_col)**2)
            
    def _distance(self, pos1, pos2):
        """
        Calculate distance between positions.
        
        Args:
            pos1 (tuple): First position (row, col)
            pos2 (tuple): Second position (row, col)
            
        Returns:
            float: Euclidean distance between positions
        """
        row1, col1 = pos1
        row2, col2 = pos2
        return math.sqrt((row1 - row2)**2 + (col1 - col2)**2)


class RRTAlgorithm(BaseAlgorithm):
    """
    Rapidly-exploring Random Tree (RRT) algorithm implementation for path planning.
    
    RRT is a sampling-based algorithm that builds a tree of valid configurations
    by randomly sampling the configuration space and connecting samples to the tree.
    
    Attributes:
        max_iterations (int): Maximum number of iterations
        step_size (float): Maximum step size for tree expansion
        goal_sample_rate (float): Probability of sampling goal position
        goal_region_radius (float): Radius around goal to consider as reached
        search_radius (float): Radius to search for neighbors
        node_list (list): List of nodes in the tree
        path (list): Final planned path
    """
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """
        Initialize RRT algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position or None
            goal_pos: Goal position or None
        """
        super().__init__(costmap, robot_pos, goal_pos)
        self.max_iterations = 1000
        self.step_size = 1.0
        self.goal_sample_rate = 0.2
        self.goal_region_radius = 1.5
        self.search_radius = 2.0
        self.node_list = []
        self.path = []
        
    def plan_path(self):
        """
        Plan path using RRT algorithm.
        
        The algorithm:
        1. Starts with the robot position as root node
        2. Randomly samples points in the configuration space
        3. Connects samples to the nearest node in the tree
        4. Expands towards the goal with some probability
        5. Reconstructs path when goal is reached
        """
        print("Planning path with RRT algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        start_node = {'pos': start, 'parent': None, 'cost': 0}
        self.node_list = [start_node]
        
        for i in range(self.max_iterations):
            rand_node = self._get_random_node(goal)
            nearest_node = self._get_nearest_node(rand_node)
            new_node = self._steer(nearest_node, rand_node)
            
            if self._is_collision_free(nearest_node['pos'], new_node['pos']):
                neighbors = self._find_neighbors(new_node)
                new_node = self._choose_parent(neighbors, nearest_node, new_node)
                self.node_list.append(new_node)
                self._rewire(new_node, neighbors)
                
                if self._reached_goal(new_node['pos'], goal):
                    self.path = self._generate_final_path(new_node)
                    self.costmap.set_path(self.path)
                    print(f"RRT path planned with {len(self.path)} steps after {i+1} iterations")
                    return
        
        print("No path found with RRT algorithm within iteration limit")
        return
        
    def _get_random_node(self, goal):
        """
        Generate a random node in the map.
        
        Args:
            goal (tuple): Goal position (row, col)
            
        Returns:
            dict: Random node with position and cost
        """
        if random.random() < self.goal_sample_rate:
            return {'pos': goal, 'parent': None, 'cost': 0}
            
        while True:
            row = random.randint(0, self.costmap.grid_height - 1)
            col = random.randint(0, self.costmap.grid_width - 1)
            if self.costmap.get_cell(row, col) == 0:
                return {'pos': (row, col), 'parent': None, 'cost': 0}
    
    def _get_nearest_node(self, rand_node):
        """
        Find the nearest node in the tree to the random node.
        
        Args:
            rand_node (dict): Random node to find nearest neighbor for
            
        Returns:
            dict: Nearest node in the tree
        """
        min_dist = float('inf')
        nearest_node = None
        
        for node in self.node_list:
            dist = self._distance(node['pos'], rand_node['pos'])
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
                
        return nearest_node
    
    def _steer(self, from_node, to_node):
        """Steer from one node to another, step-by-step."""
        from_pos = from_node['pos']
        to_pos = to_node['pos']
        
        # Calculate direction
        dx = to_pos[1] - from_pos[1]
        dy = to_pos[0] - from_pos[0]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < self.step_size:
            new_pos = to_pos
        else:
            # Normalize direction
            dx = dx / dist * self.step_size
            dy = dy / dist * self.step_size
            
            # Calculate new position
            new_row = int(from_pos[0] + dy)
            new_col = int(from_pos[1] + dx)
            
            # Ensure within bounds
            new_row = max(0, min(self.costmap.grid_height - 1, new_row))
            new_col = max(0, min(self.costmap.grid_width - 1, new_col))
            
            new_pos = (new_row, new_col)
        
        return {'pos': new_pos, 'parent': from_node, 'cost': from_node['cost'] + self._distance(from_pos, new_pos)}
    
    def _is_collision_free(self, from_pos, to_pos):
        """Check if path between positions is collision-free."""
        # Bresenham's line algorithm
        dx = abs(to_pos[1] - from_pos[1])
        dy = abs(to_pos[0] - from_pos[0])
        sx = 1 if from_pos[1] < to_pos[1] else -1
        sy = 1 if from_pos[0] < to_pos[0] else -1
        err = dx - dy
        
        row, col = from_pos
        
        while row != to_pos[0] or col != to_pos[1]:
            if self.costmap.get_cell(row, col) != 0:  # Obstacle
                return False
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                col += sx
            if e2 < dx:
                err += dx
                row += sy
                
            if not (0 <= row < self.costmap.grid_height and 0 <= col < self.costmap.grid_width):
                return False
        
        return True
    
    def _find_neighbors(self, new_node):
        """Find nearby nodes within the search radius."""
        neighbors = []
        for node in self.node_list:
            if self._distance(node['pos'], new_node['pos']) < self.search_radius:
                neighbors.append(node)
        return neighbors
    
    def _choose_parent(self, neighbors, nearest_node, new_node):
        """Choose the best parent for the new node based on cost."""
        min_cost = nearest_node['cost'] + self._distance(nearest_node['pos'], new_node['pos'])
        best_node = nearest_node
        
        for neighbor in neighbors:
            cost = neighbor['cost'] + self._distance(neighbor['pos'], new_node['pos'])
            if cost < min_cost and self._is_collision_free(neighbor['pos'], new_node['pos']):
                best_node = neighbor
                min_cost = cost
        
        new_node['parent'] = best_node
        new_node['cost'] = min_cost
        return new_node
    
    def _distance(self, pos1, pos2):
        """
        Calculate distance between positions.
        
        Args:
            pos1 (tuple): First position (row, col)
            pos2 (tuple): Second position (row, col)
            
        Returns:
            float: Euclidean distance between positions
        """
        row1, col1 = pos1
        row2, col2 = pos2
        return math.sqrt((row1 - row2)**2 + (col1 - col2)**2)
    
    def _rewire(self, new_node, neighbors):
        """Rewire the tree by checking if any neighbor should adopt the new node as a parent."""
        for neighbor in neighbors:
            cost = new_node['cost'] + self._distance(new_node['pos'], neighbor['pos'])
            if cost < neighbor['cost'] and self._is_collision_free(new_node['pos'], neighbor['pos']):
                neighbor['parent'] = new_node
                neighbor['cost'] = cost
    
    def _reached_goal(self, pos, goal):
        """Check if the goal has been reached."""
        return self._distance(pos, goal) < self.goal_region_radius
    
    def _generate_final_path(self, goal_node):
        """Generate the final path from the start to the goal."""
        path = []
        node = goal_node
        
        while node is not None:
            path.append(node['pos'])
            node = node['parent']
            
        return path[::-1]  # Reverse path


class BFSAlgorithm(BaseAlgorithm):
    """Breadth-First Search algorithm implementation."""
    
    def plan_path(self):
        """Plan path using BFS algorithm."""
        print("Planning path with BFS algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        # Check if goal is valid (not an obstacle)
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        # Initialize queue and visited set
        queue = [(start, [start])]  # (position, path)
        visited = {start}
        
        # BFS loop
        while queue:
            current, path = queue.pop(0)
            
            # Check if goal is reached
            if current == goal:
                self.path = path[1:]  # Skip start position
                self.costmap.set_path(self.path)
                print(f"BFS path planned with {len(self.path)} steps")
                return
            
            # Get neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # Right, Down, Left, Up
                neighbor_row = current[0] + dr
                neighbor_col = current[1] + dc
                neighbor = (neighbor_row, neighbor_col)
                
                # Skip invalid or visited positions
                if not (0 <= neighbor_row < self.costmap.grid_height and 
                        0 <= neighbor_col < self.costmap.grid_width):
                    continue
                    
                if neighbor in visited:
                    continue
                    
                if self.costmap.get_cell(neighbor_row, neighbor_col) != 0:  # Not free
                    continue
                
                # Add to queue and visited set
                queue.append((neighbor, path + [neighbor]))
                visited.add(neighbor)
        
        print("BFS algorithm: No path found")


class DFSAlgorithm(BaseAlgorithm):
    """Depth-First Search algorithm implementation."""
    
    def plan_path(self):
        """Plan path using DFS algorithm."""
        print("Planning path with DFS algorithm...")
        self.path = []
        
        if not self.robot_pos or not self.goal_pos:
            return
            
        start = self.robot_pos
        goal = self.goal_pos
        
        # Check if goal is valid (not an obstacle)
        if self.costmap.get_cell(goal[0], goal[1]) != 0:
            print("Goal position is an obstacle. Cannot plan path.")
            return
        
        # Initialize stack and visited set
        stack = [(start, [start])]  # (position, path)
        visited = {start}
        
        # DFS loop
        while stack:
            current, path = stack.pop()
            
            # Check if goal is reached
            if current == goal:
                self.path = path[1:]  # Skip start position
                self.costmap.set_path(self.path)
                print(f"DFS path planned with {len(self.path)} steps")
                return
            
            # Get neighbors (in reverse order for DFS)
            for dr, dc in [(-1, 0), (0, -1), (1, 0), (0, 1)]:  # Up, Left, Down, Right
                neighbor_row = current[0] + dr
                neighbor_col = current[1] + dc
                neighbor = (neighbor_row, neighbor_col)
                
                # Skip invalid or visited positions
                if not (0 <= neighbor_row < self.costmap.grid_height and 
                        0 <= neighbor_col < self.costmap.grid_width):
                    continue
                    
                if neighbor in visited:
                    continue
                    
                if self.costmap.get_cell(neighbor_row, neighbor_col) != 0:  # Not free
                    continue
                
                # Add to stack and visited set
                stack.append((neighbor, path + [neighbor]))
                visited.add(neighbor)
        
        print("DFS algorithm: No path found")


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


# Dictionary mapping card names to algorithm classes
NAVIGATION_ALGORITHMS = {
    'AStar': AStarAlgorithm,
    'RRT': RRTAlgorithm,
    'BFS': BFSAlgorithm,
    'DFS': DFSAlgorithm,
    'Dijkstra': DijkstraAlgorithm
} 