"""
Card module for the card game.
Contains classes for managing cards and card deck.
"""
import math
import pygame
from enum import Enum
from config import Config
from typing import Optional

class CardType(Enum):
    """Enum for card types."""
    NAVIGATION = "Navigation"
    COLLISION_AVOIDANCE = "Collision_avoidance"
    RECOVERY_BEHAVIOR = "Recovery"

class Card:
    """Class representing a card in the game."""
    
    def __init__(self, card_type, card_name):
        """Initialize a new card with the given type and name.

        Args:
            card_type (str): Type of the card (Navigation, Collision_avoidance, Recovery)
            card_name (str): Name of the card
        """
        self.__card_type = card_type
        self.__card_name = card_name
        
        # Get window dimensions
        self.__window_width, self.__window_height = Config.get_window_dimensions()
        
        # Card dimensions
        self.__width, self.__height = Config.get_card_dimensions(self.__window_width)
        self.__border_radius = Config.get_card_border_radius(self.__width)
        
        # Set up positions
        self.__position = (0, 0)  # Start at origin
        self.__original_position = self.__position
        
        # Load image and create shadow
        self.__load_image(card_name)
        self.__create_shadow()
        
        # Card states
        self.__current_area = None
        self.__dragging = False
        self.__drag_offset = (0, 0)
        self.__hovering = False
        self.__hovering_area = None
        self.__hovering_over_card = False
        self.__hover_scale = 1.0
        
        # Preview mode
        self.__in_preview = False
        self.__preview_index = -1
        self.__preview_total_cards = 0
        self.__preview_settings = Config.get_preview_settings(self.__window_width, self.__window_height)
        
        # Create rectangle for collision detection
        self.__rect = pygame.Rect(0, 0, self.__width, self.__height)
        self.__rect.center = self.__position
        
        # Add variables for drag animation
        self.__from_preview = False
        self.__prev_preview_position = None
        self.__animation_progress = 0.0
        self.__animation_speed = 0.2  # Speed of transition from preview to normal
    
    def __load_image(self, card_name):
        """Load card image and scale it to the card dimensions."""
        image_path = Config.load_card_image(card_name)
        
        if image_path:
            try:
                original_image = pygame.image.load(image_path)
                self.__image = pygame.transform.scale(
                    original_image, (self.__width, self.__height))
            except pygame.error:
                self.__create_placeholder()
        else:
            self.__create_placeholder()
    
    def __create_placeholder(self):
        """Create a placeholder image if card image can't be loaded."""
        self.__image = pygame.Surface((self.__width, self.__height), pygame.SRCALPHA)
        self.__image.fill(Config.WHITE_COLOR)
        font = pygame.font.SysFont(None, 36)
        text = font.render(self.__card_name, True, Config.BLACK_COLOR)
        text_rect = text.get_rect(center=(self.__width//2, self.__height//2))
        self.__image.blit(text, text_rect)
    
    def __create_shadow(self):
        """Create a shadow surface for the card."""
        shadow_settings = Config.get_shadow_settings()
        offset = shadow_settings['offset']
        opacity = shadow_settings['opacity']
        
        self.__shadow = pygame.Surface(
            (self.__width + offset*2, self.__height + offset*2), 
            pygame.SRCALPHA
        )
        self.__shadow.fill((0, 0, 0, 0))
        pygame.draw.rect(
            self.__shadow, 
            (0, 0, 0, opacity),
            self.__shadow.get_rect(),
            border_radius=self.__border_radius
        )
    
    def __update_position(self):
        """Update the rectangle position to match the card position."""
        self.__rect.center = self.__position
    
    def start_dragging(self, mouse_pos):
        """Start dragging the card from the current position.
        
        Args:
            mouse_pos (tuple): Current mouse position (x, y)
        """
        self.__dragging = True
        self.__drag_offset = (
            self.__position[0] - mouse_pos[0],
            self.__position[1] - mouse_pos[1]
        )
        self.__original_position = self.__position
        self.__current_area = None
    
    def stop_dragging(self):
        """Stop dragging the card."""
        self.__dragging = False
        self.__position = self.__original_position
        self.__update_position()
    
    def update_dragging(self, mouse_pos):
        """Update card position while dragging.
        
        Args:
            mouse_pos (tuple): Current mouse position (x, y)
        """
        if self.__dragging:
            # อัพเดทตำแหน่งการ์ด
            self.__position = (
                mouse_pos[0] + self.__drag_offset[0],
                mouse_pos[1] + self.__drag_offset[1]
            )
            self.__update_position()
            
            # รีเซ็ตสถานะ hovering
            self.__hovering = False
            self.__hovering_area = None
            self.__hovering_over_card = False
    
    def set_hovering(self, is_hovering):
        """Set whether the card is being hovered over.
        
        Args:
            is_hovering (bool): Whether the card is being hovered over
        """
        self.__hovering = is_hovering
        if is_hovering:
            self.__hover_scale = Config.HOVER_SCALE
        else:
            self.__hover_scale = 1.0
    
    def set_preview_mode(self, index, total_cards):
        """Set the card to preview mode with the given index.
        
        Args:
            index (int): Index of the card in the preview array
            total_cards (int): Total number of cards in the preview
        """
        self.__in_preview = True
        self.__preview_index = index
        self.__preview_total_cards = total_cards
    
    def exit_preview_mode(self):
        """Exit preview mode for this card."""
        self.__in_preview = False
        self.__preview_index = -1
    
    def contains_point(self, point):
        """Check if a point is within the card's area.
        
        Args:
            point (tuple): Point to check (x, y)
        
        Returns:
            bool: True if point is within the card's area
        """
        # ตรวจสอบว่าจุดอยู่ในพื้นที่การ์ดหรือไม่
        return self.__rect.collidepoint(point)
    
    def is_in_preview_area(self, point, total_cards):
        """Check if the given point is within the card's area in preview mode.
        
        Args:
            point (tuple): Point to check (x, y)
            total_cards (int): Total number of cards in preview
            
        Returns:
            bool: True if point is within the card's area
        """
        if not self.__in_preview:
            return False
        
        # Calculate position and rotation in preview mode
        preview_data = self.__calculate_preview_position(total_cards)
        pos = preview_data['pos']
        rotation = preview_data['rotation']
        
        # For non-rotated cards, use regular collision detection
        if abs(rotation) < 0.01:  # practically zero
            # Use a slightly larger rectangle for easier selection
            card_rect = pygame.Rect(0, 0, 
                                   self.__width * 1.08,  # 8% larger (reduced from 10%)
                                   self.__height * 1.08)  # 8% larger (reduced from 10%)
            card_rect.center = pos
            return card_rect.collidepoint(point)
        
        # For rotated cards, transform the point to the card's local coordinate system
        # 1. Translate point to origin-centered coordinates
        local_x = point[0] - pos[0]
        local_y = point[1] - pos[1]
        
        # 2. Rotate point in the opposite direction of card rotation
        angle_rad = math.radians(-rotation)
        rotated_x = local_x * math.cos(angle_rad) - local_y * math.sin(angle_rad)
        rotated_y = local_x * math.sin(angle_rad) + local_y * math.cos(angle_rad)
        
        # 3. Check if point is inside the card rectangle (with 8% expansion)
        hit_width = self.__width * 1.08  # 8% larger (reduced from 10%)
        hit_height = self.__height * 1.08  # 8% larger (reduced from 10%)
        
        # Check if point is within rectangle bounds
        return (abs(rotated_x) <= hit_width / 2 and abs(rotated_y) <= hit_height / 2)
    
    def __calculate_preview_position(self, total_cards):
        """Calculate position for a card in preview mode.
        
        Args:
            total_cards (int): Total number of cards in preview
            
        Returns:
            dict: Position data including position, rotation, and scale
        """
        # Get base settings for preview
        window_width, window_height = Config.get_window_dimensions()
        center_x = window_width // 2  # Always center horizontally
        
        # Set display area height - slightly below screen center
        center_y = int(window_height * 0.6)
        
        # Adjust radius for appropriate spacing
        base_radius = int(window_height * 0.45)  # Increased from 0.4 to 0.45
        
        # Single card case - center with no rotation
        if total_cards <= 1:
            return {
                'pos': (center_x, center_y - 50),  # Lift slightly
                'rotation': 0,
                'scale': self.__hover_scale,
                'hover_offset': 0 if self.__hover_scale == 1.0 else -30,
                'lift_angle': 0
            }
        
        # ---- Adjust angle based on card count ----
        # Widened all angles for more spread
        if total_cards <= 3:
            arc_angle = 60  # Increased from 40 to 60
            spacing_factor = 0.85  # Increased from 0.8 to 0.85
        elif total_cards <= 5: 
            arc_angle = 80  # Increased from 60 to 80
            spacing_factor = 0.9  # Increased from 0.85 to 0.9
        elif total_cards <= 7:
            arc_angle = 100  # Increased from 75 to 100
            spacing_factor = 0.95  # Increased from 0.9 to 0.95
        else:
            arc_angle = 120  # Increased from 90 to 120
            spacing_factor = 1.0  # Increased from 0.95 to 1.0
        
        # Adjust radius based on card count - more cards need larger radius
        adjusted_radius = base_radius * spacing_factor
        
        # Center point of the card distribution
        arc_center = (center_x, center_y + adjusted_radius)  # Center point is below the cards
        
        # Calculate angle for each card
        half_angle = arc_angle / 2
        # Calculate by relative index for symmetry
        middle_index = (total_cards - 1) / 2
        relative_index = self.__preview_index - middle_index
        
        # Angle in degrees - 0 is top
        card_angle = 90 - (relative_index * arc_angle / (total_cards - 1))
        
        # Convert to radians for calculation
        rad_angle = math.radians(card_angle)
        
        # Calculate x, y position on the arc - no initial lifting
        x = arc_center[0] + adjusted_radius * math.cos(rad_angle)
        y = arc_center[1] - adjusted_radius * math.sin(rad_angle)
        
        # Calculate card rotation - perpendicular to radius
        rotation_angle = card_angle - 90
        
        # Rest of the code remains the same...
        # (hover effect calculation)
        hover_offset = 0
        lift_angle_value = rotation_angle + 90
        
        current_time = pygame.time.get_ticks() / 1000.0
        hover_animation = 0
        
        if self.__hover_scale > 1.0:  
            animation_speed = 3.0
            animation_amplitude = 7.0
            hover_animation = math.sin(current_time * animation_speed) * animation_amplitude
            
            hover_distance = -40 + hover_animation
            
            lift_angle = math.radians(rotation_angle + 90)
            lift_angle_value = math.degrees(lift_angle)
            
            hover_offset_x = hover_distance * math.cos(lift_angle)
            hover_offset_y = hover_distance * math.sin(lift_angle)
            
            x += hover_offset_x
            y += hover_offset_y
            hover_offset = hover_distance
        
        return {
            'pos': (x, y),
            'rotation': rotation_angle,
            'scale': self.__hover_scale,
            'hover_offset': hover_offset,
            'lift_angle': lift_angle_value,
            'hover_animation': hover_animation
        }
    
    def draw(self, surface, show_hitbox=False):
        """Draw the card on the given surface.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            show_hitbox (bool): Whether to show the hit box (default: False)
        """
        if self.__in_preview:
            self.__draw_preview(surface, show_hitbox)
        elif self.__from_preview and self.__animation_progress < 1.0:
            # Draw transition animation from preview to normal
            self.__draw_transition_from_preview(surface, show_hitbox)
        else:
            # Draw shadow first
            shadow_offset = Config.SHADOW_OFFSET
            shadow_rect = self.__shadow.get_rect(center=(
                self.__position[0] + shadow_offset, 
                self.__position[1] + shadow_offset
            ))
            surface.blit(self.__shadow, shadow_rect)
            
            # Draw card with appropriate scaling if hovering
            if self.__hovering and not self.__dragging:
                scaled_image = pygame.transform.scale(
                    self.__image,
                    (int(self.__width * self.__hover_scale), 
                    int(self.__height * self.__hover_scale))
                )
                scaled_rect = scaled_image.get_rect(center=self.__position)
                surface.blit(scaled_image, scaled_rect)
            else:
                surface.blit(self.__image, self.__rect)
    
    def __draw_preview(self, surface, show_hitbox=False):
        """วาดการ์ดในโหมด preview
        
        Args:
            surface (pygame.Surface): Surface to draw on
            show_hitbox (bool): Whether to show the hit box
        """
        # ใช้ข้อมูลจำนวนการ์ดที่ถูกส่งมาจาก CardDeck โดยตรง
        total_cards = self.__preview_total_cards
        
        # รับตำแหน่งและการหมุนของการ์ดในโหมด preview
        preview_data = self.__calculate_preview_position(total_cards)
        
        # สร้างการ์ดที่หมุนแล้ว
        rotated_card = pygame.transform.rotozoom(
            self.__image, 
            preview_data['rotation'], 
            preview_data['scale']
        )
        rotated_rect = rotated_card.get_rect(center=preview_data['pos'])
        
        # สร้างเงาที่หมุนแล้ว - เงาอยู่ด้านล่างเพื่อให้ขยับตามการยกขึ้น
        rotated_shadow = pygame.transform.rotozoom(
            self.__shadow, 
            preview_data['rotation'], 
            preview_data['scale']
        )
        shadow_offset = Config.SHADOW_OFFSET
        
        # ปรับตำแหน่งเงาเมื่อมีการยกขึ้น (hover)
        if preview_data['hover_offset'] != 0:  # เมื่อมีการ hover เท่านั้น
            # เงาจะยังคงอยู่ในตำแหน่งเดิม แทนที่จะเคลื่อนที่ขึ้นไปกับการ์ด
            lift_angle = math.radians(preview_data['lift_angle'])
            shadow_offset_x = -preview_data['hover_offset'] * math.cos(lift_angle) * 0.3
            shadow_offset_y = -preview_data['hover_offset'] * math.sin(lift_angle) * 0.3
        else:
            # ถ้าไม่มีการ hover ให้เงาอยู่ห่างจากการ์ดเล็กน้อยตามปกติ
            shadow_offset_x = shadow_offset
            shadow_offset_y = shadow_offset
        
        shadow_rect = rotated_shadow.get_rect(center=(
            preview_data['pos'][0] + shadow_offset_x, 
            preview_data['pos'][1] + shadow_offset_y
        ))
        
        # วาดเงาและการ์ด
        surface.blit(rotated_shadow, shadow_rect)
        surface.blit(rotated_card, rotated_rect)
    
        # วาด hitbox เฉพาะเมื่อต้องการแสดงและไม่มีผลต่อตำแหน่งการ์ด
        if show_hitbox:
            # คำนวณขนาด hitbox (ใหญ่กว่าการ์ด 10%)
            hit_width = self.__width * 1.1 * preview_data['scale']
            hit_height = self.__height * 1.1 * preview_data['scale']
            
            # สร้าง hitbox surface แบบโปร่งใส
            hitbox_surface = pygame.Surface((hit_width, hit_height), pygame.SRCALPHA)
            
            # สีแดงโปร่งใส แต่ไม่มีผลต่อการยกตัว
            hitbox_surface.fill((255, 0, 0, 80))
            
            # หมุน hitbox ตามการ์ด
            rotated_hitbox = pygame.transform.rotozoom(
                hitbox_surface, 
                preview_data['rotation'], 
                1.0
            )
            
            # ใช้ตำแหน่งเดียวกับการ์ดโดยไม่ทำให้ตำแหน่งเปลี่ยน
            hitbox_rect = rotated_hitbox.get_rect(center=preview_data['pos'])
            
            # วาด hitbox
            surface.blit(rotated_hitbox, hitbox_rect)
    
    def __draw_transition_from_preview(self, surface, show_hitbox=False):
        """Draw transition animation from preview to normal dragging.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            show_hitbox (bool): Whether to show the hit box
        """
        # Interpolate between preview position and current position
        start_pos = self.__prev_preview_position
        end_pos = self.__position
        
        current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * self.__animation_progress
        current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * self.__animation_progress
        
        # Draw shadow
        shadow_offset = Config.SHADOW_OFFSET
        shadow_rect = self.__shadow.get_rect(center=(
            current_x + shadow_offset, 
            current_y + shadow_offset
        ))
        surface.blit(self.__shadow, shadow_rect)
        
        # Draw card
        card_rect = self.__image.get_rect(center=(current_x, current_y))
        surface.blit(self.__image, card_rect)
    
    def draw_valid_areas(self, surface):
        """Draw valid placement areas on the surface.
        This is now handled by CardDeck.
        """
        pass
    
    @property
    def card_type(self):
        """Get the card's type."""
        return self.__card_type
    
    @property   
    def card_name(self):
        """Get the card's name."""
        return self.__card_name
    
    @property
    def original_position(self):
        """Get the card's original position."""
        return self.__original_position
    
    @property
    def position(self):
        """Get the card's current position."""
        return self.__position
    
    @position.setter
    def position(self, pos):
        """Set the card's position."""
        self.__position = pos
        self.__update_position()
    
    @property
    def current_area(self):
        """Get the card's current area."""
        return self.__current_area
    
    @current_area.setter
    def current_area(self, area):
        """Set the card's current area."""
        self.__current_area = area
    
    @property
    def dragging(self):
        """Get whether the card is being dragged."""
        return self.__dragging
    
    @property
    def hovering(self):
        """Check if the card is being hovered over."""
        return self.__hovering
    
    @property
    def in_preview(self):
        """Check if the card is in preview mode."""
        return self.__in_preview
    
    @property
    def preview_index(self):
        """Get the card's index in preview mode."""
        return self.__preview_index
    
    @property
    def hover_scale(self):
        """Get the card's hover scale."""
        return self.__hover_scale
    
    @hover_scale.setter
    def hover_scale(self, scale):
        """Set the card's hover scale."""
        self.__hover_scale = scale
    
    def update(self):
        """Update card animation states."""
        # Update animation for transition from preview to normal
        if self.__from_preview and self.__animation_progress < 1.0:
            self.__animation_progress = min(1.0, self.__animation_progress + self.__animation_speed)
            if self.__animation_progress >= 1.0:
                self.__from_preview = False
    
    def start_dragging_from_preview(self, mouse_pos, preview_position):
        """Start dragging a card from preview position.
        
        Args:
            mouse_pos (tuple): Current mouse position (x, y)
            preview_position (tuple): Card's position in preview mode
        """
        self.__from_preview = True
        self.__prev_preview_position = preview_position
        self.__animation_progress = 0.0
        
        # Set initial position to where the mouse clicked to avoid jumping
        self.__position = mouse_pos
        
        # Calculate drag offset to keep card centered at mouse position
        self.__drag_offset = (0, 0)
        
        self.__dragging = True
        self.__original_position = self.__position
        self.__current_area = None
    
    @property
    def hovering_area(self):
        """Get the area the card is currently hovering over."""
        return self.__hovering_area
    
    @hovering_area.setter
    def hovering_area(self, value):
        """Set the area the card is currently hovering over."""
        self.__hovering_area = value

    @property
    def hovering_over_card(self):
        """Check if card is hovering over another card."""
        return self.__hovering_over_card

    @hovering_over_card.setter
    def hovering_over_card(self, value):
        """Set whether the card is hovering over another card."""
        self.__hovering_over_card = value

    @property
    def image(self):
        """Get the card's image."""
        return self.__image
    
    @property
    def shadow(self):
        """Get the card's shadow."""
        return self.__shadow
    
    @property
    def width(self):
        """Get the card's width."""
        return self.__width
    
    @property
    def height(self):
        """Get the card's height."""
        return self.__height
    
    @property
    def prev_preview_position(self):
        """Get the card's previous preview position."""
        return self.__prev_preview_position

    @property
    def animation_progress(self):
        """Get the card's animation progress."""
        return self.__animation_progress

    @property
    def rect(self):
        """Get the card's rectangle."""
        return self.__rect


def main():
    """Test function for card module."""
    import pygame
    import sys
    
    # Initialize pygame
    pygame.init()
    
    # Get screen info
    screen_info = pygame.display.Info()
    window_width, window_height = Config.get_window_dimensions()
    
    # Set up the screen
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Card Game Test")
    
    # Create a deck of cards
    deck = CardDeck()
    
    # Create font for mouse position display
    font = pygame.font.SysFont(None, 24)
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Collect all events
        events = pygame.event.get()
        
        # Process events
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # Handle card events
        deck.handle_events(events)
        
        # Update card states
        deck.update()
        
        # Clear the screen
        screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw the deck
        deck.draw(screen)
        
        # Display mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        position_text = f"Mouse: X = {mouse_x}, Y = {mouse_y}"
        text_surface = font.render(position_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(topleft=(10, 10))
        
        # Draw semi-transparent black background
        bg_rect = text_rect.inflate(20, 10)
        bg_rect.topleft = (text_rect.left - 10, text_rect.top - 5)
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
        
        # Draw text
        screen.blit(text_surface, text_rect)
        
        # Update the display
        pygame.display.flip()
        
        # Control the frame rate
        clock.tick(60)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()