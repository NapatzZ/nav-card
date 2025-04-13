import pygame
import math
from typing import List, Tuple
from card import Card
from config import Config


class CardDeck:
    """Class to manage a collection of cards."""
    
    def __init__(self, stage):
        """Initialize the card deck with starting cards."""
        self.__cards = []
        self.__placed_cards = {}
        
        # Store reference to stage
        self.stage = stage
        
        # Preview mode state
        self.__preview_mode = False
        self.__hovered_card_index = -1
        self.__deck_visible = False  # เพิ่มตัวแปรเก็บสถานะการมองเห็นของ deck
        
        # Debug-related variables
        debug_settings = Config.get_debug_settings()
        self.__show_hitbox = False
        self.__show_mouse_position = debug_settings['enabled']
        
        # Animation variables
        self.__hover_animation_time = 0
        
        # Add initial test cards
        self.__add_starting_cards()
        
        # Clear any cards in invalid states
        self.__clear_unused_cards()
    
    def __add_starting_cards(self):
        """Add initial cards to the deck for testing."""
        # กำหนดการ์ดทั้งหมดที่นี่
        cards_to_add = [
            # Navigation cards
            ("Navigation", "A_Star"),
            ("Navigation", "Wall_Following"),
            ("Navigation", "RRT"),
            
            # Collision_avoidance cards
           #  ("Collision_avoidance", "Potential_Field"),
          #   ("Collision_avoidance", "Dynamic_Window"),
          #   ("Collision_avoidance", "Velocity_Obstacle"),
            
            # Recovery cards
         #    ("Recovery", "Backup"),
        #     ("Recovery", "Spin"),
        #     ("Recovery", "Random_Walk")
        ]

        for card_type, card_name in cards_to_add:
            card = Card(card_type, card_name)
            # ไม่ต้องกำหนดตำแหน่งเริ่มต้น เพราะจะแสดงเฉพาะตอน fanout
            card.current_area = "deck"
            self.__cards.append(card)
    
    def handle_events(self, events):
        """Handle game events related to cards.
        
        Args:
            events (list): List of pygame events
        """
        debug_settings = Config.get_debug_settings()
        
        for event in events:
            # Toggle preview mode with spacebar
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.__toggle_preview_mode()
                elif event.key == pygame.K_1 and debug_settings['enabled']:
                    self.__show_hitbox = True
                elif event.key == pygame.K_0 and debug_settings['enabled']:
                    self.__show_hitbox = False
                elif event.key == pygame.K_m and debug_settings['enabled']:
                    self.__show_mouse_position = not self.__show_mouse_position
            
            # Handle mouse events
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.__handle_mouse_down(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.__handle_mouse_up()
            
            elif event.type == pygame.MOUSEMOTION:
                self.__handle_mouse_motion(event.pos)
    
    def __toggle_preview_mode(self):
        """Toggle between preview and normal modes."""
        self.__preview_mode = not self.__preview_mode
        self.__deck_visible = self.__preview_mode
        
        if self.__preview_mode:
            # Get only cards not placed on the table
            available_cards = []
            for card in self.__cards:
                if card.current_area == "deck" or card.current_area is None:
                    available_cards.append(card)
            
            # Check if there are any available cards
            if len(available_cards) == 0:
                self.__preview_mode = False
                self.__deck_visible = False
                return
            
            # Set preview mode for each card
            total_cards = len(available_cards)
            for i, card in enumerate(available_cards):
                card.set_preview_mode(i, total_cards)
        else:
            for card in self.__cards:
                card.exit_preview_mode()
            self.__deck_visible = False
        
        self.__hovered_card_index = -1
    
    def __handle_mouse_down(self, pos):
        """Handle mouse button down event."""
        print(f"\n[Mouse Down] at position: {pos}")
        
        if self.__preview_mode:
            print("[Preview Mode] Checking for card click...")
            deck_cards = [card for card in self.__cards if card.current_area == "deck"]
            
            for i, card in enumerate(deck_cards):
                if card.is_in_preview_area(pos, len(deck_cards)):
                    print(f"[Preview Mode] Card clicked: {card.card_type} - {card.card_name}")
                    preview_data = card._Card__calculate_preview_position(len(deck_cards))
                    preview_pos = preview_data['pos']
                    
                    # เก็บตำแหน่งเริ่มต้นสำหรับอนิเมชั่น
                    card.start_dragging_from_preview(pos, preview_pos)
                    card.update_dragging(pos)
                    
                    # ปิดโหมด preview แต่ยังคงเก็บการลากการ์ดปัจจุบันไว้
                    self.__preview_mode = False
                    self.__deck_visible = False
                    
                    # ออกจาก preview สำหรับการ์ดอื่นๆ ทั้งหมด
                    for other_card in self.__cards:
                        if other_card != card and other_card.in_preview:
                            other_card.exit_preview_mode()
                            
                    break
        else:
            print("[Normal Mode] Checking for card click...")
            for area, card in self.__placed_cards.items():
                if card and card.contains_point(pos):
                    print(f"[Normal Mode] Card clicked: {card.card_type} - {card.card_name} in {area}")
                    card.start_dragging(pos)
                    break
    
    def __handle_mouse_up(self):
        """Handle mouse button up event."""
        print("\n[Mouse Up] Checking for card placement...")
        for card in self.__cards:
            if card.dragging:
                print(f"[Card Placement] Attempting to place card: {card.card_type} - {card.card_name}")
                print(f"[Card Placement] Current position: {card.position}")
                print(f"[Card Placement] Current area: {card.current_area}")
                print(f"[Card Placement] Hovering area: {card.hovering_area}")
                
                # เก็บตำแหน่งปัจจุบันก่อนเรียก stop_dragging
                current_position = card.position
                
                # หยุดการลาก (แต่ไม่ต้องรีเซ็ตตำแหน่ง)
                card.stop_dragging(reset_position=False)
                
                # ตรวจสอบการวางการ์ดที่ตำแหน่งปัจจุบัน
                self.__check_card_placement(card, current_position)
    
    def __handle_mouse_motion(self, pos):
        """Handle mouse motion event.
        
        Args:
            pos (tuple): Mouse position (x, y)
        """
        if self.__preview_mode:
            # Get cards in the deck
            deck_cards = [card for card in self.__cards if card.current_area == "deck"]
            
            # Reset all cards to not hovering first
            for card in deck_cards:
                card.hover_scale = 1.0
            
            # Find which card the mouse is hovering over
            hover_found = False
            hover_index = -1
            
            for i, card in enumerate(deck_cards):
                if card.is_in_preview_area(pos, len(deck_cards)):
                    hover_found = True
                    hover_index = i
                    break
            
            # Set the hovered card index
            self.__hovered_card_index = hover_index
            
            # Set the hovered card's scale
            if hover_index >= 0 and hover_index < len(deck_cards):
                deck_cards[hover_index].hover_scale = Config.PREVIEW_HOVER_SCALE
        else:
            # Update dragging cards
            for card in self.__cards:
                if card.dragging:
                    card.update_dragging(pos)
                    # ส่งการ์ดไปให้ stage ตรวจสอบ
                    self.stage.handle_card_drag(card, pos)
            
            # Update hover state for all cards
            for card in self.__cards:
                if not card.dragging:
                    hovering = card.contains_point(pos)
                    card.set_hovering(hovering)
    
    def __check_card_placement(self, card: Card, current_position):
        """ตรวจสอบการวางการ์ด"""
        print(f"\n[Card Placement Check] Card: {card.card_type} - {card.card_name}")
        print(f"[Card Placement Check] Position: {current_position}")
        print(f"[Card Placement Check] Stage exists: {self.stage is not None}")
        print(f"[Card Placement Check] Hovering area: {card.hovering_area}")
        
        # ถ้าไม่มี stage หรือการ์ดไม่ได้อยู่เหนือช่องใดๆ
        if not self.stage:
            print("[Card Placement Check] No stage found, returning card to deck")
            card.position = card.original_position
            card.current_area = "deck"
            return

        # พยายามวางการ์ด
        if self.stage.place_card(card, current_position):
            print("[Card Placement Check] Card placed successfully")
            # อัปเดต current_area ตาม hovering_area
            if card.hovering_area:
                card.current_area = card.hovering_area
                
                # ลบการ์ดอื่นๆ ที่อาจวางอยู่ในพื้นที่เดียวกัน
                cards_to_remove = []
                for existing_card, area in self.__placed_cards.items():
                    if area == card.hovering_area and existing_card != card:
                        print(f"[Card Placement Check] Removing old card from __placed_cards: {existing_card.card_name}")
                        cards_to_remove.append(existing_card)
                
                # ลบการ์ดที่ต้องลบออกจาก __placed_cards
                for remove_card in cards_to_remove:
                    if remove_card in self.__placed_cards:
                        del self.__placed_cards[remove_card]
                
                # อัปเดตการ์ดที่วางแล้ว
                self.__placed_cards[card] = card.hovering_area
                print(f"[Card Placement Check] Updated __placed_cards with {card.card_name}")
            else:
                print(f"[Card Placement Check] No hovering area found, using slot position")
                # อัปเดตการ์ดที่วางแล้ว
                self.__placed_cards[card] = card.current_area
        else:
            print("[Card Placement Check] Card placement failed, returning to deck")
            # คืนการ์ดกลับไปที่ deck
            card.position = card.original_position
            card.current_area = "deck"
    
    def update(self):
        """Update card states."""
        # Update animation states for all cards
        for card in self.__cards:
            card.update()
            
        # อัปเดตตำแหน่งการ์ดที่กำลังลาก
        mouse_pos = pygame.mouse.get_pos()
        for card in self.__cards:
            if card.dragging:
                card.update_dragging(mouse_pos)
                # ส่งการ์ดไปให้ stage ตรวจสอบ
                self.stage.handle_card_drag(card, mouse_pos)
    
    def draw(self, screen):
        """Draw the deck and all cards."""
        # ตรวจสอบว่ามีการลากการ์ดอยู่หรือไม่
        dragging_any_card = any(card.dragging for card in self.__cards)
        
        # วาดการ์ดที่วางแล้ว
        for card, area in self.__placed_cards.items():
            if card is not None and not card.dragging:
                card.draw(screen)

        # วาดการ์ดใน deck เฉพาะเมื่ออยู่ใน preview mode และไม่มีการลากการ์ดใดๆ
        if self.__preview_mode and not dragging_any_card:
            for card in self.__cards:
                if card is not None and not card.dragging and card.in_preview:
                    card.draw(screen)
                    
        # วาดการ์ดที่กำลังลากอยู่ (แสดงทับการ์ดอื่นๆ)
        for card in self.__cards:
            if card is not None and card.dragging:
                card.draw(screen)

        # แสดงข้อมูล debug ถ้าเปิดใช้งาน
        if self.__show_mouse_position:
            self.__draw_mouse_position(screen)

    def __clear_unused_cards(self):
        """Find and clear any cards that might be in invalid states."""
        # Reset all cards not in play areas to deck
        for card in self.__cards:
            if card.current_area not in ["Navigation", "Collision_avoidance", "Recovery"]:
                card.current_area = "deck"

    @property
    def show_hitbox(self):
        """Get the current hitbox display state."""
        return self.__show_hitbox

    def __draw_mouse_position(self, surface):
        """Display mouse position and debug information on screen.
        
        Args:
            surface (pygame.Surface): Surface to draw on
        """
        # Check if debug mode is enabled
        debug_settings = Config.get_debug_settings()
        if not debug_settings['enabled']:
            return

        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Create font for text display
        font = pygame.font.SysFont(None, debug_settings['font_size'])
        
        # Create information text lines
        lines = []
        lines.append(f"Mouse: X = {mouse_x}, Y = {mouse_y}")
        
        if self.__preview_mode:
            lines.append(f"Mode: Preview (displaying cards)")
            if self.__hovered_card_index >= 0:
                lines.append(f"Hovering card #{self.__hovered_card_index}")
        else:
            lines.append("Mode: Normal (card placement)")
        
        # Add key command instructions
        lines.append("Press SPACE = toggle mode, 1 = show hitbox, 0 = hide hitbox, M = toggle debug info")
        
        # Draw each line
        for i, line in enumerate(lines):
            # Create text surface
            text_surface = font.render(line, True, debug_settings['text_color'])
            text_rect = text_surface.get_rect(
                topleft=(
                    debug_settings['padding'], 
                    debug_settings['padding'] + i * debug_settings['line_height']
                )
            )
            
            # Draw semi-transparent background
            bg_rect = text_rect.inflate(20, 10)
            bg_rect.topleft = (text_rect.left - 10, text_rect.top - 5)
            pygame.draw.rect(surface, debug_settings['bg_color'], bg_rect)
            
            # Draw text
            surface.blit(text_surface, text_rect)

    def __calculate_preview_position(self, card, index, total_cards):
        """Calculate position for a card in preview mode.
        
        Args:
            card (Card): The card to calculate position for
            index (int): Index of the card in the preview array
            total_cards (int): Total number of cards in preview
            
        Returns:
            dict: Position data including position, rotation, and scale
        """
        # Get base settings for preview
        window_width, window_height = Config.get_window_dimensions()
        center_x = window_width // 2
        
        # Set display area height - slightly below screen center
        center_y = int(window_height * 0.6)
        
        # Adjust radius for appropriate spacing
        base_radius = int(window_height * 0.45)
        
        # Single card case - center with no rotation
        if total_cards <= 1:
            return {
                'pos': (center_x, center_y - 50),
                'rotation': 0,
                'scale': card.hover_scale,
                'hover_offset': 0 if card.hover_scale == 1.0 else -30,
                'lift_angle': 0
            }
        
        # Adjust angle based on card count
        if total_cards <= 3:
            arc_angle = 60
            spacing_factor = 0.85
        elif total_cards <= 5: 
            arc_angle = 80
            spacing_factor = 0.9
        elif total_cards <= 7:
            arc_angle = 100
            spacing_factor = 0.95
        else:
            arc_angle = 120
            spacing_factor = 1.0
        
        # Adjust radius based on card count
        adjusted_radius = base_radius * spacing_factor
        
        # Center point of the card distribution
        arc_center = (center_x, center_y + adjusted_radius)
        
        # Calculate angle for each card
        half_angle = arc_angle / 2
        # Calculate by relative index for symmetry
        middle_index = (total_cards - 1) / 2
        relative_index = index - middle_index
        
        # Angle in degrees - 0 is top
        card_angle = 90 - (relative_index * arc_angle / (total_cards - 1))
        
        # Convert to radians for calculation
        rad_angle = math.radians(card_angle)
        
        # Calculate x, y position on the arc
        x = arc_center[0] + adjusted_radius * math.cos(rad_angle)
        y = arc_center[1] - adjusted_radius * math.sin(rad_angle)
        
        # Calculate card rotation - perpendicular to radius
        rotation_angle = card_angle - 90
        
        # Hover effect calculation
        hover_offset = 0
        lift_angle_value = rotation_angle + 90
        
        current_time = pygame.time.get_ticks() / 1000.0
        hover_animation = 0
        
        if card.hover_scale > 1.0:  
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
            'scale': card.hover_scale,
            'hover_offset': hover_offset,
            'lift_angle': lift_angle_value,
            'hover_animation': hover_animation
        }

    def __draw_preview(self, surface, card, show_hitbox=False):
        """Draw card in preview mode.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            card (Card): The card to draw
            show_hitbox (bool): Whether to show the hit box
        """
        # Get position and rotation of the card in preview mode
        preview_data = self.__calculate_preview_position(card, card.preview_index, len(self.__cards))
        
        # Create rotated card
        rotated_card = pygame.transform.rotozoom(
            card.image, 
            preview_data['rotation'], 
            preview_data['scale']
        )
        rotated_rect = rotated_card.get_rect(center=preview_data['pos'])
        
        # Create rotated shadow
        rotated_shadow = pygame.transform.rotozoom(
            card.shadow, 
            preview_data['rotation'], 
            preview_data['scale']
        )
        shadow_offset = Config.SHADOW_OFFSET
        
        # Adjust shadow position when hovering
        if preview_data['hover_offset'] != 0:
            lift_angle = math.radians(preview_data['lift_angle'])
            shadow_offset_x = -preview_data['hover_offset'] * math.cos(lift_angle) * 0.3
            shadow_offset_y = -preview_data['hover_offset'] * math.sin(lift_angle) * 0.3
        else:
            shadow_offset_x = shadow_offset
            shadow_offset_y = shadow_offset
        
        shadow_rect = rotated_shadow.get_rect(center=(
            preview_data['pos'][0] + shadow_offset_x, 
            preview_data['pos'][1] + shadow_offset_y
        ))
        
        # Draw shadow and card
        surface.blit(rotated_shadow, shadow_rect)
        surface.blit(rotated_card, rotated_rect)
    
        # Draw hitbox if requested
        if show_hitbox:
            # Calculate hitbox size (10% larger than card)
            hit_width = card.width * 1.1 * preview_data['scale']
            hit_height = card.height * 1.1 * preview_data['scale']
            
            # Create transparent hitbox surface
            hitbox_surface = pygame.Surface((hit_width, hit_height), pygame.SRCALPHA)
            hitbox_surface.fill((255, 0, 0, 80))
            
            # Rotate hitbox with card
            rotated_hitbox = pygame.transform.rotozoom(
                hitbox_surface, 
                preview_data['rotation'], 
                1.0
            )
            
            # Use same position as card
            hitbox_rect = rotated_hitbox.get_rect(center=preview_data['pos'])
            
            # Draw hitbox
            surface.blit(rotated_hitbox, hitbox_rect)

    def __draw_transition_from_preview(self, surface, card, show_hitbox=False):
        """Draw transition animation from preview to normal dragging.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            card (Card): The card to draw
            show_hitbox (bool): Whether to show the hit box
        """
        # Interpolate between preview position and current position
        start_pos = card.prev_preview_position
        end_pos = card.position
        
        current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * card.animation_progress
        current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * card.animation_progress
        
        # Draw shadow
        shadow_offset = Config.SHADOW_OFFSET
        shadow_rect = card.shadow.get_rect(center=(
            current_x + shadow_offset, 
            current_y + shadow_offset
        ))
        surface.blit(card.shadow, shadow_rect)
        
        # Draw card
        card_rect = card.image.get_rect(center=(current_x, current_y))
        surface.blit(card.image, card_rect)

    def is_in_preview_area(self, card, point, total_cards):
        """Check if the given point is within the card's area in preview mode.
        
        Args:
            card (Card): The card to check
            point (tuple): Point to check (x, y)
            total_cards (int): Total number of cards in preview
            
        Returns:
            bool: True if point is within the card's area
        """
        if not card.in_preview:
            return False
        
        # Calculate position and rotation in preview mode
        preview_data = self.__calculate_preview_position(card, card.preview_index, total_cards)
        pos = preview_data['pos']
        rotation = preview_data['rotation']
        
        # For non-rotated cards, use regular collision detection
        if abs(rotation) < 0.01:
            card_rect = pygame.Rect(0, 0, 
                                   card.width * 1.08,
                                   card.height * 1.08)
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
        hit_width = card.width * 1.08
        hit_height = card.height * 1.08
        
        # Check if point is within rectangle bounds
        return (abs(rotated_x) <= hit_width / 2 and abs(rotated_y) <= hit_height / 2)

    @property
    def cards(self):
        """Get all cards in the deck."""
        return self.__cards