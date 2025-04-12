"""
State module for managing game states and transitions.
"""
from config import Config

class GameState:
    """Class to manage game states and transitions."""
    
    def __init__(self):
        """Initialize the game state."""
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
