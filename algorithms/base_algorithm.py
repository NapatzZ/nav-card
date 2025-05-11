"""
Base algorithm class for all card algorithms.
"""
import time

class BaseAlgorithm:
    """Base class for all algorithm implementations."""
    
    def __init__(self, costmap, robot_pos=None, goal_pos=None):
        """Initialize the algorithm.
        
        Args:
            costmap: Reference to the costmap object
            robot_pos: Initial robot position (row, col) or None
            goal_pos: Goal position (row, col) or None
        """
        self.costmap = costmap
        self.robot_pos = robot_pos or costmap.robot_pos
        self.goal_pos = goal_pos or costmap.goal_pos
        self.path = []
        self.current_path_index = 0
        self.is_running = False
        self.is_completed = False
        self.step_delay = 0.2  # เวลาหน่วง (วินาที) ระหว่างแต่ละสเต็ป
        self.last_step_time = 0  # เวลาของสเต็ปล่าสุด
        
    def start(self):
        """Start the algorithm execution."""
        if self.robot_pos is None or self.goal_pos is None:
            print("Cannot start algorithm: robot or goal position not set.")
            return False
            
        self.is_running = True
        self.is_completed = False
        self.current_path_index = 0
        self.last_step_time = time.time()  # เริ่มจับเวลา
        self.plan_path()
        return True
        
    def stop(self):
        """Stop the algorithm execution."""
        self.is_running = False
        
    def reset(self):
        """Reset the algorithm state."""
        self.is_running = False
        self.is_completed = False
        self.current_path_index = 0
        self.path = []
        
    def update(self):
        """Update the algorithm state.
        
        Returns:
            bool: True if algorithm is still running, False if completed or stopped
        """
        if not self.is_running or self.is_completed:
            return False
            
        if not self.path:
            self.is_completed = True
            return False
        
        # ตรวจสอบว่าถึงเวลาที่จะทำสเต็ปต่อไปหรือไม่
        current_time = time.time()
        if current_time - self.last_step_time < self.step_delay:
            return True  # ยังไม่ถึงเวลา ส่งคืน True เพื่อให้อัลกอริทึมยังคงทำงานต่อ
            
        # Move robot along the path
        if self.current_path_index < len(self.path):
            # Update robot position
            new_pos = self.path[self.current_path_index]
            self.costmap.set_robot_position(*new_pos)
            self.robot_pos = new_pos
            self.current_path_index += 1
            self.last_step_time = current_time  # อัปเดตเวลาล่าสุด
            
            # Check if we've reached the goal
            if self.robot_pos and self.goal_pos:
                distance = abs(self.robot_pos[0] - self.goal_pos[0]) + abs(self.robot_pos[1] - self.goal_pos[1])
                if distance <= 1:  # ถ้าอยู่ในระยะห่างไม่เกิน 1 ช่อง ถือว่าถึงเป้าหมายแล้ว
                    print(f"[BaseAlgorithm] Goal reached! Distance: {distance}")
                    # Set final position to exactly the goal position for visual clarity
                    self.costmap.set_robot_position(*self.goal_pos)
                    self.robot_pos = self.goal_pos
                    self.is_completed = True
                    self.is_running = False
                    print(f"{self.__class__.__name__}: Path completed - Goal reached")
                    return False
        else:
            # Reached the end of the path
            self.is_completed = True
            self.is_running = False
            print(f"{self.__class__.__name__}: Path completed")
            
        return self.is_running
        
    def plan_path(self):
        """Plan the path from robot to goal.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement plan_path()")
        
    def get_name(self):
        """Get the name of the algorithm.
        
        Returns:
            str: Algorithm name
        """
        return self.__class__.__name__ 