"""
Game state management module.
"""
from enum import Enum

# เพิ่ม Enum สำหรับเก็บสถานะเกม
class GameStateEnum(Enum):
    LOGIN = "LOGIN"
    CARD_CHOOSING = "CARD_CHOOSING"
    PLAYING = "PLAYING"
    FINISH = "FINISH"
    PAUSE = "PAUSE"

class GameState:
    """
    Singleton class for managing game state.
    
    This class ensures only one instance exists throughout the game,
    providing centralized state management.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            # Create new instance if none exists
            cls._instance = super(GameState, cls).__new__(cls)
            # Initialize first instance
            cls._instance.current_state = GameStateEnum.LOGIN.value  # เริ่มต้นที่หน้าล็อกอิน
            # เพิ่มตัวแปรสำหรับเก็บข้อมูลด่านปัจจุบัน
            cls._instance.current_level = 1
            # เก็บข้อมูลด่านสูงสุดที่ผ่านแล้ว
            cls._instance.highest_completed_level = 0
            # เก็บรายชื่อการ์ดที่ปลดล็อกแล้ว
            cls._instance.unlocked_cards = {
                "Navigation": ["DFS"],  # เริ่มต้นมีแค่ DFS
                "Collision avoidance": [],
                "Recovery": []
            }
            # เก็บข้อมูลการ์ดที่จะปลดล็อกในแต่ละด่าน
            cls._instance.level_unlocks = {
                # ด่าน: [{"type": ประเภทการ์ด, "name": ชื่อการ์ด}, ...]
                1: [],  # ด่านแรกมี DFS อยู่แล้ว
                2: [{"type": "Navigation", "name": "BFS"}],
                3: [{"type": "Recovery", "name": "SpinInPlace"}, {"type": "Recovery", "name": "StepBack"}],
                4: [{"type": "Collision avoidance", "name": "VFH"}],
                5: [{"type": "Navigation", "name": "Dijkstra"}],
                6: [{"type": "Navigation", "name": "AStar"}],
                7: [{"type": "Collision avoidance", "name": "Bug"}],
                8: [{"type": "Navigation", "name": "RRT"}],
                9: [],
                10: [],
                11: []
            }
            # เก็บชื่อผู้ใช้
            cls._instance.username = ""
        return cls._instance
    
    def change_state(self, new_state: str):
        """
        Change the current game state.
        
        Args:
            new_state (str): New state to set
        """
        # ตรวจสอบว่า new_state เป็นค่าที่ถูกต้อง
        if new_state in [state.value for state in GameStateEnum]:
            self.current_state = new_state
        else:
            print(f"Invalid game state: {new_state}")
    
    def get_state(self) -> str:
        """
        Get the current game state.
        
        Returns:
            str: Current game state
        """
        return self.current_state
    
    def update(self):
        """Update game state logic."""
        pass
        
    def advance_level(self):
        """
        เลื่อนไปยังด่านถัดไปและปลดล็อกการ์ดใหม่
        
        Returns:
            list: รายการการ์ดที่ปลดล็อกใหม่
        """
        # บันทึกว่าด่านปัจจุบันผ่านแล้ว
        if self.current_level > self.highest_completed_level:
            self.highest_completed_level = self.current_level
        
        # เพิ่มระดับด่าน
        self.current_level += 1
        if self.current_level > 11:
            self.current_level = 11  # จำกัดไว้ที่ 11 ด่าน
            return []
            
        # ปลดล็อกการ์ดใหม่เฉพาะเมื่อเพิ่งผ่านด่านนี้เป็นครั้งแรก
        newly_unlocked = []
        if self.current_level <= self.highest_completed_level + 1:
            for card_info in self.level_unlocks.get(self.current_level, []):
                card_type = card_info["type"]
                card_name = card_info["name"]
                
                # เพิ่มการ์ดที่ปลดล็อกใหม่
                if card_name not in self.unlocked_cards[card_type]:
                    self.unlocked_cards[card_type].append(card_name)
                    newly_unlocked.append({"type": card_type, "name": card_name})
                
        return newly_unlocked
        
    def get_unlocked_cards(self):
        """
        รับรายการการ์ดที่ปลดล็อกแล้วทั้งหมด
        
        Returns:
            dict: พจนานุกรมที่มีคีย์เป็นประเภทการ์ดและค่าเป็นรายชื่อการ์ด
        """
        return self.unlocked_cards
        
    def get_current_level(self):
        """
        รับหมายเลขด่านปัจจุบัน
        
        Returns:
            int: หมายเลขด่านปัจจุบัน
        """
        return self.current_level
        
    def reset_progress(self):
        """
        รีเซ็ตความก้าวหน้าของเกม กลับไปเริ่มที่ด่าน 1 และมีเฉพาะการ์ด DFS
        """
        self.current_level = 1
        self.highest_completed_level = 0
        self.unlocked_cards = {
            "Navigation": ["DFS"],
            "Collision avoidance": [],
            "Recovery": []
        }
        
    def complete_current_level(self):
        """
        บันทึกว่าด่านปัจจุบันผ่านแล้ว
        """
        if self.current_level > self.highest_completed_level:
            self.highest_completed_level = self.current_level
            return True
        return False
        
    def can_advance_to_level(self, level):
        """
        ตรวจสอบว่าสามารถไปยังด่านที่กำหนดได้หรือไม่
        
        Args:
            level (int): ด่านที่ต้องการไป
            
        Returns:
            bool: True ถ้าสามารถไปได้, False ถ้าไม่สามารถไปได้
        """
        # สามารถไปด่านที่ต่ำกว่าหรือเท่ากับด่านสูงสุดที่ผ่านแล้ว + 1 ได้
        return level <= self.highest_completed_level + 1
        
    def set_username(self, username):
        """
        กำหนดชื่อผู้ใช้
        
        Args:
            username (str): ชื่อผู้ใช้
        """
        self.username = username
        
    def get_username(self):
        """
        รับชื่อผู้ใช้
        
        Returns:
            str: ชื่อผู้ใช้
        """
        return self.username
