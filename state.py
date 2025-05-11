"""
Game state management module.
"""
from enum import Enum

# Game state enum
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
            cls._instance.current_state = GameStateEnum.LOGIN.value  # Start at login screen
            # Add variable to store current level
            cls._instance.current_level = 1
            # Store highest level completed
            cls._instance.highest_completed_level = 0
            # Store list of unlocked cards
            cls._instance.unlocked_cards = {
                "Navigation": ["DFS"],  # Start with only DFS
                "Collision avoidance": [],
                "Recovery": []
            }
            # Store card unlock data for each level
            cls._instance.level_unlocks = {
                # Level: [{"type": card type, "name": card name}, ...]
                1: [],  # First level already has DFS
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
            # Store username
            cls._instance.username = ""
        return cls._instance
    
    def change_state(self, new_state: str):
        """
        Change the current game state.
        
        Args:
            new_state (str): New state to set
        """
        # Check if new_state is valid
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
        Advance to the next level and unlock new cards
        
        Returns:
            list: List of newly unlocked cards
        """
        print(f"[GameState] Advancing from level {self.current_level}")
        
        # Record that current level is completed
        if self.current_level > self.highest_completed_level:
            self.highest_completed_level = self.current_level
            print(f"[GameState] Updated highest completed level to {self.highest_completed_level}")
        
        # Increase level
        self.current_level += 1
        if self.current_level > 11:
            self.current_level = 11  # Limit to 11 levels
            print(f"[GameState] Reached maximum level (11)")
            return []
            
        print(f"[GameState] Now at level {self.current_level}")
            
        # Unlock new cards only when passing this level for the first time
        newly_unlocked = []
        
        # Get cards to unlock for this level
        cards_to_unlock = self.level_unlocks.get(self.current_level, [])
        print(f"[GameState] Found {len(cards_to_unlock)} potential cards to unlock for level {self.current_level}")
            
        # Process each card in the level unlock list
        for card_info in cards_to_unlock:
            card_type = card_info["type"]
            card_name = card_info["name"]
            
            # Add newly unlocked card if not already unlocked
            if card_name not in self.unlocked_cards[card_type]:
                self.unlocked_cards[card_type].append(card_name)
                newly_unlocked.append({"type": card_type, "name": card_name})
                print(f"[GameState] Unlocked new card: {card_type} - {card_name}")
                
        print(f"[GameState] Unlocked {len(newly_unlocked)} new cards")
        return newly_unlocked
        
    def get_unlocked_cards(self):
        """
        Get list of all unlocked cards
        
        Returns:
            dict: Dictionary with keys as card types and values as card names
        """
        return self.unlocked_cards
        
    def get_current_level(self):
        """
        Get current level number
        
        Returns:
            int: Current level number
        """
        return self.current_level
        
    def reset_progress(self):
        """
        Reset game progress, back to level 1 with only DFS card
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
        Record that current level is completed
        
        Returns:
            bool: True if this level was just completed for the first time
        """
        if self.current_level > self.highest_completed_level:
            self.highest_completed_level = self.current_level
            return True
        return False
        
    def can_advance_to_level(self, level):
        """
        Check if player can advance to specified level
        
        Args:
            level (int): Level to check
            
        Returns:
            bool: True if can advance, False if not
        """
        # Can go to levels lower than or equal to highest completed level + 1
        return level <= self.highest_completed_level + 1
        
    def set_username(self, username):
        """
        Set username
        
        Args:
            username (str): Username
        """
        self.username = username
        
    def get_username(self):
        """
        Get username
        
        Returns:
            str: Username
        """
        return self.username
