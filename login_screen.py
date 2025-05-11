"""
Login Screen module for handling user authentication.
"""
import pygame
import time
import os
from config import Config
from player_data import PlayerData

class TextInput:
    """
    Class for handling text input in the login screen.
    """
    def __init__(self, x, y, width, height, font_size=32):
        """
        Initialize text input box.
        
        Args:
            x (int): X position
            y (int): Y position
            width (int): Width of input box
            height (int): Height of input box
            font_size (int): Font size for input text
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = pygame.Color(180, 180, 180)  # Light gray
        self.color_active = pygame.Color(255, 255, 255)    # White
        self.color = self.color_inactive
        self.font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", font_size)
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_time = 0.5  # Blink every 0.5 seconds
        
    def handle_event(self, event):
        """
        Handle events for text input.
        
        Args:
            event (pygame.event.Event): Pygame event
            
        Returns:
            bool: True if enter key was pressed, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active state
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            return False
            
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Limit text length to prevent overflow
                    if len(self.text) < 20:  # Max 20 characters
                        self.text += event.unicode
                return False
        return False
                
    def update(self):
        """Update cursor blinking."""
        # Update cursor blink
        current_time = time.time()
        if current_time - self.cursor_timer > self.cursor_blink_time:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
            
    def draw(self, screen):
        """
        Draw the text input box.
        
        Args:
            screen (pygame.Surface): Surface to draw on
        """
        # Draw background
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.color)
        
        # Calculate text position (centered vertically, left-aligned with padding)
        text_x = self.rect.x + 10  # 10px padding
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        
        # Draw text
        screen.blit(text_surface, (text_x, text_y))
        
        # Draw cursor if active
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width()
            cursor_y1 = text_y
            cursor_y2 = text_y + text_surface.get_height()
            pygame.draw.line(screen, self.color, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

class LoginScreen:
    """
    Class for handling the login screen.
    """
    def __init__(self, screen_width, screen_height):
        """
        Initialize login screen.
        
        Args:
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active = True
        self.username = ""
        self.player_data = PlayerData()
        self.is_returning_player = False
        self.returning_player_info = ""
        
        # Calculate popup dimensions
        self.popup_width = 500
        self.popup_height = 350  # Increased height for additional text
        self.popup_x = (screen_width - self.popup_width) // 2
        self.popup_y = (screen_height - self.popup_height) // 2
        
        # Create text input
        input_width = 300
        input_height = 50
        input_x = self.popup_x + (self.popup_width - input_width) // 2
        input_y = self.popup_y + 130
        self.text_input = TextInput(input_x, input_y, input_width, input_height)
        
        # Create login button
        self.button_width = 150
        self.button_height = 50
        self.button_x = self.popup_x + (self.popup_width - self.button_width) // 2
        self.button_y = self.popup_y + 250  # Adjusted button position down
        self.button_rect = pygame.Rect(self.button_x, self.button_y, self.button_width, self.button_height)
        self.button_color = pygame.Color(100, 180, 100)  # Green
        self.button_hover_color = pygame.Color(120, 200, 120)  # Lighter green
        self.button_is_hovered = False
        
        # Initialize fonts
        font_path = "font/PixelifySans-SemiBold.ttf"
        self.title_font = pygame.font.Font(font_path, 36)
        self.label_font = pygame.font.Font(font_path, 24)
        self.info_font = pygame.font.Font(font_path, 18)
        self.button_font = pygame.font.Font(font_path, 24)
        
    def handle_events(self, events):
        """
        Handle events for login screen.
        
        Args:
            events (list): List of pygame events
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        for event in events:
            # Check for enter key in text input
            if self.text_input.handle_event(event):
                return self._attempt_login()
                
            # Check for button click
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rect.collidepoint(event.pos):
                    return self._attempt_login()
            
            # Check for button hover
            if event.type == pygame.MOUSEMOTION:
                self.button_is_hovered = self.button_rect.collidepoint(event.pos)
            
            # Check for returning player immediately when typing
            if event.type == pygame.KEYUP and self.text_input.active:
                self._check_returning_player()
                
        return False
        
    def _check_returning_player(self):
        """Check if player already exists in the system"""
        username = self.text_input.text
        if len(username) >= 3 and self.player_data.player_exists(username):
            self.is_returning_player = True
            
            # Read player data to display information
            player_file = self.player_data.get_player_file_path(username)
            try:
                import json
                with open(player_file, 'r', encoding='utf-8') as f:
                    player_data = json.load(f)
                    level = player_data.get("current_level", 1)
                    highest_level = player_data.get("highest_completed_level", 0)
                    
                    unlocked_cards = 0
                    for card_type, cards in player_data.get("unlocked_cards", {}).items():
                        unlocked_cards += len(cards)
                        
                    self.returning_player_info = f"Level: {level}, Highest level: {highest_level}, Unlocked cards: {unlocked_cards}"
            except:
                self.returning_player_info = "Player data found (unable to read details)"
        else:
            self.is_returning_player = False
            self.returning_player_info = ""
        
    def _attempt_login(self):
        """
        Attempt to login with the current username.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        if len(self.text_input.text) >= 3:
            self.username = self.text_input.text
            self.active = False
            
            # If player exists, load their data
            if self.player_data.player_exists(self.username):
                self.player_data.load_player_data(self.username)
                print(f"[LoginScreen] Welcome back, {self.username}!")
                
                # ต้องมีการอัปเดตการ์ดที่ปลดล็อกแล้วในเด็คการ์ด แต่ยังไม่สามารถเข้าถึง card_deck ได้โดยตรงจากที่นี่
                # จึงต้องตั้งค่าแฟล็กเพื่อให้ GameManager รู้ว่าต้องอัปเดตการ์ด
                self.is_returning_player = True  # ใช้แฟล็กนี้เพื่อบอกว่าต้องอัปเดตการ์ด
            else:
                print(f"[LoginScreen] New player: {self.username}")
                self.is_returning_player = False
                
            return True
        return False
        
    def update(self):
        """Update login screen elements."""
        self.text_input.update()
        
    def draw(self, screen):
        """
        Draw the login screen.
        
        Args:
            screen (pygame.Surface): Surface to draw on
        """
        if not self.active:
            return
            
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Black with 150 alpha
        screen.blit(overlay, (0, 0))
        
        # Draw popup background
        popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
        pygame.draw.rect(screen, (50, 50, 50), popup_rect)  # Dark gray background
        pygame.draw.rect(screen, (100, 100, 100), popup_rect, 2)  # Light gray border
        
        # Draw title
        title_text = self.title_font.render("Welcome to Nav Card Game", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=self.popup_x + self.popup_width // 2, y=self.popup_y + 30)
        screen.blit(title_text, title_rect)
        
        # Draw label
        label_text = self.label_font.render("Please enter your name:", True, (255, 255, 255))
        label_rect = label_text.get_rect(centerx=self.popup_x + self.popup_width // 2, y=self.popup_y + 90)
        screen.blit(label_text, label_rect)
        
        # Draw text input
        self.text_input.draw(screen)
        
        # Display returning player message
        if self.is_returning_player:
            welcome_text = self.info_font.render("Welcome back! Your data will be loaded automatically", True, (100, 255, 100))
            welcome_rect = welcome_text.get_rect(centerx=self.popup_x + self.popup_width // 2, y=self.popup_y + 190)
            screen.blit(welcome_text, welcome_rect)
            
            info_text = self.info_font.render(self.returning_player_info, True, (200, 200, 200))
            info_rect = info_text.get_rect(centerx=self.popup_x + self.popup_width // 2, y=self.popup_y + 215)
            screen.blit(info_text, info_rect)
        
        # Draw button
        button_color = self.button_hover_color if self.button_is_hovered else self.button_color
        pygame.draw.rect(screen, button_color, self.button_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.button_rect, 2, border_radius=5)  # White border
        
        # Draw button text
        button_text = self.button_font.render("Start Game", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=self.button_rect.center)
        screen.blit(button_text, button_text_rect)
        
    def get_username(self):
        """
        Get the entered username.
        
        Returns:
            str: Username
        """
        return self.username 