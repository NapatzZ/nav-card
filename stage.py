import pygame
from typing import List, Tuple, Optional
from card import Card, CardType
from config import Config

class CardSlot:
    def __init__(self, position: tuple[int, int], card_type: CardType):
        """Initialize a card slot.
        
        Args:
            position (tuple): Position of the slot (x, y)
            card_type (CardType): Type of card that can be placed in this slot
        """
        self.position = position
        self.card_type = card_type
        self.card = None
        self.is_highlighted = False
        self.highlight_color = (255, 255, 255)
        
        # สร้างพื้นผิวสำหรับช่องการ์ด
        self.slot_surface = self._create_slot_surface()
        
        # สร้าง valid area rect
        self.valid_area_rect = self._create_valid_area_rect()
        
        # สร้าง rect สำหรับช่องการ์ด
        self.rect = pygame.Rect(
            position[0],
            position[1],
            Config.CARD_SLOT_WIDTH,
            Config.CARD_SLOT_HEIGHT
        )

    def _create_valid_area_rect(self) -> pygame.Rect:
        """สร้างพื้นที่ valid area สำหรับการ์ด"""
        return pygame.Rect(
            self.position[0],
            self.position[1],
            Config.CARD_SLOT_WIDTH,
            Config.CARD_SLOT_HEIGHT
        )

    def _create_slot_surface(self) -> pygame.Surface:
        """สร้างพื้นผิวสำหรับช่องการ์ด"""
        surface = pygame.Surface((Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), pygame.SRCALPHA)
        
        # วาดพื้นหลังช่อง
        pygame.draw.rect(surface, Config.CARD_SLOT_COLOR, (0, 0, Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), border_radius=10)
        
        # วาดชื่อประเภทการ์ด
        font = pygame.font.Font(None, 24)
        text = font.render(self.card_type.value, True, (255, 255, 255))
        text_rect = text.get_rect(centerx=Config.CARD_SLOT_WIDTH//2, y=10)
        surface.blit(text, text_rect)
        
        return surface

    def draw(self, screen: pygame.Surface, dragging_card: Optional[Card] = None):
        """วาดช่องการ์ดและ valid area
        
        Args:
            screen (pygame.Surface): พื้นผิวที่จะวาด
            dragging_card (Optional[Card]): การ์ดที่กำลังลาก
        """
        # วาดพื้นหลังของช่อง
        screen.blit(self.slot_surface, self.position)
        
        # วาดเส้นขอบ
        border_color = self.highlight_color if self.is_highlighted else (255, 255, 255)
        pygame.draw.rect(screen, border_color,
                        (*self.position, Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT),
                        2, border_radius=10)
        
        # วาดพื้นที่ valid area ถ้ามีการ์ดที่กำลังลาก
        if dragging_card:
            # สร้างพื้นผิวสำหรับ valid area
            valid_surface = pygame.Surface((Config.CARD_SLOT_WIDTH, Config.CARD_SLOT_HEIGHT), pygame.SRCALPHA)
            
            # ตรวจสอบว่าสามารถวางการ์ดได้หรือไม่
            can_place = self.can_accept_card(dragging_card)
            
            # กำหนดสีพื้นหลังตามเงื่อนไข
            if self.card is not None:
                if dragging_card.hovering_area == self.card_type.value and dragging_card.hovering_over_card:
                    valid_surface.fill((100, 100, 100, Config.VALID_AREA_ALPHA))  # สีเทาเข้มเมื่อจะแทนที่การ์ด
                else:
                    valid_surface.fill((0, 0, 0, 0))  # โปร่งใส
            elif dragging_card.hovering_area == self.card_type.value:
                if can_place:
                    valid_surface.fill((120, 120, 120, Config.VALID_AREA_ALPHA))  # สีเทาเมื่อสามารถวางได้
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))  # สีแดงเมื่อวางไม่ได้
            elif self.card_type.value == dragging_card.card_type:
                if can_place:
                    valid_surface.fill((150, 150, 150, Config.VALID_AREA_ALPHA))  # สีเทาอ่อนเมื่อสามารถวางได้
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))  # สีแดงเมื่อวางไม่ได้
            else:
                if can_place:
                    valid_surface.fill((80, 130, 100, Config.VALID_AREA_ALPHA))  # สีเขียวอ่อนเมื่อสามารถวางได้
                else:
                    valid_surface.fill((200, 100, 100, Config.VALID_AREA_ALPHA))  # สีแดงเมื่อวางไม่ได้
            
            # วาด valid area ลงบนหน้าจอ
            screen.blit(valid_surface, self.position)
            
            # วาดข้อความประเภทการ์ดด้านบน
            font = pygame.font.SysFont(None, 32)
            label_text = self.card_type.value
            label_surface = font.render(label_text, True, Config.WHITE_COLOR)
            label_rect = label_surface.get_rect(
                centerx=self.position[0] + Config.CARD_SLOT_WIDTH // 2,
                bottom=self.position[1] - 10
            )
            screen.blit(label_surface, label_rect)
            
            # วาดข้อความประเภทการ์ดด้านล่าง
            type_surface = font.render(self.card_type.value, True, Config.WHITE_COLOR)
            type_rect = type_surface.get_rect(
                centerx=self.position[0] + Config.CARD_SLOT_WIDTH // 2,
                top=self.position[1] + Config.CARD_SLOT_HEIGHT + 10
            )
            screen.blit(type_surface, type_rect)
        
        # วาดการ์ดถ้ามี
        if self.card:
            self.card.draw(screen)

    def can_accept_card(self, card: Card) -> bool:
        """ตรวจสอบว่าสามารถวางการ์ดในช่องนี้ได้หรือไม่"""
        print(f"[CardSlot] Checking if can accept card: {card.card_type} - {card.card_name}")
        print(f"[CardSlot] Slot type: {self.card_type.value}")
        return card.card_type == self.card_type.value

    def place_card(self, card: Card) -> bool:
        """Place a card in this slot."""
        if not self.can_accept_card(card):
            print(f"[CardSlot] Cannot place card: {card.card_type} - {card.card_name} in slot: {self.card_type.value}")
            return False
            
        # ถ้ามีการ์ดอยู่แล้ว ให้คืนการ์ดเก่ากลับไปที่ deck
        removed_card = None
        if self.card is not None:
            print(f"[CardSlot] Returning old card: {self.card.card_name} to deck")
            removed_card = self.card
            removed_card.current_area = "deck"
            removed_card.position = removed_card.original_position
            self.card = None  # ลบการ์ดเก่าออกจากช่องก่อน
            
        # วางการ์ดใหม่
        print(f"[CardSlot] Placing new card: {card.card_name} in slot: {self.card_type.value}")
        self.card = card
        card.rect.center = self.rect.center
        card.position = self.rect.center
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

    def _create_background(self) -> pygame.Surface:
        """Create the game board background."""
        surface = pygame.Surface((Config.BOARD_WIDTH, Config.BOARD_HEIGHT))
        surface.fill(Config.BOARD_COLOR)
        
        # วาดลวดลายพื้นหลัง
        for y in range(0, Config.BOARD_HEIGHT, 50):
            for x in range(0, Config.BOARD_WIDTH, 50):
                pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        
        return surface

    def _initialize_slots(self):
        """Initialize card slots with their positions and types."""
        # คำนวณตำแหน่งเริ่มต้นของช่องแรก
        start_x = (Config.BOARD_WIDTH - (3 * Config.CARD_SLOT_WIDTH + 2 * Config.CARD_SLOT_SPACING)) // 2
        start_y = (Config.BOARD_HEIGHT - Config.CARD_SLOT_HEIGHT) // 2

        # สร้างช่องสำหรับการ์ดแต่ละประเภท
        slot_types = [CardType.NAVIGATION, CardType.COLLISION_AVOIDANCE, CardType.RECOVERY_BEHAVIOR]
        for i, card_type in enumerate(slot_types):
            x = start_x + i * (Config.CARD_SLOT_WIDTH + Config.CARD_SLOT_SPACING)
            self.slots.append(CardSlot((x, start_y), card_type))

    def draw(self, screen: pygame.Surface, dragging_card: Optional[Card] = None):
        # วาดพื้นหลังโต๊ะ
        screen.blit(self.background, (0, 0))
        
        # วาดช่องวางการ์ดทั้งหมด
        for slot in self.slots:
            slot.draw(screen, dragging_card)

    def handle_card_drag(self, card: Card, mouse_pos: tuple[int, int]):
        """จัดการการลากการ์ด"""
        print(f"\n[Stage] Handling card drag: {card.card_type} - {card.card_name}")
        print(f"[Stage] Mouse position: {mouse_pos}")
        
        card.hovering_area = None  # รีเซ็ตค่าเริ่มต้น
        card.hovering_over_card = False
        
        # ตรวจสอบว่าการ์ดอยู่เหนือช่องใดๆ
        for slot in self.slots:
            # ตรวจสอบทุกช่องเพื่อแสดง debug info
            if slot.valid_area_rect.collidepoint(mouse_pos):
                print(f"[Stage] Card is over slot: {slot.card_type}")
                # ตรวจสอบว่าการ์ดสามารถวางในช่องนี้ได้
                if slot.can_accept_card(card):
                    print("[Stage] Slot can accept card")
                    card.hovering_area = slot.card_type.value
                    if slot.card is not None:
                        card.hovering_over_card = True
                    return  # ออกจากฟังก์ชันเมื่อพบช่องที่เหมาะสม
        
        # ถ้าไม่พบช่องที่เหมาะสม
        card.hovering_area = None

    def place_card(self, card: Card, position: tuple[int, int]) -> bool:
        """พยายามวางการ์ดในช่องที่เหมาะสม"""
        print(f"\n[Stage] Attempting to place card: {card.card_type} - {card.card_name}")
        print(f"[Stage] At position: {position}")
        
        # ตรวจสอบตำแหน่งกับทุกช่อง
        found_valid_slot = False
        for slot in self.slots:
            if slot.valid_area_rect.collidepoint(position):
                found_valid_slot = True
                print(f"[Stage] Found slot: {slot.card_type}")
                
                # ตรวจสอบว่าการ์ดสามารถวางในช่องนี้ได้
                if slot.can_accept_card(card):
                    print("[Stage] Slot can accept card, placing...")
                    # ถ้ามีการ์ดเก่าอยู่ ให้คืนกลับไปที่ deck
                    if slot.card is not None:
                        print(f"[Stage] Returning old card: {slot.card.card_name} to deck")
                        old_card = slot.card
                        old_card.current_area = "deck"
                        old_card.position = old_card.original_position
                        # ทำให้แน่ใจว่าการ์ดเก่าถูกลบออกจาก slot ก่อนวางการ์ดใหม่
                        slot.card = None
                    
                    # วางการ์ดใหม่
                    print(f"[Stage] Placing new card: {card.card_name} in slot: {slot.card_type}")
                    slot.card = card
                    card.position = slot.rect.center
                    print("[Stage] Card placement successful")
                    return True
                else:
                    print(f"[Stage] Card type mismatch: {card.card_type} cannot be placed in {slot.card_type}")
        
        if not found_valid_slot:
            print("[Stage] No valid slot found at position", position)
        return False

    def get_slot_at_position(self, pos: Tuple[int, int]) -> Optional[CardSlot]:
        for slot in self.slots:
            if slot.valid_area_rect.collidepoint(pos):
                return slot
        return None
