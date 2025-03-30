"""
Main module for the card game.
Handles game initialization and main loop.
"""
import sys
import pygame
from config import Config
from card import CardDeck


def main():
    """Main function to run the card game."""
    # Initialize pygame
    pygame.init()
    
    # Set up the display
    window_width, window_height = Config.get_window_dimensions()
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Card Game")
    
    # Create card deck
    deck = CardDeck()
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Collect events
        events = pygame.event.get()
        
        # Check for quit
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # Handle card events
        deck.handle_events(events)
        
        # Update game state
        deck.update()
        
        # Clear the screen
        screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw all game elements
        deck.draw(screen)
        
        # Update the display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)
    
    # Clean up
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


