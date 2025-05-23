"""
Configuration module for card game.
Contains all constants and settings for the game.
"""
import os
import glob
import pygame

class Config:
    """Class to store all configuration settings for the card game."""
    
    # Debug mode (0 = OFF, 1 = ON)
    DEBUG_MODE = 0  # Set to 0 to disable debug information
    
    # Log settings
    LOG_LEVEL = 1  # 0 = None, 1 = Critical only, 2 = Normal, 3 = Verbose/All
    LOG_MOUSE_POSITION = True  # Set to True to log mouse position when clicking
    LOG_STATE_CHANGES = True   # Set to True to log game state changes
    LOG_ALGORITHM_INFO = True  # Set to True to log algorithm selection and execution
    
    # Screen and window settings
    SCREEN_SCALE = 0.8  # 80% of screen size
    
    # Board dimensions
    BOARD_WIDTH = 1200
    BOARD_HEIGHT = 800
    BOARD_COLOR = (53, 101, 77)  # Dark green for card table
    
    # Card slot dimensions
    CARD_SLOT_WIDTH = 300
    CARD_SLOT_HEIGHT = 500
    CARD_SLOT_SPACING = 50
    CARD_SLOT_COLOR = (70, 120, 90)  # Slightly lighter green for empty areas
    
    # Colors
    BACKGROUND_COLOR = (53, 101, 77)  # Dark green for card table
    WHITE_COLOR = (255, 255, 255)
    BLACK_COLOR = (0, 0, 0)
    HIGHLIGHT_COLOR = (255, 255, 0, 180)  # Yellow for borders
    EMPTY_AREA_COLOR = (70, 120, 90)  # Slightly lighter green for empty areas
    
    # Card dimensions
    CARD_WIDTH_RATIO = 0.25  # 25% of window width
    CARD_HEIGHT_RATIO = 1.5  # Height:width ratio of 1.5
    CARD_BORDER_RADIUS_RATIO = 0.1  # 10% of card width
    
    # Valid placement areas
    VALID_AREA_SCALE = 1.4  # 140% of card size
    VALID_AREA_PADDING = 20  # Additional padding from edges
    VALID_AREA_ALPHA = 200  # Transparency of valid area
    
    # Preview settings
    PREVIEW_RADIUS_RATIO = 0.3  # 30% of window width
    PREVIEW_CENTER_OFFSET = 100  # Offset from bottom
    PREVIEW_ANGLE = 60  # Angle in degrees
    PREVIEW_ANIMATION_SPEED = 0.2
    PREVIEW_HOVER_SCALE = 1.2
    PREVIEW_HOVER_LIFT = 50    # Increased from 40 to 50
    
    # Shadow settings
    SHADOW_OFFSET = 5
    SHADOW_OPACITY = 64  # Alpha value for shadow
    
    # New constants for hover transition
    HOVER_TRANSITION_SPEED = 0.3  # Speed of hover state change (0-1)
    HOVER_TRANSITION_SPEED_OUT = 0.4  # Speed of hover state reduction (0-1)
    
    # Card hover settings
    HOVER_SCALE = 1.1
    
    @staticmethod
    def get_window_dimensions():
        """Calculate window dimensions based on actual screen size."""
        screen_info = pygame.display.Info()
        window_width = int(screen_info.current_w * Config.SCREEN_SCALE)
        window_height = int(screen_info.current_h * Config.SCREEN_SCALE)
        return window_width, window_height
    
    @staticmethod
    def get_card_dimensions(window_width):
        """Calculate card dimensions based on window width."""
        card_width = int(window_width * Config.CARD_WIDTH_RATIO)
        card_height = int(card_width * Config.CARD_HEIGHT_RATIO)
        return card_width, card_height
    
    @staticmethod
    def get_card_border_radius(card_width):
        """Calculate card border radius based on card width."""
        return int(card_width * Config.CARD_BORDER_RADIUS_RATIO)
    
    @staticmethod
    def get_area_positions(window_width, window_height):
        """Get positions for all card placement areas."""
        # Divide the area into 3 symmetrical sections with equal spacing
        # Use the ratio 1/6, 3/6, 5/6 of the screen width
        return {
            "Navigation": (int(window_width * (1/6)), window_height // 2),  # Left
            "Collision avoidance": (int(window_width * (3/6)), window_height // 2),  # Center
            "Recovery": (int(window_width * (5/6)), window_height // 2),  # Right
            "deck": (int(window_width * 0.5), int(window_height * 0.85))  # Bottom
        }
    
    @staticmethod
    def get_area_labels():
        """Get labels for card placement areas."""
        return {
            "Navigation": "Navigation",
            "Collision avoidance": "Collision avoidance",
            "Recovery": "Recovery"
        }
    
    @staticmethod
    def get_valid_area_dimensions(card_width, card_height):
        """Calculate dimensions for valid placement areas."""
        valid_width = int(card_width * Config.VALID_AREA_SCALE)
        valid_height = int(card_height * Config.VALID_AREA_SCALE)
        return valid_width, valid_height
    
    @staticmethod
    def get_preview_settings(window_width, window_height):
        """Get settings for the preview mode."""
        return {
            'radius': int(window_height * 0.4),  # 40% of screen height
            'center': (window_width // 2, int(window_height * 0.6)),  # Center horizontally, 60% of height vertically
            'hover_lift': 40,  # Amount to lift when hovering
            'animation_speed': 0.2  # Animation speed (0-1)
        }
    
    @staticmethod
    def get_shadow_settings():
        """Get shadow settings for cards."""
        return {
            'offset': Config.SHADOW_OFFSET,
            'opacity': Config.SHADOW_OPACITY
        }
    
    @staticmethod
    def get_card_types():
        """Get valid card types."""
        return ["Navigation", "Collision avoidance", "Recovery"]
    
    @staticmethod
    def get_card_names():
        """Get valid card names for each type."""
        return {
            "Navigation": ["DFS", "BFS", "Dijkstra", "AStar", "RRT"],
            "Collision avoidance": ["VFH", "BUG"],
            "Recovery": ["SpinInPlace", "StepBack"]
        }
    
    @staticmethod
    def load_card_image(card_name):
        """Load card image from assets folder."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "assets", f"{card_name}.png")
        image_files = glob.glob(image_path)
        
        if not image_files:
            # Create a placeholder if image is not found
            return None
        
        return image_files[0]
    
    @staticmethod
    def get_debug_settings():
        """Get debug information display settings."""
        return {
            'enabled': Config.DEBUG_MODE == 1,
            'font_size': 24,
            'bg_color': (0, 0, 0, 150),  # Semi-transparent black
            'text_color': (255, 255, 255),  # White text
            'padding': 10,
            'line_height': 25
        }
    
    @staticmethod
    def log(module, message, level=2, show_pos=False, mouse_pos=None):
        """
        Central logging function that respects log level settings.
        
        Args:
            module (str): Module name (e.g., "GameManager", "Stage")
            message (str): Message to log
            level (int): Log level (1=Critical, 2=Normal, 3=Verbose)
            show_pos (bool): Whether to include mouse position
            mouse_pos (tuple): Current mouse position (x, y)
        """
        # Skip if log level is too low
        if Config.LOG_LEVEL < level:
            return
            
        # Format basic message
        log_msg = f"[{module}] {message}"
        
        # Add mouse position if requested and available
        if show_pos and Config.LOG_MOUSE_POSITION and mouse_pos:
            log_msg += f" | Mouse: {mouse_pos}"
            
        # Print the message
        print(log_msg)
        
    