"""
GameManager module for managing the main game loop and states.
"""
import pygame
import os
import random
import time
from config import Config
from cardDeck import CardDeck 
from card import Card
from state import GameState
from stage import Stage
from costmap import Costmap

class GameManager:
    """
    Main game manager class that handles the game loop, states, and interactions.
    
    This class is responsible for:
    - Managing the game window and display
    - Handling user input and events
    - Coordinating between different game components
    - Managing game states and transitions
    - Controlling the camera and view
    - Running algorithms and simulations
    """

    def __init__(self):
        """
        Initialize the game manager with all necessary components and settings.
        
        Sets up:
        - Pygame window and display
        - Game components (Stage, CardDeck, GameState)
        - Costmap for navigation
        - Camera and view settings
        - Auto-start timer settings
        """
        pygame.init()
        
        # Set up the display
        self.window_width, self.window_height = Config.get_window_dimensions()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Card Game")
        
        # Initialize game components
        self.stage = Stage()
        self.card_deck = CardDeck(self.stage)
        self.game_state = GameState()  # Use new singleton pattern
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Check for PGM file
        pgm_file_path = os.path.join("data", "map.pgm")
        
        # Initialize costmap with appropriate resolution
        # Using 20 pixels per grid cell gives a good balance between detail and performance
        self.costmap = Costmap(
            rect_width=900,  # 45 * 20
            rect_height=460,  # 23 * 20
            resolution=20, 
            pgm_path=pgm_file_path if os.path.exists(pgm_file_path) else None
        )
        
        # Track if the last click was to place robot (True) or goal (False)
        self.place_robot_mode = True
        
        # Camera variables
        self.camera_y = 0
        self.target_camera_y = 0
        self.camera_speed = 0.05  # Speed of camera movement (0-1, 1 = instant)
        self.camera_animating = False
        
        # Timer for auto-starting algorithm
        self.algorithm_start_time = 0
        self.should_auto_start = False
        self.auto_start_delay = 2 
    
    def handle_events(self):
        """
        Handle all game events including:
        - Window events (quit)
        - Mouse movement and clicks
        - Keyboard input
        - Button interactions
        - Card interactions
        """
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle mouse movement for buttons
            elif event.type == pygame.MOUSEMOTION:
                # Send camera position as well
                self.stage.handle_mouse_motion(event.pos)
            
            # Handle key press for switching between placing robot/goal
            elif event.type == pygame.KEYDOWN:
                try:
                    if event.key == pygame.K_SPACE and self.game_state.current_state == "PLAYING":
                        self.reset_game()
                except Exception as e:
                    print(f"Error handling key press: {e}")
            
            # Handle button clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    # Send camera position as well
                    button_action = self.stage.handle_button_click(event.pos)
                    if button_action:
                        self.handle_button_action(button_action)
                    else:
                        # Check if click is on costmap
                        mouse_x, mouse_y = event.pos
                        rect_start = (147, -368 + self.camera_y)
                        rect_end = (1054, 87 + self.camera_y)
                        
                        if (rect_start[0] <= mouse_x <= rect_end[0] and 
                            rect_start[1] <= mouse_y <= rect_end[1]):
                            # Convert to costmap coordinates
                            costmap_x = mouse_x - rect_start[0]
                            costmap_y = mouse_y - rect_start[1]
                            
                            # Convert to grid coordinates with safety checks
                            row, col = self.costmap.px_to_grid(costmap_x, costmap_y)
                            
                            # Handle click with current mode
                            success = self.costmap.handle_click(row, col, self.place_robot_mode)
                            
                            if success:
                                if self.place_robot_mode:
                                    print(f"Robot placed at grid position ({row}, {col})")
                                    # Switch to goal placement mode after placing robot
                                    self.place_robot_mode = False
                                    print("Now placing: Goal (red)")
                                else:
                                    print(f"Goal set at grid position ({row}, {col})")
                except Exception as e:
                    print(f"Error handling button click: {e}")
                    # Continue without crashing
        
        try:
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
        except Exception as e:
            print(f"Error handling card events: {e}")
            # Continue without crashing
    
    def handle_button_action(self, action: str):
        """
        Handle button actions based on the action name.
        
        Args:
            action (str): The name of the action to perform
        """
        try:
            if action == "reset":
                self.reset_game()
            elif action == "start":
                self.start_game()
            elif action == "load_map":
                self.load_map()
            elif action == "place_robot":
                self.place_robot_mode = True
                print("Now placing: Robot (blue)")
            elif action == "place_goal":
                self.place_robot_mode = False
                print("Now placing: Goal (red)")
        except Exception as e:
            print(f"Error handling button action: {e}")
            # Continue without crashing
    
    def load_map(self):
        """
        Load a map from a PGM file.
        
        Attempts to load the map from the default path in the data directory.
        """
        try:
            # Default path for map file
            pgm_file_path = os.path.join("data", "map.pgm")
            if os.path.exists(pgm_file_path):
                success = self.costmap.load_pgm_map(pgm_file_path)
                if success:
                    print("Successfully loaded map from", pgm_file_path)
                else:
                    print("Failed to load map from", pgm_file_path)
            else:
                print("No map file found at", pgm_file_path)
        except Exception as e:
            print(f"Error loading map: {e}")
            # Continue without crashing
    
    def reset_game(self):
        """
        Reset the game to its initial state.
        
        This includes:
        - Removing cards from slots
        - Resetting the card deck
        - Changing game state
        - Resetting camera position
        - Showing all buttons
        - Stopping any running algorithm
        """
        try:
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
            
            # Reset to robot placement mode
            self.place_robot_mode = True
            
            # Show all buttons again
            for button in self.stage.buttons:
                button.set_visible(True)
            
            # Stop any running algorithm
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                self.current_algorithm.stop()
                self.current_algorithm = None
        except Exception as e:
            print(f"Error resetting game: {e}")
            # Continue without crashing
    
    def start_game(self):
        """
        Start the game and prepare for algorithm execution.
        
        This includes:
        - Changing game state
        - Setting up gameplay mode
        - Adjusting camera position
        - Hiding UI buttons
        - Setting up auto-start timer
        """
        try:
            print("[GameManager] Starting game...")
            # Change game state to PLAYING
            self.game_state.change_state("PLAYING")
            
            # Set state to gameplay mode
            self.card_deck.set_game_stage(True)
            
            # Set camera target position to move down half the screen (use positive value)
            self.target_camera_y = self.window_height / 1.8
            self.camera_animating = True
            
            # Hide all game buttons
            for button in self.stage.buttons:
                button.set_visible(False)
            
            # Set timer for auto-starting algorithm after delay
            self.algorithm_start_time = time.time()
            self.should_auto_start = True
            
            # Show message to user about auto-starting
            print("--------------------------------------------")
            print(f"Game will start automatically in {self.auto_start_delay} seconds")
            print("--------------------------------------------")
        except Exception as e:
            print(f"Error starting game: {e}")
            # Continue without crashing
    
    def run_algorithm(self):
        """Run the selected algorithm to navigate robot to goal."""
        try:
            print("[GameManager] Running algorithm...")
            
            # Check if robot and goal are set
            if not self.costmap.robot_pos or not self.costmap.goal_pos:
                print("Cannot start algorithm: Robot and goal positions must be set first")
                return
            
            # Get all cards in slots
            algorithm_cards = []
            for slot in self.stage.slots:
                if slot.card:
                    algorithm_cards.append(slot.card)
            
            if not algorithm_cards:
                print("Cannot start algorithm: Algorithm cards must be selected first")
                return
            
            # For testing, use the first card
            selected_card = algorithm_cards[0]
            print(f"Using algorithm: {selected_card.card_name} ({selected_card.card_type})")
            
            # Get algorithm class based on card type and name
            algorithm_class = None
            
            # Import algorithm modules
            from algorithms.navigation import NAVIGATION_ALGORITHMS
            from algorithms.collision_avoidance import COLLISION_AVOIDANCE_ALGORITHMS
            from algorithms.recovery import RECOVERY_ALGORITHMS
            
            # Look up algorithm class based on card type and name
            if selected_card.card_type == "Navigation":
                algorithm_class = NAVIGATION_ALGORITHMS.get(selected_card.card_name)
            elif selected_card.card_type == "Collision avoidance":
                algorithm_class = COLLISION_AVOIDANCE_ALGORITHMS.get(selected_card.card_name)
            elif selected_card.card_type == "Recovery":
                algorithm_class = RECOVERY_ALGORITHMS.get(selected_card.card_name)
            
            if not algorithm_class:
                print(f"Algorithm not found for card: {selected_card.card_name}")
                return
            
            # Create algorithm instance
            self.current_algorithm = algorithm_class(self.costmap)
            
            # Start algorithm
            success = self.current_algorithm.start()
            if not success:
                print("Failed to start algorithm")
                self.current_algorithm = None
                return
            
            print("--------------------------------------------")
            print(f"Algorithm {selected_card.card_name} is running, please wait...")
            print("--------------------------------------------")
        except Exception as e:
            print(f"Error starting algorithm: {e}")
            self.current_algorithm = None
            # Continue without crashing
    
    def update(self):
        """Update the game state."""
        try:
            # Update camera animation
            if self.camera_animating:
                diff = self.target_camera_y - self.camera_y
                if abs(diff) > 0.5:
                    self.camera_y += diff * self.camera_speed
                else:
                    self.camera_y = self.target_camera_y
                    self.camera_animating = False
            
            # Check if algorithm should auto-start
            if self.should_auto_start and time.time() - self.algorithm_start_time >= self.auto_start_delay:
                self.should_auto_start = False
                self.run_algorithm()
            
            # Update game state
            self.game_state.update()
            
            # Update cards
            self.card_deck.update()
            
            # Update algorithm if running
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                still_running = self.current_algorithm.update()
                if not still_running:
                    print("Algorithm completed or stopped.")
                    self.current_algorithm = None
        except Exception as e:
            print(f"Error updating game: {e}")
            # Continue without crashing
    
    def draw(self):
        """Draw all game elements."""
        try:
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
            
            # Draw costmap inside the rectangle
            self.costmap.draw(self.screen, rect_start)
            
            # Draw border in white, 3 pixels thick
            pygame.draw.rect(
                self.screen, 
                Config.WHITE_COLOR, 
                (rect_start[0], rect_start[1], rect_width, rect_height),
                3,  # Border thickness
                border_radius=10  # Rounded corners
            )
            
            # Draw buttons separately without camera offset
            for button in self.stage.buttons:
                button.draw(self.screen)
            
            # Update the display
            pygame.display.flip()
        except Exception as e:
            print(f"Error drawing game: {e}")
            # Continue without crashing
    
    def run(self):
        """Run the main game loop."""
        while self.running:
            try:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(60)
            except Exception as e:
                print(f"Error in game loop: {e}")
                # Continue without crashing
        
        pygame.quit() 
        
        
"""

game_state
card_deck.set_game_stage 

"""