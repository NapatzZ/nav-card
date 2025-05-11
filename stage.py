"""
Stage module for managing card slots, buttons, and game board.
"""
import pygame
from typing import List, Tuple, Optional
from card import Card, CardType
from config import Config
import os

class Button:
    """
    Class representing a clickable button in the game.
    
    Attributes:
        position (Tuple[int, int]): Position of the button
        action_name (str): Name of the action when clicked
        image (pygame.Surface): Button image
        rect (pygame.Rect): Rectangle for click detection
        is_hovered (bool): Whether mouse is hovering over button
        is_visible (bool): Whether button is visible
        is_level_button (bool): Whether this is a level button
    """
    
    def __init__(self, position: Tuple[int, int], image_path: str, action_name: str):
        """
        Initialize a button with an image.
        
        Args:
            position (Tuple[int, int]): Position of the button
            image_path (str): Path to the image file or None for text-only button
            action_name (str): Name of the action when clicked
        """
        self.position = position
        self.action_name = action_name
        self.is_level_button = False  # By default, buttons move with camera
        
        if image_path:
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (250, 150))
            except pygame.error:
                self._create_text_button()
        else:
            # สร้างปุ่มที่เป็นข้อความ
            self._create_text_button()
        
        self.rect = self.image.get_rect(center=position)
        self.is_hovered = False
        self.is_visible = True
    
    def _create_text_button(self):
        """สร้างปุ่มโดยใช้ข้อความแทนรูปภาพ"""
        button_width = 250
        button_height = 150
        
        self.image = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        self.image.fill((100, 100, 100, 200))  # พื้นหลังสีเทาโปร่งใส
        
        # วาดขอบสี่เหลี่ยม
        pygame.draw.rect(self.image, (200, 200, 200), 
                        (0, 0, button_width, button_height), 3, border_radius=10)
        
        # แสดงข้อความตรงกลาง
        display_text = self.action_name.upper()
        
        # เลือกขนาดฟอนต์ตามความยาวของข้อความ
        font_size = 48 if len(display_text) < 10 else 36
        
        try:
            font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", font_size)
        except:
            font = pygame.font.Font(None, font_size)  # ใช้ฟอนต์เริ่มต้นถ้าไม่พบฟอนต์ที่กำหนด
            
        text = font.render(display_text, True, (255, 255, 255))
        text_rect = text.get_rect(center=(button_width // 2, button_height // 2))
        self.image.blit(text, text_rect)
    
    def set_visible(self, visible: bool):
        """
        Set the visibility of the button.
        
        Args:
            visible (bool): Whether the button should be visible
        """
        self.is_visible = visible
        
    def draw(self, screen: pygame.Surface, camera_offset=(0, 0)):
        """
        Draw the button on the screen.
        
        Args:
            screen (pygame.Surface): Surface to draw on
            camera_offset (Tuple[int, int]): Offset for camera position (x, y)
        """
        if not self.is_visible:
            return
            
        if self.is_hovered:
            scaled_image = pygame.transform.scale(self.image, 
                                                 (int(self.rect.width * 1.25), 
                                                  int(self.rect.height * 1.25)))
            scaled_rect = scaled_image.get_rect(center=self.rect.center)
            screen.blit(scaled_image, scaled_rect)
        else:
            screen.blit(self.image, self.rect)
    
    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if mouse is over the button.
        
        Args:
            mouse_pos (Tuple[int, int]): Current mouse position
            
        Returns:
            bool: True if mouse is over the button
        """
        if not self.is_visible:
            self.is_hovered = False
            return False
            
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
    
    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if button is clicked.
        
        Args:
            mouse_pos (Tuple[int, int]): Current mouse position
            
        Returns:
            bool: True if button is clicked
        """
        if not self.is_visible:
            return False
            
        return self.rect.collidepoint(mouse_pos)

class CardSlot:
    """
    Class representing a slot where cards can be placed.
    
    Attributes:
        position (tuple): Position of the slot (x, y)
        card_type (CardType): Type of card that can be placed in this slot
        card (Optional[Card]): Card currently in the slot
        is_highlighted (bool): Whether the slot is highlighted
        highlight_color (tuple): Color for highlighting
        slot_surface (pygame.Surface): Surface for the slot
        valid_area_rect (pygame.Rect): Rectangle for valid card placement area
        rect (pygame.Rect): Rectangle for the slot
    """
    
    def __init__(self, position: tuple[int, int], card_type: CardType):
        """
        Initialize a card slot.
        
        Args:
            position (tuple): Position of the slot (x, y)
            card_type (CardType): Type of card that can be placed in this slot
        """
        self.position = position
        self.card_type = card_type
        self.card = None
        self.is_highlighted = False
        self.highlight_color = (255, 255, 255)
        
        self.slot_surface = self._create_slot_surface()
        self.valid_area_rect = self._create_valid_area_rect()
        self.rect = pygame.Rect(
            position[0],
            position[1],
            Config.CARD_SLOT_WIDTH,
            Config.CARD_SLOT_HEIGHT
        )

    def _create_valid_area_rect(self) -> pygame.Rect:
        """
        Create valid area rect for the card.
        
        Returns:
            pygame.Rect: Rectangle representing the valid area
        """
        return pygame.Rect(
            self.position[0],
            self.position[1],
            Config.CARD_SLOT_WIDTH,
            Config.CARD_SLOT_HEIGHT
        )

    def _create_slot_surface(self) -> pygame.Surface:
        """
        Create surface for card slot.
        
        Returns:
            pygame.Surface: Surface for the card slot
        """
        surface = pygame.Surface((Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), pygame.SRCALPHA)
        
        pygame.draw.rect(surface, Config.CARD_SLOT_COLOR, (0, 0, Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), border_radius=10)
        
        font = pygame.font.SysFont("Arial", 24)
        text = font.render(self.card_type.value, True, (255, 255, 255))
        text_rect = text.get_rect(centerx=Config.CARD_SLOT_WIDTH//2, y=10)
        surface.blit(text, text_rect)
        
        return surface

    def draw(self, screen: pygame.Surface, dragging_card: Optional[Card] = None):
        """
        Draw card slot and valid area.
        
        Args:
            screen (pygame.Surface): Surface to draw on
            dragging_card (Optional[Card]): Card being dragged
        """
        screen.blit(self.slot_surface, self.position)
        
        border_color = self.highlight_color if self.is_highlighted else (255, 255, 255)
        pygame.draw.rect(screen, border_color,
                        (*self.position, Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT),
                        2, border_radius=10)
        
        if dragging_card:
            valid_surface = pygame.Surface((Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), pygame.SRCALPHA)
            
            can_place = self.can_accept_card(dragging_card)
            
            if self.card is not None:
                if dragging_card.hovering_area == self.card_type.value and dragging_card.hovering_over_card:
                    valid_surface.fill((100, 100, 100, Config.VALID_AREA_ALPHA))
                else:
                    valid_surface.fill((0, 0, 0, 0))
            elif dragging_card.hovering_area == self.card_type.value:
                if can_place:
                    valid_surface.fill((120, 120, 120, Config.VALID_AREA_ALPHA))
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))
            elif self.card_type.value == dragging_card.card_type:
                if can_place:
                    valid_surface.fill((150, 150, 150, Config.VALID_AREA_ALPHA))
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))
            else:
                if can_place:
                    valid_surface.fill((80, 130, 100, Config.VALID_AREA_ALPHA))
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))
            
            screen.blit(valid_surface, self.position)
            
            font = pygame.font.SysFont(None, 32)
            label_text = self.card_type.value
            label_surface = font.render(label_text, True, Config.WHITE_COLOR)
            label_rect = label_surface.get_rect(
                centerx=self.position[0] + Config.CARD_SLOT_WIDTH // 2,
                bottom=self.position[1] - 10
            )
            screen.blit(label_surface, label_rect)
            
            type_surface = font.render(self.card_type.value, True, Config.WHITE_COLOR)
            type_rect = type_surface.get_rect(
                centerx=self.position[0] + Config.CARD_SLOT_WIDTH // 2,
                top=self.position[1] + Config.CARD_SLOT_HEIGHT + 10
            )
            screen.blit(type_surface, type_rect)
        
        if self.card and not self.card.dragging:
            card_center_x = self.position[0] + Config.CARD_SLOT_WIDTH // 2
            card_center_y = self.position[1] + Config.CARD_SLOT_HEIGHT // 2
            
            original_pos = self.card.position
            self.card.position = (card_center_x, card_center_y)
            self.card.draw(screen)
            self.card.position = original_pos

    def can_accept_card(self, card: Card) -> bool:
        """Check if a card can be placed in this slot.
        
        Args:
            card (Card): Card to be placed
            
        Returns:
            bool: True if card can be placed, False otherwise
        """
        print(f"[CardSlot] Checking if can accept card: {card.card_type} - {card.card_name}")
        print(f"[CardSlot] Slot type: {self.card_type.value}")
        return card.card_type == self.card_type.value

    def place_card(self, card: Card) -> bool:
        """Place a card in this slot.
        
        Args:
            card (Card): Card to be placed
            
        Returns:
            bool: True if card was placed successfully, False otherwise
        """
        if not self.can_accept_card(card):
            print(f"[CardSlot] Cannot place card: {card.card_type} - {card.card_name} in slot: {self.card_type.value}")
            return False
            
        # If there's an existing card, return the old card to the deck
        removed_card = None
        if self.card is not None:
            print(f"[CardSlot] Returning old card: {self.card.card_name} to deck")
            removed_card = self.card
            removed_card.current_area = "deck"
            removed_card.position = removed_card.original_position
            removed_card.rect.center = removed_card.original_position
            self.card = None  # Remove old card from slot before returning
            
        # Place new card
        print(f"[CardSlot] Placing new card: {card.card_name} in slot: {self.card_type.value}")
        self.card = card
        
        # Set card position to center of slot
        card_center_x = self.position[0] + Config.CARD_SLOT_WIDTH // 2
        card_center_y = self.position[1] + Config.CARD_SLOT_HEIGHT // 2
        
        # Update position and other attributes
        card.rect.center = (card_center_x, card_center_y)
        card.position = (card_center_x, card_center_y)
        card.current_area = self.card_type.value
        
        return True

    def remove_card(self) -> Optional[Card]:
        if self.card:
            removed_card = self.card
            self.card = None
            return removed_card
        return None

