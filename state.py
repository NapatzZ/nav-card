"""
Game state management module.
"""
from enum import Enum

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
            cls._instance.current_state = "PLAYING"
        return cls._instance
    
    def change_state(self, new_state: str):
        """
        Change the current game state.
        
        Args:
            new_state (str): New state to set
        """
        self.current_state = new_state
    
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
