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
    
    def handle_events(self):
        """Handle all game events."""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            # จัดการการเคลื่อนไหวของเมาส์สำหรับปุ่ม
            elif event.type == pygame.MOUSEMOTION:
                self.stage.handle_mouse_motion(event.pos)
            
            # จัดการการคลิกปุ่ม
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                button_action = self.stage.handle_button_click(event.pos)
                if button_action:
                    self.handle_button_action(button_action)
        
        # Handle card events
        self.card_deck.handle_events(events)
    
    def handle_button_action(self, action: str):
        """จัดการกับการคลิกปุ่ม
        
        Args:
            action (str): ชื่อของการกระทำจากปุ่มที่ถูกคลิก
        """
        if action == "reset":
            self.reset_game()
        elif action == "start":
            self.start_game()
    
    def reset_game(self):
        """รีเซ็ตเกมกลับสู่สถานะเริ่มต้น โดยย้ายการ์ดทั้งหมดจาก stage กลับไปที่ deck"""
        print("[GameManager] Resetting game...")
        
        # ลบการ์ดจากทุกช่อง
        for slot in self.stage.slots:
            slot.card = None
        
        # เรียกใช้ reset_cards จาก card_deck
        self.card_deck.reset_cards()
        
        # เปลี่ยนสถานะเกมเป็น PLAYING
        self.game_state.change_state("PLAYING")
    
    def start_game(self):
        """เริ่มเกม"""
        print("[GameManager] Starting game...")
        # เปลี่ยนสถานะเกมเป็น PLAYING
        self.game_state.change_state("PLAYING")
    
    def update(self):
        """Update game state."""
        self.card_deck.update()
        self.game_state.update()
    
    def draw(self):
        """Draw all game elements."""
        # Clear the screen
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # หาการ์ดที่กำลังลากอยู่
        dragging_card = None
        for card in self.card_deck.cards:
            if card.dragging:
                dragging_card = card
                break
        
        # Draw stage first (background and slots)
        self.stage.draw(self.screen, dragging_card)
        
        # Draw game elements
        self.card_deck.draw(self.screen)
        
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