class Stage:
    def __init__(self):
        self.slots: List[CardSlot] = []
        self._initialize_slots()
        self.background = self._create_background()
        
        # Add Reset and Start buttons
        self.buttons = self._initialize_buttons()

    def _create_background(self) -> pygame.Surface:
        """Create the game board background."""
        surface = pygame.Surface((Config.BOARD_WIDTH, Config.BOARD_HEIGHT))
        surface.fill(Config.BOARD_COLOR)
        
        # Draw grid background
        for y in range(0, Config.BOARD_HEIGHT, 50):
            for x in range(0, Config.BOARD_WIDTH, 50):
                pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        
        return surface
    
    def _initialize_buttons(self) -> List[Button]:
        """
        Initialize buttons for the stage.
        
        Returns:
            List[Button]: List of button objects
        """
        # Dimensions
        window_width, window_height = Config.get_window_dimensions()
        
        # แบ่งหน้าจอเป็น 3 ส่วนสำหรับปุ่มหลัก
        reset_button_x = int(window_width * (1/6))  # ด้านซ้าย
        start_button_x = int(window_width * (3/6))  # ตรงกลาง
        stats_button_x = int(window_width * (5/6))  # ด้านขวา
        
        # กำหนดตำแหน่ง Y สำหรับปุ่มทั้งหมด (ปรับให้ต่ำลงอีก)
        buttons_y = window_height + 100  # ปรับจาก 60 เป็น 40 เพื่อให้ปุ่มอยู่ชิดด้านล่างมากขึ้น
        
        # Create list of buttons
        buttons = []
        
        # Add reset button (ซ้าย)
        try:
            reset_button = Button(
                (reset_button_x, buttons_y),
                os.path.join("assets", "reset_button.png"),
                "reset"
            )
            buttons.append(reset_button)
        except Exception as e:
            print(f"Error loading reset button: {e}")
            # สร้างปุ่มข้อความถ้าไม่พบรูปภาพ
            reset_button = Button(
                (reset_button_x, buttons_y),
                None,
                "reset"
            )
            buttons.append(reset_button)
        
        # Add start button (กลาง)
        try:
            start_button = Button(
                (start_button_x, buttons_y),
                os.path.join("assets", "start_button.png"),
                "start"
            )
            buttons.append(start_button)
        except Exception as e:
            print(f"Error loading start button: {e}")
            # สร้างปุ่มข้อความถ้าไม่พบรูปภาพ
            start_button = Button(
                (start_button_x, buttons_y),
                None,
                "start"
            )
            buttons.append(start_button)
        
        # Add stats button (ขวา)
        try:
            stats_button = Button(
                (stats_button_x, buttons_y),
                None,  # ไม่มีไฟล์รูปภาพ ใช้ข้อความแทน
                "stats"
            )
            buttons.append(stats_button)
        except Exception as e:
            print(f"Error creating stats button: {e}")
        
        return buttons

    def _initialize_slots(self):
        """Initialize card slots with their positions and types."""
        # Calculate initial position of the first slot
        start_x = (Config.BOARD_WIDTH - (3 * Config.CARD_SLOT_WIDTH + 2 * Config.CARD_SLOT_SPACING)) // 2
        start_y = (Config.BOARD_HEIGHT - Config.CARD_SLOT_HEIGHT) // 2

        # Create slots for each card type
        slot_types = [CardType.NAVIGATION, CardType.COLLISION_AVOIDANCE, CardType.RECOVERY_BEHAVIOR]
        for i, card_type in enumerate(slot_types):
            x = start_x + i * (Config.CARD_SLOT_WIDTH + Config.CARD_SLOT_SPACING)
            self.slots.append(CardSlot((x, start_y), card_type))

    def draw(self, screen: pygame.Surface, dragging_card: Optional[Card] = None, camera_offset: Tuple[int, int] = (0, 0)):
        """Draw the stage and all its elements to the screen.
        
        Args:
            screen (pygame.Surface): The surface to draw on
            dragging_card (Optional[Card]): Card being dragged, if any
            camera_offset (Tuple[int, int]): Offset for camera position (x, y)
        """
        # Draw game board background
        # Calculate background position using camera_offset
        screen.blit(self.background, camera_offset)
        
        # Draw card slots (excluding cards)
        for slot in self.slots:
            # Create temporary slot with adjusted position and state
            adjusted_slot = CardSlot(
                (slot.position[0] + camera_offset[0], slot.position[1] + camera_offset[1]),
                slot.card_type
            )
            adjusted_slot.is_highlighted = slot.is_highlighted
            
            # Important: Do not set card for adjusted_slot
            # To prevent drawing overlapping cards (since CardDeck will draw cards)
            adjusted_slot.card = None
            
            # Draw only the slot without cards
            adjusted_slot.draw(screen, dragging_card)

    def handle_card_drag(self, card: Card, mouse_pos: tuple[int, int], camera_offset: Tuple[int, int] = (0, 0)):
        """Handle card dragging over the stage.
        
        Args:
            card (Card): Card being dragged
            mouse_pos (tuple[int, int]): Current mouse position
            camera_offset (Tuple[int, int]): Camera offset (x, y)
        """
        # Adjust mouse position considering camera offset
        adjusted_mouse_pos = (mouse_pos[0] - camera_offset[0], mouse_pos[1] - camera_offset[1])
        
        # Reset all hovering states
        hovering_any_slot = False
        hovering_over_card = False
        
        # Check for card overlapping existing card
        for slot in self.slots:
            if slot.card and slot.card != card:
                # If there's a card and it's not the card being dragged
                card_rect = pygame.Rect(slot.card.position[0] - 50, slot.card.position[1] - 75, 100, 150)
                if card_rect.collidepoint(adjusted_mouse_pos):
                    # Mouse is over existing card
                    hovering_over_card = True
                    card.hovering_area = slot.card_type.value
                    hovering_any_slot = True
                    break
        
        # If not over any card, check for card placement slot
        if not hovering_over_card:
            for slot in self.slots:
                # Create Rect for card placement slot
                slot_rect = pygame.Rect(
                    slot.position[0], slot.position[1], 
                    Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT
                )
                
                if slot_rect.collidepoint(adjusted_mouse_pos):
                    # Mouse is over card placement slot
                    card.hovering_area = slot.card_type.value
                    hovering_any_slot = True
                    break
        
        # Update hovering state of the card
        card.hovering_over_card = hovering_over_card
        
        # If not over any slot, reset hovering_area
        if not hovering_any_slot:
            card.hovering_area = None

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion events.
        
        Args:
            mouse_pos (Tuple[int, int]): Mouse position (x, y)
        """
        # Buttons don't move with camera_offset, so no need to adjust mouse position for hover check
        for button in self.buttons:
            button.check_hover(mouse_pos)
    
    def handle_button_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Handle button click events.
        
        Args:
            mouse_pos (Tuple[int, int]): Mouse position when clicked (x, y)
            
        Returns:
            Optional[str]: Action name if a button was clicked, None otherwise
        """
        # ตรวจสอบการคลิกปุ่ม
        for button in self.buttons:
            if button.is_visible:
                # ตรวจสอบว่าการคลิกอยู่ในปุ่มหรือไม่
                if button.rect.collidepoint(mouse_pos):
                    # ใช้ Config.log แทน print และแสดงตำแหน่งเมาส์
                    Config.log("Stage", f"Button clicked: {button.action_name}", level=1, show_pos=True, mouse_pos=mouse_pos)
                    
                    # ถ้าเป็นปุ่ม stats ไม่ต้องส่งคืนค่า
                    if button.action_name == "stats":
                        # แสดงข้อความว่าฟีเจอร์นี้ยังไม่พร้อมใช้งาน
                        return "show_message"
                    
                    return button.action_name
        
        return None
    
    def place_card(self, card: Card, position: tuple[int, int], camera_offset: Tuple[int, int] = (0, 0)) -> bool:
        """Place a card on a slot.
        
        Args:
            card (Card): Card to place
            position (tuple[int, int]): Position to place the card (x, y)
            camera_offset (Tuple[int, int]): Camera offset (x, y)
        
        Returns:
            bool: True if card was placed successfully, False otherwise
        """
        # Adjust position considering camera offset
        adjusted_position = (position[0] - camera_offset[0], position[1] - camera_offset[1])
        
        # แสดงข้อมูลการพยายามวาง card พร้อมตำแหน่ง
        Config.log("Stage", f"Placing card: {card.card_name} ({card.card_type})", level=2, show_pos=True, mouse_pos=position)
        
        # Find slot at the adjusted position
        for slot in self.slots:
            # Check if slot contains this position
            slot_rect = pygame.Rect(
                slot.position[0], slot.position[1],
                Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT
            )
            
            if slot_rect.collidepoint(adjusted_position):
                Config.log("Stage", f"Found slot for card type: {slot.card_type.value}", level=2)
                result = slot.place_card(card)
                
                if result:
                    # Set card position to slot position with offset for centering
                    card.position = (
                        slot.position[0] + Config.CARD_SLOT_WIDTH // 2,
                        slot.position[1] + Config.CARD_SLOT_HEIGHT // 2
                    )
                    card.current_area = slot.card_type.value
                    
                    # Update slot rect
                    card.rect.center = card.position
                    Config.log("Stage", f"Card successfully placed", level=1)
                
                return result
                
        Config.log("Stage", "No valid slot found at position", level=2, show_pos=True, mouse_pos=position)
        return False

    def get_slot_at_position(self, pos: Tuple[int, int]) -> Optional[CardSlot]:
        for slot in self.slots:
            if slot.valid_area_rect.collidepoint(pos):
                return slot
        return None

    def get_selected_algorithm(self):
        """
        Get the algorithm selected by the player
        
        Returns:
            Tuple[str, str]: (algorithm name, algorithm type) or ("", "") if none selected
        """
        # Check Navigation slot card first
        for slot in self.slots:
            if slot.card and slot.card_type == CardType.NAVIGATION:
                return (slot.card.card_name, slot.card.card_type)
                
        # If no Navigation card found but other cards exist, use other card
        for slot in self.slots:
            if slot.card:
                return (slot.card.card_name, slot.card.card_type)
                
        # No cards at all
        return ("", "")
    
    def run_algorithm(self, costmap, statistics):
        """
        Run algorithm based on selected cards
        
        Args:
            costmap: Costmap data for robot movement
            statistics: Object for recording statistics
            
        Returns:
            bool: True if algorithm started successfully, False if not
        """
        # Check if robot and goal positions are set
        if not costmap.robot_pos or not costmap.goal_pos:
            Config.log("Stage", "Cannot start algorithm: Robot and goal positions must be set first", level=1)
            return False
            
        # Get cards in all slots
        algorithm_cards = []
        for slot in self.slots:
            if slot.card:
                algorithm_cards.append(slot.card)
                
        if not algorithm_cards:
            Config.log("Stage", "Cannot start algorithm: Algorithm cards must be selected first", level=1)
            return False
            
        # Use first card for testing
        selected_card = algorithm_cards[0]
        # แสดงข้อมูลอัลกอริทึมที่เลือกใช้ (ควรแสดงเสมอ - level 1)
        Config.log("Stage", f"Selected algorithm: {selected_card.card_name} ({selected_card.card_type})", level=1)
        
        # Import algorithm modules
        from algorithms.navigation import NAVIGATION_ALGORITHMS
        from algorithms.collision_avoidance import COLLISION_AVOIDANCE_ALGORITHMS
        from algorithms.recovery import RECOVERY_ALGORITHMS
        
        # Find algorithm class based on card type and name
        algorithm_class = None
        if selected_card.card_type == "Navigation":
            algorithm_class = NAVIGATION_ALGORITHMS.get(selected_card.card_name)
        elif selected_card.card_type == "Collision avoidance":
            algorithm_class = COLLISION_AVOIDANCE_ALGORITHMS.get(selected_card.card_name)
        elif selected_card.card_type == "Recovery":
            algorithm_class = RECOVERY_ALGORITHMS.get(selected_card.card_name)
            
        if not algorithm_class:
            Config.log("Stage", f"Algorithm not found for card: {selected_card.card_name}", level=1)
            return False
            
        # Let GameManager create and manage algorithm instance
        # We just return the necessary data
        return algorithm_class, costmap


