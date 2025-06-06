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
            # ตรวจสอบว่ามี path หรือไม่ ถ้าไม่มีแสดงว่าการวางแผนล้มเหลว
            # ไม่ควรถือว่า completed เพราะอาจต้องพยายามหาเส้นทางอีกครั้ง
            # แต่ยังถือว่าไม่สำเร็จในการทำงานปัจจุบัน
            print(f"[BaseAlgorithm] No path available. Path planning may have failed.")
            self.is_completed = False
            self.is_running = False
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
                # คำนวณระยะห่างทั้งแบบ Manhattan และ Euclidean
                manhattan_dist = abs(self.robot_pos[0] - self.goal_pos[0]) + abs(self.robot_pos[1] - self.goal_pos[1])
                euclidean_dist = ((self.robot_pos[0] - self.goal_pos[0])**2 + (self.robot_pos[1] - self.goal_pos[1])**2)**0.5
                
                # ใช้เกณฑ์ที่เข้มงวดกว่าเดิม - ต้องใกล้เป้าหมายจริงๆ
                if manhattan_dist <= 1 and euclidean_dist <= 1.0:
                    print(f"[BaseAlgorithm] Goal reached! Manhattan distance: {manhattan_dist}, Euclidean distance: {euclidean_dist:.2f}")
                    # Set final position to exactly the goal position for visual clarity
                    self.costmap.set_robot_position(*self.goal_pos)
                    self.robot_pos = self.goal_pos
                    self.is_completed = True
                    self.is_running = False
                    print(f"{self.__class__.__name__}: Path completed - Goal reached")
                    return False
        else:
            # ตรวจสอบว่าถึงเป้าหมายแล้วจริงๆ ก่อนจะถือว่าเสร็จสิ้น
            if self.robot_pos and self.goal_pos:
                manhattan_dist = abs(self.robot_pos[0] - self.goal_pos[0]) + abs(self.robot_pos[1] - self.goal_pos[1])
                if manhattan_dist <= 1:
                    self.is_completed = True
                    self.is_running = False
                    print(f"{self.__class__.__name__}: Path completed - Goal reached")
                else:
                    # ถ้ายังห่างจากเป้าหมายอยู่ ให้ถือว่ายังไม่สำเร็จ แม้ว่าจะสิ้นสุดเส้นทางแล้ว
                    print(f"{self.__class__.__name__}: Path completed but goal not reached! Distance: {manhattan_dist}")
                    self.is_completed = False
                    self.is_running = False
            else:
                # ถ้าไม่มีตำแหน่งเป้าหมายหรือหุ่นยนต์ ให้ถือว่าเสร็จสิ้นแต่ไม่สำเร็จ
                self.is_completed = False
                self.is_running = False
                print(f"{self.__class__.__name__}: Path completed but no robot/goal position")
            
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