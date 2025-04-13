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
    VALID_AREA_PADDING = 20  # เพิ่มระยะห่างจากขอบ
    VALID_AREA_ALPHA = 200  # ความโปร่งใสของ valid area
    
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
            "Collision_avoidance": (int(window_width * (3/6)), window_height // 2),  # Center
            "Recovery": (int(window_width * (5/6)), window_height // 2),  # Right
            "deck": (int(window_width * 0.5), int(window_height * 0.85))  # Bottom
        }
    
    @staticmethod
    def get_area_labels():
        """Get labels for card placement areas."""
        return {
            "Navigation": "Navigation",
            "Collision_avoidance": "Collision_avoidance",
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
        return ["Navigation", "Collision_avoidance", "Recovery"]
    
    @staticmethod
    def get_card_names():
        """Get valid card names for each type."""
        return {
            "Navigation": ["AStar", "WallFollowing", "RRT", "GreedySearch", "Dijkstra"],
            "Collision_avoidance": ["DWA", "Bug", "VFH"],
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
        
    