"""
State module for managing game states and transitions.
"""
from config import Config

class GameState:
    """Class to manage game states and transitions using Singleton pattern."""
    
    # คลาส variable สำหรับเก็บ instance เดียว
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of GameState.
        
        Returns:
            GameState: The singleton instance
        """
        if cls._instance is None:
            cls._instance = GameState()
        return cls._instance
    
    def __init__(self):
        """Initialize the game state."""
        # ถ้ามี instance อยู่แล้ว ให้คืนค่า instance เดิม
        if GameState._instance is not None:
            return
        
        # ตั้งค่า instance แรก
        GameState._instance = self
        
        self.current_state = "PLAYING"  # Initial state
        self.states = {
            "PLAYING": self._handle_playing,
            "PAUSED": self._handle_paused,
            "GAME_OVER": self._handle_game_over
        }
    
    def update(self):
        """Update the current game state."""
        handler = self.states.get(self.current_state)
        if handler:
            handler()
    
    def change_state(self, new_state):
        """Change the current game state.
        
        Args:
            new_state (str): The new state to transition to
        """
        if new_state in self.states:
            self.current_state = new_state
    
    def _handle_playing(self):
        """Handle the playing state."""
        # Add game logic for playing state
        pass
    
    def _handle_paused(self):
        """Handle the paused state."""
        # Add game logic for paused state
        pass
    
    def _handle_game_over(self):
        """Handle the game over state."""
        # Add game logic for game over state
        pass
