class Config:
    # Screen and window settings
    _SCREEN_WIDTH = 1600
    _SCREEN_HEIGHT = 1200
    _WINDOW_SCALE = 0.8  # 80% of screen size
    
    # Colors
    _BACKGROUND_COLOR = (53, 101, 77)  # Dark green for card table
    _WHITE_COLOR = (255, 255, 255)
    _BLACK_COLOR = (0, 0, 0)
    _HIGHLIGHT_COLOR = (255, 255, 0, 180)  # Yellow for borders
    _HOVER_COLOR = (192, 192, 192, 180)  # Light gray for hover effect
    
    # Card dimensions
    _CARD_WIDTH_RATIO = 0.25  # 25% of window width
    _CARD_HEIGHT_RATIO = 1.5  # Height:width ratio of 1.5
    _CARD_BORDER_RADIUS_RATIO = 0.1  # 10% of card width
    
    # Card positions and area settings
    _DECK_POSITION_RATIO = (0.25, 0.5)  # 25% from left, centered vertically
    _COMMUNITY_POSITION_RATIO = (0.75, 0.5)  # 75% from left, centered vertically
    _VALID_AREA_SCALE = 1.4  # 140% of card size
    
    # Preview settings
    _PREVIEW_RADIUS_RATIO = 0.3  # 30% of window width
    _PREVIEW_CENTER_OFFSET = 100  # Offset from bottom
    _PREVIEW_ANGLE = 60  # Angle in degrees
    _PREVIEW_ANIMATION_SPEED = 0.1
    _PREVIEW_HOVER_SCALE = 1.1  # 10% larger on hover
    
    # Shadow settings
    _SHADOW_OFFSET = 5
    _SHADOW_OPACITY = 64  # Alpha value for shadow
    
    # Card types
    _VALID_CARD_TYPES = ["Navigation", "Collision_avoidance", "Recovery"]
    _VALID_CARD_NAMES = ["A_Star", "Wall_Following", "RRT", "Greedy_Search", "Dijkstra", 
                        "DWA", "Bug", "VFH", "Spin-in-Place", "Step-Back"]
    
    @classmethod
    def get_window_dimensions(cls, screen_info):
        """Calculate window dimensions based on actual screen size."""
        actual_width = screen_info.current_w
        actual_height = screen_info.current_h
        
        window_width = int(actual_width * cls._WINDOW_SCALE)
        window_height = int(actual_height * cls._WINDOW_SCALE)
        
        return window_width, window_height
    
    @classmethod
    def get_card_dimensions(cls, window_width):
        """Calculate card dimensions based on window width."""
        card_width = int(window_width * cls._CARD_WIDTH_RATIO)
        card_height = int(card_width * cls._CARD_HEIGHT_RATIO)
        
        return card_width, card_height
    
    @classmethod
    def get_card_border_radius(cls, card_width):
        """Calculate card border radius based on card width."""
        return int(card_width * cls._CARD_BORDER_RADIUS_RATIO)
    
    @classmethod
    def get_positions(cls, window_width, window_height):
        """Calculate positions for deck and community areas."""
        deck_position = (int(window_width * cls._DECK_POSITION_RATIO[0]), 
                         int(window_height * cls._DECK_POSITION_RATIO[1]))
        
        community_position = (int(window_width * cls._COMMUNITY_POSITION_RATIO[0]), 
                             int(window_height * cls._COMMUNITY_POSITION_RATIO[1]))
        
        return deck_position, community_position
    
    @classmethod
    def get_valid_area_dimensions(cls, card_width, card_height):
        """Calculate dimensions for valid placement areas."""
        valid_width = int(card_width * cls._VALID_AREA_SCALE)
        valid_height = int(card_height * cls._VALID_AREA_SCALE)
        
        return valid_width, valid_height
    
    @classmethod
    def get_preview_settings(cls, window_width, window_height):
        """Calculate preview mode settings."""
        preview_radius = int(window_width * cls._PREVIEW_RADIUS_RATIO)
        preview_center = (window_width // 2, 
                          window_height - cls._PREVIEW_CENTER_OFFSET)
        
        return {
            'radius': preview_radius,
            'center': preview_center,
            'angle': cls._PREVIEW_ANGLE,
            'animation_speed': cls._PREVIEW_ANIMATION_SPEED,
            'hover_scale': cls._PREVIEW_HOVER_SCALE
        }
    
    @classmethod
    def get_shadow_settings(cls):
        """Get shadow settings."""
        return {
            'offset': cls._SHADOW_OFFSET,
            'opacity': cls._SHADOW_OPACITY
        }
    
    @classmethod
    def load_image_of(cls, name):
        """Load card image from assets folder."""
        import os
        import glob
        
        print(f"\n****************Loading image for card: {name}****************")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "assets", f"{name}.png")
        print(f"Loading image from: {image_path}")
        image_path = glob.glob(image_path)
        print(f"Image path found: {image_path}")
        
        if not image_path:
            error_message = f"Image {name}.png not found in assets directory."
            error_line = f"**************** {error_message:^5} ****************"
            raise FileNotFoundError(error_line)      
        
        print("************************************************\n")
        return image_path[0]
    
    @classmethod
    def background_color(cls):
        return cls._BACKGROUND_COLOR
    
    @classmethod
    def white_color(cls):
        return cls._WHITE_COLOR
    
    @classmethod
    def black_color(cls):
        return cls._BLACK_COLOR
    
    @classmethod
    def highlight_color(cls):
        return cls._HIGHLIGHT_COLOR
    
    @classmethod
    def hover_color(cls):
        return cls._HOVER_COLOR
    
    @classmethod
    def valid_card_types(cls):
        return cls._VALID_CARD_TYPES
    
    @classmethod
    def valid_card_names(cls):
        return cls._VALID_CARD_NAMES