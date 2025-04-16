"""
GameManager module for managing the main game loop and states.
"""
import pygame
from config import Config
from cardDeck import CardDeck 
from card import Card
from state import GameState
from stage import Stage

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
        self.stage = Stage()
        self.card_deck = CardDeck(self.stage)
        self.game_state = GameState()
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Camera variables
        self.camera_y = 0
        self.target_camera_y = 0
        self.camera_speed = 0.05  # Speed of camera movement (0-1, 1 = instant)
        self.camera_animating = False
    
    def handle_events(self):
        """Handle all game events."""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle mouse movement for buttons
            elif event.type == pygame.MOUSEMOTION:
                # Send camera position as well
                self.stage.handle_mouse_motion(event.pos, (0, self.camera_y))
            
            # Handle button clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Send camera position as well
                button_action = self.stage.handle_button_click(event.pos, (0, self.camera_y))
                if button_action:
                    self.handle_button_action(button_action)
        
        # Handle card events with camera offset
        # Create new events with adjusted mouse position
        adjusted_events = []
        for event in events:
            # Adjust position for mouse-related events
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                # Create a copy of the event
                adjusted_event = pygame.event.Event(event.type, dict(event.__dict__))
                # Adjust pos value if it exists
                if hasattr(adjusted_event, 'pos'):
                    adjusted_event.pos = (
                        adjusted_event.pos[0], 
                        adjusted_event.pos[1] - int(self.camera_y)
                    )
                adjusted_events.append(adjusted_event)
            else:
                adjusted_events.append(event)
        
        # Send adjusted events to card_deck
        self.card_deck.handle_events(adjusted_events)
    
    def handle_button_action(self, action: str):
        """Handle button clicks.
        
        Args:
            action (str): Name of the action from the clicked button
        """
        if action == "reset":
            self.reset_game()
        elif action == "start":
            self.start_game()
    
    def reset_game(self):
        """Reset the game to initial state by moving all cards from stage back to deck."""
        print("[GameManager] Resetting game...")
        
        # Remove cards from all slots
        for slot in self.stage.slots:
            slot.card = None
        
        # Call reset_cards from card_deck
        self.card_deck.reset_cards()
        
        # Change game state to PLAYING
        self.game_state.change_state("PLAYING")
        
        # Set state to card selection mode (not gameplay mode)
        self.card_deck.set_game_stage(False)
        
        # Reset camera to initial position
        self.target_camera_y = 0
        self.camera_animating = True
    
    def start_game(self):
        """Start the game."""
        print("[GameManager] Starting game...")
        # Change game state to PLAYING
        self.game_state.change_state("PLAYING")
        
        # Set state to gameplay mode
        self.card_deck.set_game_stage(True)
        
        # Set camera target position to move down half the screen (use positive value)
        self.target_camera_y = self.window_height / 1.8
        self.camera_animating = True
    
    def update(self):
        """Update game state."""
        self.card_deck.update()
        self.game_state.update()
        
        # Update camera position (smooth animation)
        if self.camera_animating:
            # Calculate distance between current position and target
            camera_diff = self.target_camera_y - self.camera_y
            
            # If distance is very small, consider target reached
            if abs(camera_diff) < 0.5:
                self.camera_y = self.target_camera_y
                self.camera_animating = False
            else:
                # Move camera smoothly toward target
                self.camera_y += camera_diff * self.camera_speed
    
    def draw(self):
        """Draw all game elements."""
        # Clear the screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Find card being dragged
        dragging_card = None
        for card in self.card_deck.cards:
            if card.dragging:
                dragging_card = card
                break
        
        # Create offset for drawing everything based on camera position
        camera_offset = (0, self.camera_y)
        
        # Draw stage first (background and slots) with camera offset
        self.stage.draw(self.screen, dragging_card, camera_offset)
        
        # Draw game elements with camera offset
        self.card_deck.draw(self.screen, camera_offset)
        
        # Draw rectangle for game screen
        # Adjust position according to camera_offset
        rect_start = (147, -368 + self.camera_y)
        rect_end = (1054, 87 + self.camera_y)
        rect_width = rect_end[0] - rect_start[0]
        rect_height = rect_end[1] - rect_start[1]
        
        # Draw border in white, 3 pixels thick
        pygame.draw.rect(
            self.screen, 
            Config.WHITE_COLOR, 
            (rect_start[0], rect_start[1], rect_width, rect_height),
            3,  # Border thickness
            border_radius=10  # Rounded corners
        )
        
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