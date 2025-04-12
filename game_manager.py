"""
GameManager module for managing the main game loop and states.
"""
import pygame
from config import Config
from card import CardDeck
from state import GameState

class GameManager:
    """Class to manage the main game loop and states."""
    
    def __init__(self):
        """Initialize the game manager."""
        pygame.init()
        
        # Set up the display
        self.window_width, self.window_height = Config.get_window_dimensions()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Card Game")
        
        # Initialize game components
        self.card_deck = CardDeck()
        self.game_state = GameState()
        self.clock = pygame.time.Clock()
        self.running = True
    
    def handle_events(self):
        """Handle all game events."""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        
        # Handle card events
        self.card_deck.handle_events(events)
    
    def update(self):
        """Update game state."""
        self.card_deck.update()
        self.game_state.update()
    
    def draw(self):
        """Draw all game elements."""
        # Clear the screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw game elements
        self.card_deck.draw(self.screen)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):
        """Run the main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit() 