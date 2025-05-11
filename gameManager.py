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
from state import GameState, GameStateEnum
from stage import Stage
from costmap import Costmap
from login_screen import LoginScreen
from statistic import Statistics
from player_data import PlayerData

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
        
        # Initialize game state first
        self.game_state = GameState()  # Use singleton pattern
        
        # Initialize statistics
        self.statistics = Statistics()
        
        # Initialize player data manager
        self.player_data = PlayerData()
        
        # Initialize login screen
        self.login_screen = LoginScreen(self.window_width, self.window_height)
        
        # Initialize game components
        self.stage = Stage()
        self.card_deck = CardDeck(self.stage)
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
        
        # Camera variables
        self.camera_y = 0
        self.target_camera_y = 0
        self.camera_speed = 0.05  # Speed of camera movement (0-1, 1 = instant)
        self.camera_animating = False
        
        # Timer for auto-starting algorithm
        self.algorithm_start_time = 0
        self.should_auto_start = False
        self.auto_start_delay = 2 
        
        # Variables for displaying newly unlocked cards
        self.new_cards_notification = False
        self.new_cards = []
        self.notification_start_time = 0
        self.notification_duration = 5  # Display for 5 seconds
        
        # Load map for current level
        self.load_current_level_map()
        
        # Update level button states
        self.update_level_buttons()
        
        # Variables for displaying time
        self.timer_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 36)
        self.timer_rect = pygame.Rect(0, 0, 350, 50)  # Define area for time display
        self.timer_rect.centerx = self.window_width // 2
        self.timer_rect.top = 20
    
    def handle_events(self):
        """Handle all game events."""
        events = pygame.event.get()
        
        # ถ้าอยู่ในหน้าล็อกอิน ให้จัดการอีเวนต์ของหน้าล็อกอินเท่านั้น
        if self.game_state.get_state() == GameStateEnum.LOGIN.value:
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # จัดการอีเวนต์ของหน้าล็อกอิน
            login_success = self.login_screen.handle_events(events)
            if login_success:
                # เมื่อล็อกอินสำเร็จ ให้เปลี่ยนสถานะเกมเป็น CARD_CHOOSING
                username = self.login_screen.get_username()
                self.game_state.set_username(username)
                self.statistics.set_username(username)
                self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
                print(f"User logged in as: {username}")
                
                # ตรวจสอบว่าเป็นผู้เล่นเก่าที่โหลดข้อมูลมาหรือไม่
                if self.login_screen.is_returning_player:
                    print(f"[GameManager] Updating cards for returning player: {username}")
                    
                    # แสดงข้อมูลการ์ดที่ปลดล็อกจาก GameState
                    unlocked_cards = self.game_state.get_unlocked_cards()
                    print(f"[GameManager] Unlocked cards from GameState:")
                    for card_type, cards in unlocked_cards.items():
                        print(f"  {card_type}: {cards}")
                    
                    # ลำดับการทำงานสำคัญมาก:
                    # 1. อัปเดตการ์ดในเด็คตามข้อมูลที่โหลดมา
                    cards_added = self.card_deck.update_available_cards()
                    print(f"[GameManager] Cards updated: {cards_added}")
                    
                    # 2. โหลดแผนที่ของระดับปัจจุบัน (ต้องทำก่อน reset_game)
                    self.load_current_level_map()
                    
                    # 3. อัปเดตปุ่มเลือกระดับตามระดับปัจจุบัน (ต้องทำก่อน reset_game)
                    self.update_level_buttons()
                    
                    # 4. รีเซ็ตเกมเพื่อให้แน่ใจว่าทุกอย่างถูกตั้งค่าอย่างถูกต้อง
                    # รวมถึงการรีเซ็ตการ์ดด้วย
                    self.reset_game()
                    
                    print(f"[GameManager] Player data loaded and game initialized successfully.")
                
            return
            
        # ตรวจสอบการกด ESC เพื่อเข้าสู่โหมด PAUSE
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ถ้าอยู่ในโหมด PAUSE ให้กลับไปยังสถานะก่อนหน้า
                if self.game_state.get_state() == GameStateEnum.PAUSE.value:
                    # หากกำลังเล่นอยู่ในโหมด PLAYING ก่อนจะ PAUSE
                    # ให้เริ่มจับเวลาใหม่โดยตั้งค่าเวลาเริ่มต้นใหม่
                    # การรีเซ็ตนี้ทำให้เวลาเริ่มนับต่อจากจุดที่หยุดไว้
                    self.statistics.start_timer()
                    
                    # เปลี่ยนกลับไปยังสถานะก่อนหน้า (PLAYING หรือ CARD_CHOOSING)
                    if self.camera_y > 0:
                        self.game_state.change_state(GameStateEnum.PLAYING.value)
                    else:
                        self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
                    return  # ดำเนินการต่อโดยไม่ต้องทำส่วนอื่น
                    
                # เข้าสู่โหมด PAUSE
                self.game_state.change_state(GameStateEnum.PAUSE.value)
                
                # หยุดการจับเวลาชั่วคราว
                self.statistics.stop_timer(pause=True)
                return  # ดำเนินการต่อโดยไม่ต้องทำส่วนอื่น
        
        # ถ้าอยู่ในโหมด PAUSE ไม่ต้องประมวลผลอีเวนต์อื่นๆ
        if self.game_state.get_state() == GameStateEnum.PAUSE.value:
            return
        
        # ถ้าไม่ได้อยู่ในหน้าล็อกอิน ให้จัดการอีเวนต์ของเกมตามปกติ
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
                    if event.key == pygame.K_SPACE:
                        if self.game_state.get_state() == GameStateEnum.PLAYING.value:
                            print("[GameManager] Spacebar pressed in PLAYING mode, returning to CARD_CHOOSING mode")
                            
                            # หยุดอัลกอริทึมที่กำลังทำงาน
                            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                                self.current_algorithm.stop()
                                self.current_algorithm = None
                            
                            # ล้างเส้นทางสีเขียว โดยไม่โหลดแผนที่ใหม่
                            self.costmap.reset()
                            print("[GameManager] Reset costmap, cleared path only")
                            
                            # เลื่อนกล้องลงและเปลี่ยนเป็นโหมด CARD_CHOOSING โดยตรง
                            self.target_camera_y = 0
                            self.camera_animating = True
                            
                            # หยุดการจับเวลา
                            if self.statistics.is_timing:
                                self.statistics.stop_timer()
                                self.statistics.set_completion_success(False)
                                # ไม่บันทึกข้อมูลเนื่องจากเป็นการยกเลิก
                                # self.statistics.save_all_data()
                            
                            # เปลี่ยนสถานะเกมเป็น CARD_CHOOSING
                            self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
                            
                            # ตั้งค่าไม่ให้อยู่ในโหมดเกม
                            self.card_deck.set_game_stage(False)
                            
                            # แสดงปุ่มทั้งหมดอีกครั้ง
                            print("Showing all buttons including start and reset")
                            for button in self.stage.buttons:
                                button.set_visible(True)
                                
                        elif self.game_state.get_state() == GameStateEnum.FINISH.value:
                            # When in FINISH mode and Space is pressed, start a new game
                            print("[GameManager] Spacebar pressed in FINISH mode, returning to CARD_CHOOSING mode")
                            
                            # Store current state for later use
                            was_successful = self.statistics.completion_success
                            current_level = self.game_state.get_current_level()
                            print(f"[GameManager] Level {current_level} completion: {was_successful}")
                            
                            # If successful, advance to next level automatically
                            if was_successful:
                                print("[GameManager] Successfully completed level, advancing to next level")
                                # Advance to next level if not at max level already
                                if current_level < 11:  # 11 is the maximum level
                                    # Call advance_to_next_level to handle unlocking cards, etc.
                                    self.advance_to_next_level()
                                    # This will unlock cards, load the new map, etc.
                                else:
                                    print("[GameManager] Already at maximum level, not advancing")
                            else:
                                # Clear path and reset state
                                self.costmap.reset()
                            
                            # Move camera down and change to CARD_CHOOSING mode directly
                            self.target_camera_y = 0
                            self.camera_animating = True
                            
                            # Change game state to CARD_CHOOSING
                            self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
                            
                            # Set state to not be in game mode
                            self.card_deck.set_game_stage(False)
                            
                            # Show all buttons again
                            for button in self.stage.buttons:
                                button.set_visible(True)
                                
                            # Update level buttons to ensure next level is available if completed
                            self.update_level_buttons()
                            print(f"[GameManager] Buttons updated. Current level: {self.game_state.get_current_level()}, Highest completed: {self.game_state.highest_completed_level}")
                    # เพิ่มปุ่ม N สำหรับเลื่อนไปด่านถัดไป (สำหรับการทดสอบ)
                    elif event.key == pygame.K_n:
                        self.advance_to_next_level()
                except Exception as e:
                    print(f"Error handling key press: {e}")
            
            # Handle button clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    # แยกจัดการสำหรับปุ่มที่เป็น level_button
                    button_clicked = False
                    for button in self.stage.buttons:
                        if hasattr(button, 'is_level_button') and button.is_level_button and button.is_visible:
                            # ปุ่มเปลี่ยนระดับต้องใช้ตำแหน่งเมาส์โดยตรง ไม่ต้องปรับ offset
                            if button.rect.collidepoint(event.pos):
                                print(f"[GameManager] Level button clicked: {button.action_name}")
                                self.handle_button_action(button.action_name)
                                button_clicked = True
                                break
                    
                    # ถ้ายังไม่มีการคลิกปุ่มเปลี่ยนระดับ ให้ตรวจสอบปุ่มอื่นๆ
                    if not button_clicked:
                        # ส่งตำแหน่งเมาส์ไปยัง stage เพื่อตรวจสอบการคลิกปุ่มอื่นๆ
                        button_action = self.stage.handle_button_click(event.pos)
                        if button_action:
                            self.handle_button_action(button_action)
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
        """Handle button clicks.
        
        Args:
            action (str): Action name from the button
        """
        print(f"[GameManager] Handling button action: {action}")
        
        try:
            # Try to perform the action
            if action == "start":
                # Start game with current card configuration
                self.start_game()
                
            elif action == "reset":
                # Reset game
                self.reset_game()
                
            elif action == "next_level_valid":
                # Go to next level
                self.advance_to_next_level()
                
            elif action == "prev_level_valid":
                # Go to previous level
                self.go_to_previous_level()
            
            # After handling button action, update button visibility
            self.update_level_buttons()
            
        except Exception as e:
            print(f"Error handling button action: {e}")
            
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
            
    def load_current_level_map(self):
        """
        Load map for the current level and set start position, goal and time limit from levels.csv
        """
        try:
            # Get current level number
            current_level = self.game_state.get_current_level()
            
            # Update level in statistics
            self.statistics.set_level(current_level)
            
            # Read data from levels.csv file
            import csv
            level_data = None
            levels_csv_path = os.path.join("data", "levels.csv")
            
            if os.path.exists(levels_csv_path):
                with open(levels_csv_path, 'r') as csvfile:
                    csv_reader = csv.DictReader(csvfile)
                    for row in csv_reader:
                        map_level = row['map'].replace('map', '').replace('.pgm', '')
                        if int(map_level) == current_level:
                            level_data = row
                            break
            
            # Create map filename based on level
            map_file = f"map{current_level}.pgm"
            pgm_file_path = os.path.join("data", map_file)
            
            if os.path.exists(pgm_file_path):
                success = self.costmap.load_pgm_map(pgm_file_path)
                if success:
                    print(f"Successfully loaded map for level {current_level} from {pgm_file_path}")
                    
                    # If we have data from levels.csv, set start position and goal
                    if level_data:
                        # Set robot position (start)
                        start_row = int(level_data['start_row'])
                        start_col = int(level_data['start_col'])
                        self.costmap.set_robot_position(start_row, start_col)
                        
                        # Set goal position
                        finish_row = int(level_data['finish_row'])
                        finish_col = int(level_data['finish_col'])
                        self.costmap.set_goal_position(finish_row, finish_col)
                        
                        # Set time limit for this level
                        time_limit = int(level_data['time_limit'])
                        self.statistics.set_time_limit(time_limit)
                        print(f"Set time limit for level {current_level} to {time_limit} seconds")
                        
                        print(f"Set robot position to ({start_row}, {start_col}) and goal to ({finish_row}, {finish_col})")
                else:
                    print(f"Failed to load map for level {current_level} from {pgm_file_path}")
                    # If loading fails, use general map
                    self.load_map()
            else:
                print(f"No map file found for level {current_level} at {pgm_file_path}")
                # If no map file for this level, use general map
                self.load_map()
        except Exception as e:
            print(f"Error loading level map: {e}")
            # Continue without crashing
    
    def reset_game(self):
        """
        Reset the game state to initial conditions.
        
        This includes:
        - Resetting the costmap
        - Resetting camera position
        - Changing game state
        - Showing all buttons
        - Stopping any running algorithm
        """
        try:
            print("[GameManager] Resetting game...")
            
            # Reset the costmap
            self.costmap.reset()
            
            # Recalculate camera position
            self.target_camera_y = 0
            self.camera_animating = True
            
            # Change game state to CARD_CHOOSING
            self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
            
            # Reset all cards back to the deck using CardDeck's reset method
            self.card_deck.reset_cards()  # ใช้ reset_cards แทน reset เพื่อจัดการกับการ drag
            
            # Set state to card selection mode (ไม่ใช่โหมดเกมเพลย์)
            self.card_deck.set_game_stage(False)
            
            # เพิ่มการตรวจสอบว่าการ์ดถูกรีเซ็ตเรียบร้อยแล้ว
            print("[GameManager] Verifying all cards reset to deck...")
            all_slots_empty = True
            for slot in self.stage.slots:
                if slot.card is not None:
                    all_slots_empty = False
                    print(f"[GameManager] WARNING: Slot {slot.card_type.value} still has card: {slot.card.card_name}")
                    # บังคับให้ slot.card เป็น None
                    slot.card = None
            
            if all_slots_empty:
                print("[GameManager] All slots are empty after reset")
                
            # หยุดและล้างอัลกอริทึมปัจจุบัน
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                self.current_algorithm.stop()
                self.current_algorithm = None
                print("[GameManager] Current algorithm stopped and cleared")
                
            # แสดงปุ่มทั้งหมด
            self.show_all_buttons()
            
            # ปิดการแจ้งเตือนการ์ดใหม่
            self.new_cards_notification = False
            
        except Exception as e:
            print(f"Error resetting game: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # ตรวจสอบอีกครั้งว่า current_algorithm เป็น None
            self.current_algorithm = None
            
    def show_all_buttons(self):
        """Show all buttons in the game, including start and reset buttons."""
        print("[GameManager] Showing all buttons")
        for button in self.stage.buttons:
            button.set_visible(True)
            
        # ตรวจสอบและอัปเดตปุ่มเปลี่ยนระดับ
        self.update_level_buttons()
    
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
            self.game_state.change_state(GameStateEnum.PLAYING.value)
            
            # Set state to gameplay mode
            self.card_deck.set_game_stage(True)
            
            # ตรวจสอบและรีเซ็ตตำแหน่งหุ่นยนต์ถ้าไม่ได้อยู่ที่จุดเริ่มต้น
            self.__check_and_reset_robot_position()
            
            # Set camera target position to move down half the screen (use positive value)
            self.target_camera_y = self.window_height / 1.8
            self.camera_animating = True
            
            # Hide all game buttons except level buttons
            for button in self.stage.buttons:
                if not hasattr(button, 'is_level_button') or not button.is_level_button:
                    button.set_visible(False)
                else:
                    # ปุ่มเปลี่ยนแมพยังคงแสดงในโหมด PLAYING
                    button.set_visible(True)
            
            # ตรวจสอบว่ามีการวางการ์ดในช่องหรือไม่
            has_cards = False
            for slot in self.stage.slots:
                if slot.card:
                    has_cards = True
                    break
            
            if has_cards:
                # มีการ์ดวางอยู่ ตั้งเวลาสำหรับเริ่มอัลกอริทึมอัตโนมัติ
                self.algorithm_start_time = time.time()
                self.should_auto_start = True
                
                # Start timer
                self.statistics.start_timer()
                
                # Show message to user about auto-starting
                print("--------------------------------------------")
                print(f"Game will start automatically in {self.auto_start_delay} seconds")
                print("--------------------------------------------")
            else:
                # ไม่มีการ์ดวางอยู่ ข้ามการเริ่มอัลกอริทึมอัตโนมัติ
                self.should_auto_start = False
                
                # รีเซ็ตอัลกอริทึมเป็น None
                if hasattr(self, 'current_algorithm') and self.current_algorithm:
                    self.current_algorithm.stop()
                self.current_algorithm = None
                print("[GameManager] Reset algorithm to None due to no cards placed")
                
                print("--------------------------------------------")
                print("No cards placed. Auto-start skipped. Viewing map only.")
                print("--------------------------------------------")
                
        except Exception as e:
            print(f"Error starting game: {e}")
            # Continue without crashing
    
    def run_algorithm(self):
        """Run the selected algorithm."""
        try:
            print("[GameManager] Running algorithm...")
            
            # ตรวจสอบว่ามีการวางการ์ดในแต่ละช่องหรือไม่
            has_cards = False
            print("--------------------------------------------")
            print("[GameManager] ตรวจสอบการ์ดในแต่ละช่อง:")
            for i, slot in enumerate(self.stage.slots):
                if slot.card:
                    has_cards = True
                    print(f"  ช่อง {i+1} ({slot.card_type.value}): {slot.card.card_name}")
                else:
                    print(f"  ช่อง {i+1} ({slot.card_type.value}): ว่างเปล่า (None)")
            print("--------------------------------------------")
                    
            if not has_cards:
                print("[GameManager] No cards placed in any slots, cannot start algorithm")
                # รีเซ็ตอัลกอริทึมเป็น None เมื่อไม่มีการ์ด
                if hasattr(self, 'current_algorithm') and self.current_algorithm:
                    self.current_algorithm.stop()
                    self.current_algorithm = None
                    print("[GameManager] Reset algorithm to None due to no cards placed")
                return
            
            # บันทึกอัลกอริทึมที่ใช้
            algorithm_name, algorithm_type = self.stage.get_selected_algorithm()
            if algorithm_name:
                print(f"[GameManager] เลือกใช้อัลกอริทึม: {algorithm_name} ({algorithm_type})")
                self.statistics.set_algorithm(algorithm_name, algorithm_type)
            
            # เรียกอัลกอริทึมจาก stage
            print("[GameManager] กำลังเรียกใช้ run_algorithm() ของ stage...")
            result = self.stage.run_algorithm(self.costmap, self.statistics)
            
            # ตรวจสอบค่าที่ได้จาก run_algorithm
            if result is None:
                # กรณีไม่มีการ์ดในช่อง (ไม่ใช่ error แต่ไม่มีการ์ด)
                print("[GameManager] No cards in slots, algorithm set to None")
                # รีเซ็ตอัลกอริทึมเป็น None
                if hasattr(self, 'current_algorithm') and self.current_algorithm:
                    self.current_algorithm.stop()
                    self.current_algorithm = None
                return
            elif result is False:
                # กรณีเกิดข้อผิดพลาดในการเริ่มอัลกอริทึม
                print("[GameManager] Failed to start algorithm due to errors")
                return
                
            algorithm_class, costmap = result
            print(f"[GameManager] ได้รับคลาสอัลกอริทึม: {algorithm_class.__name__}")
            
            # สร้างอินสแตนซ์ของอัลกอริทึม
            print("[GameManager] กำลังสร้างอินสแตนซ์ของอัลกอริทึม...")
            self.current_algorithm = algorithm_class(costmap)
            
            # เริ่มอัลกอริทึม
            print("[GameManager] กำลังเริ่มอัลกอริทึม...")
            success = self.current_algorithm.start()
            if not success:
                print("[GameManager] Failed to start algorithm")
                self.current_algorithm = None
                return
                
            print("--------------------------------------------")
            print(f"Running algorithm {algorithm_name}, please wait...")
            print("--------------------------------------------")
            
        except Exception as e:
            print(f"Error running algorithm: {e}")
            # Continue without crashing
    
    def on_algorithm_complete(self, success, path_length=0):
        """Handle completion of algorithm (robot reached goal or failed)."""
        try:
            print(f"[GameManager] Algorithm completed with success: {success}, path length: {path_length}")
            
            # Stop timer and save statistics
            if self.statistics.is_timing:
                self.statistics.stop_timer()
                self.statistics.set_completion_success(success)
                print(f"[GameManager] Setting completion_success to: {success}")
                self.statistics.save_all_data()
            
            # Mark level as completed if successful and change state to FINISH
            if success:
                # Record that player has completed this level
                completed = self.game_state.complete_current_level()
                print(f"[GameManager] Level completion status updated: {completed}")
                
                # Check if there are new cards to unlock for the next level
                next_level = self.game_state.get_current_level() + 1
                if next_level <= 11:  # Ensure we're not beyond the last level
                    potential_unlocks = self.game_state.level_unlocks.get(next_level, [])
                    if potential_unlocks:
                        print(f"[GameManager] Potential cards to unlock at level {next_level}: {len(potential_unlocks)}")
                
                # Save player data
                self.player_data.save_player_data(self.game_state.get_username())
            
            # Change to FINISH state after processing completion
            self.game_state.change_state(GameStateEnum.FINISH.value)
            print(f"[GameManager] State changed to FINISH. Success: {success}")
            
            # Update level buttons to reflect new state - important for showing next level button
            self.update_level_buttons()
            
            # Force the next level button to be visible if level was completed successfully
            if success:
                for button in self.stage.buttons:
                    # Make next level button visible and bring to front
                    if button.action_name == "next_level_valid":
                        button.set_visible(True)
                        # Ensure the invalid button is hidden
                    elif button.action_name == "next_level_invalid":
                        button.set_visible(False)
            
        except Exception as e:
            print(f"Error in algorithm complete callback: {e}")
            # If error occurs, still set completion status to ensure proper display
            self.statistics.set_completion_success(success)
            # Ensure we change to FINISH state even if there's an error
            self.game_state.change_state(GameStateEnum.FINISH.value)
    
    def update(self):
        """Update the game state."""
        try:
            # If in login screen, update login screen only
            if self.game_state.get_state() == GameStateEnum.LOGIN.value:
                self.login_screen.update()
                return
                
            # If in PAUSE mode, don't update anything
            if self.game_state.get_state() == GameStateEnum.PAUSE.value:
                return
                
            # Update camera animation
            if self.camera_animating:
                diff = self.target_camera_y - self.camera_y
                if abs(diff) > 0.5:
                    self.camera_y += diff * self.camera_speed
                else:
                    self.camera_y = self.target_camera_y
                    self.camera_animating = False
                    
                    # Set game state based on camera position
                    if self.camera_y > 0 and self.game_state.get_state() == GameStateEnum.CARD_CHOOSING.value:
                        self.game_state.change_state(GameStateEnum.PLAYING.value)
                        print("[GameManager] State changed to PLAYING")
                        
                        # ตรวจสอบและรีเซ็ตตำแหน่งหุ่นยนต์ถ้าไม่ได้อยู่ที่จุดเริ่มต้น
                        self.__check_and_reset_robot_position()
                        
                    elif self.camera_y <= 0 and self.game_state.get_state() == GameStateEnum.PLAYING.value:
                        self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
                        print("[GameManager] State changed to CARD_CHOOSING")
            
            # Check if algorithm should auto-start
            if self.should_auto_start and time.time() - self.algorithm_start_time >= self.auto_start_delay:
                self.should_auto_start = False
                self.run_algorithm()
                
            # Update game state
            self.game_state.update()
            
            # Update cards
            self.card_deck.update()
            
            # Check time limit when in PLAYING mode
            if self.game_state.get_state() == GameStateEnum.PLAYING.value and self.statistics.is_timing:
                elapsed_time = self.statistics.get_elapsed_time()
                time_limit = self.statistics.get_time_limit()
                
                # If time exceeds limit, stop game and show failure
                if elapsed_time > time_limit:
                    print(f"[GameManager] Time limit exceeded: {elapsed_time:.2f}/{time_limit} seconds")
                    
                    # Stop running algorithm
                    if hasattr(self, 'current_algorithm') and self.current_algorithm:
                        self.current_algorithm.stop()
                        self.current_algorithm.is_completed = False
                        
                    # Call callback when algorithm completes (failure)
                    self.on_algorithm_complete(False, 0)
                    
                    # Clear algorithm instance
                    self.current_algorithm = None
            
            # Update level buttons status
            if self.game_state.get_state() == GameStateEnum.CARD_CHOOSING.value:
                self.update_level_buttons()
                
            # Update algorithm if running
            if hasattr(self, 'current_algorithm') and self.current_algorithm and self.game_state.get_state() == GameStateEnum.PLAYING.value:
                # Update algorithm state
                still_running = self.current_algorithm.update()
                
                # Record robot position if moved
                if self.costmap.robot_pos:
                    self.statistics.add_robot_position(
                        self.costmap.robot_pos[0], 
                        self.costmap.robot_pos[1]
                    )
                
                # Check if robot has reached the goal
                if self.costmap.robot_pos and self.costmap.goal_pos:
                    robot_row, robot_col = self.costmap.robot_pos
                    goal_row, goal_col = self.costmap.goal_pos
                    
                    # คำนวณระยะห่างโดยใช้ทั้ง Manhattan distance และ Euclidean distance
                    manhattan_dist = abs(robot_row - goal_row) + abs(robot_col - goal_col)
                    euclidean_dist = ((robot_row - goal_row)**2 + (robot_col - goal_col)**2)**0.5
                    
                    # ใช้เกณฑ์ที่เข้มงวดกว่าเดิม - ต้องใกล้เป้าหมายจริงๆ
                    if manhattan_dist <= 1 and euclidean_dist <= 1.0:
                        print(f"[GameManager] Robot reached goal! Manhattan distance: {manhattan_dist}, Euclidean distance: {euclidean_dist:.2f}")
                        
                        # Force algorithm to stop running
                        self.current_algorithm.is_running = False
                        still_running = False
                        
                        # Mark algorithm as completed
                        self.current_algorithm.is_completed = True
                        
                        # Create path if none exists
                        if not hasattr(self.current_algorithm, 'path') or not self.current_algorithm.path:
                            self.current_algorithm.path = [(robot_row, robot_col)]
                    elif not still_running and not self.current_algorithm.is_completed:
                        # ถ้าอัลกอริทึมหยุดทำงานแล้วแต่ยังไม่ถึงเป้าหมาย
                        print(f"[GameManager] Algorithm stopped but goal not reached! Manhattan distance: {manhattan_dist}, Euclidean distance: {euclidean_dist:.2f}")
                        self.current_algorithm.is_completed = False
                
                # If algorithm has stopped, complete the level
                if not still_running:
                    print("[GameManager] Algorithm completed or stopped.")
                    
                    # Call callback when algorithm completes
                    success = self.current_algorithm.is_completed
                    path_length = len(self.current_algorithm.path) if hasattr(self.current_algorithm, 'path') else 0
                    self.on_algorithm_complete(success, path_length)
                    
                    # Clear algorithm instance
                    self.current_algorithm = None
                    
                    # Show message if successful
                    if success:
                        print(f"[GameManager] Completed level {self.game_state.get_current_level()}!")
                    
            # Update card unlock notification display
            if self.new_cards_notification:
                if time.time() - self.notification_start_time >= self.notification_duration:
                    self.new_cards_notification = False
        except Exception as e:
            print(f"Error updating game: {e}")
            # Continue without crashing
    
    def draw(self):
        """Draw all game elements."""
        try:
            # Clear the screen
            self.screen.fill(Config.BACKGROUND_COLOR)
            
            # If in login screen, draw login screen only
            if self.game_state.get_state() == GameStateEnum.LOGIN.value:
                self.login_screen.draw(self.screen)
                pygame.display.flip()
                return
                
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
            
            # สร้าง surface ชั่วคราวสำหรับวาดแผนที่
            map_surface = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            map_surface.fill((0, 0, 0, 0))  # ทำให้โปร่งใสทั้งหมด
            
            # วาดแผนที่ลงบน surface ชั่วคราว (ปรับตำแหน่งให้เป็น 0,0)
            self.costmap.draw(map_surface, (0, 0))
            
            # สร้าง mask สำหรับ clipping
            mask = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))  # ทำให้โปร่งใสทั้งหมด
            
            # วาดสี่เหลี่ยมบน mask ด้วยขอบมน
            pygame.draw.rect(
                mask, 
                (255, 255, 255, 255),  # สีขาวทึบ 
                (0, 0, rect_width, rect_height),
                0,  # ความหนา 0 คือเติมสีทั้งหมด
                border_radius=10  # ขอบมน
            )
            
            # ใช้ mask กับ map_surface (ทำ clipping)
            map_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            
            # นำแผนที่ไปวาดบนหน้าจอหลัก ตามตำแหน่งที่ต้องการ
            self.screen.blit(map_surface, rect_start)
            
            # Draw border in white, 3 pixels thick
            pygame.draw.rect(
                self.screen, 
                Config.WHITE_COLOR, 
                (rect_start[0], rect_start[1], rect_width, rect_height),
                3,  # Border thickness
                border_radius=10  # Rounded corners
            )
            
            # Draw buttons separately
            for button in self.stage.buttons:
                if hasattr(button, 'is_level_button') and button.is_level_button:
                    # Level buttons should always stay at fixed position on top
                    # แสดงปุ่มเปลี่ยนแมพเฉพาะเมื่อกล้องอยู่ด้านบน (camera_y > 150) 
                    # หรืออยู่ในสถานะ PLAYING เท่านั้น
                    if self.camera_y > 150 or self.game_state.get_state() == GameStateEnum.PLAYING.value:
                        # วาดปุ่มในตำแหน่งปกติโดยไม่คำนึงถึงตำแหน่งของกล้อง
                        original_pos = button.position
                        button.rect.center = original_pos  # ตำแหน่งเดิมของปุ่ม ไม่ขึ้นกับกล้อง
                        button.draw(self.screen)
                else:
                    # Other buttons move with camera
                    button.draw(self.screen, camera_offset)
            
            # Display information only when camera is at the top (camera_y > 0)
            # Do not display information when camera moves down (camera_y <= 0)
            if self.camera_y > 150:  # เปลี่ยนจาก 0 เป็น 150 เพื่อให้ข้อมูลหายเร็วขึ้น
                # Display information at normal position
                current_level = self.game_state.get_current_level()
                username = self.game_state.get_username()
                elapsed_time = self.statistics.get_elapsed_time()
                formatted_time = self.statistics.format_time(elapsed_time)
                font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 36)
                
                # Display level number (left)
                level_text = font.render(f"Level {current_level}", True, Config.WHITE_COLOR)
                self.screen.blit(level_text, (20, 20))
                
                # Display player name (right)
                username_text = font.render(f"Player: {username}", True, Config.WHITE_COLOR)
                username_rect = username_text.get_rect(topright=(self.window_width - 20, 20))
                self.screen.blit(username_text, username_rect)
                
                # Display elapsed time (center)
                timer_bg = pygame.Surface((350, 45), pygame.SRCALPHA)  # Increased width from 200 to 350
                timer_bg.fill((0, 0, 0, 128))
                timer_rect = timer_bg.get_rect(centerx=self.window_width // 2, top=20)
                self.screen.blit(timer_bg, timer_rect)
                
                # Display elapsed time and time limit
                time_limit = self.statistics.get_time_limit()
                timer_text = self.timer_font.render(f"{formatted_time} / {self.statistics.format_time(time_limit)}", True, Config.WHITE_COLOR)
                timer_text_rect = timer_text.get_rect(center=timer_rect.center)
                self.screen.blit(timer_text, timer_text_rect)
                
                # If time exceeded, show warning in red
                if elapsed_time > time_limit and self.game_state.get_state() == GameStateEnum.PLAYING.value:
                    time_warning = self.timer_font.render("Time Exceeded!", True, (255, 0, 0))
                    warning_rect = time_warning.get_rect(centerx=self.window_width // 2, top=timer_rect.bottom + 10)
                    self.screen.blit(time_warning, warning_rect)
                
                # If in FINISH mode, show additional message
                if self.game_state.get_state() == GameStateEnum.FINISH.value:
                    # Create transparent black background to dim the screen
                    overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))  # Transparent black (alpha 180/255)
                    self.screen.blit(overlay, (0, 0))
                    
                    result_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 48)
                    # Use completion_success from statistics for display
                    if self.statistics.completion_success:
                        result_text = result_font.render("Success!", True, (0, 255, 0))
                    else:
                        result_text = result_font.render("Failed!", True, (255, 0, 0))
                    result_rect = result_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
                    self.screen.blit(result_text, result_rect)
                    
                    hint_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
                    hint_text = hint_font.render("Press SPACE to continue", True, Config.WHITE_COLOR)
                    hint_rect = hint_text.get_rect(center=(self.window_width // 2, self.window_height // 2 + 60))
                    self.screen.blit(hint_text, hint_rect)
            
            # Display new card unlocked notification
            if self.new_cards_notification and self.new_cards:
                self.draw_new_cards_notification()
                
            # If in PAUSE mode, show message
            if self.game_state.get_state() == GameStateEnum.PAUSE.value:
                # Create transparent background
                pause_bg = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
                pause_bg.fill((0, 0, 0, 150))  # Transparent black
                self.screen.blit(pause_bg, (0, 0))
                
                # Show PAUSE text
                pause_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 72)
                pause_text = pause_font.render("PAUSE", True, Config.WHITE_COLOR)
                pause_rect = pause_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
                self.screen.blit(pause_text, pause_rect)
                
                # Show instruction
                hint_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
                hint_text = hint_font.render("Press ESC to continue", True, Config.WHITE_COLOR)
                hint_rect = hint_text.get_rect(center=(self.window_width // 2, self.window_height // 2 + 60))
                self.screen.blit(hint_text, hint_rect)
            
            # Update the display
            pygame.display.flip()
        except Exception as e:
            print(f"Error drawing game: {e}")
            # Continue without crashing
            
    def draw_new_cards_notification(self):
        """Display notification for newly unlocked cards"""
        try:
            # Check and display completion_success status for debugging
            print(f"[GameManager] Current completion_success: {self.statistics.completion_success}")
            
            # Create background for notification
            notification_width = 600  # Increased from 500 to 600
            notification_height = 400  # Increased from 300 to 400
            
            # Calculate center position of screen
            screen_width, screen_height = self.screen.get_size()
            x_pos = (screen_width - notification_width) // 2
            y_pos = (screen_height - notification_height) // 2
            
            # Create transparent background
            notification_bg = pygame.Surface((notification_width, notification_height), pygame.SRCALPHA)
            notification_bg.fill((0, 0, 0, 180))  # Transparent black
            
            # Display background
            self.screen.blit(notification_bg, (x_pos, y_pos))
            
            # Display title text
            font_title = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 36)
            title_text = font_title.render("New Cards Unlocked!", True, Config.WHITE_COLOR)
            title_rect = title_text.get_rect(centerx=screen_width//2, top=y_pos + 20)
            self.screen.blit(title_text, title_rect)
            
            # Card descriptions based on type and name
            card_descriptions = {
                "Navigation": {
                    "DFS": "Depth-First Search: Explores as far as possible along branches before backtracking.",
                    "BFS": "Breadth-First Search: Explores all neighbors at current depth before moving deeper.",
                    "Dijkstra": "Dijkstra's Algorithm: Finds shortest path using a priority queue based on distance.",
                    "AStar": "A* Search: Uses heuristics to find shortest path more efficiently than Dijkstra.",
                    "RRT": "Rapidly-exploring Random Tree: Efficiently explores large areas by random sampling."
                },
                "Collision avoidance": {
                    "VFH": "Vector Field Histogram: Avoids obstacles using local environment representation.",
                    "Bug": "Bug Algorithm: Simple approach that follows obstacles until path is clear."
                },
                "Recovery": {
                    "SpinInPlace": "Spin In Place: Rotates in place to find a new valid path.",
                    "StepBack": "Step Back: Moves backward to recover from obstacles."
                }
            }
            
            # Display list of unlocked cards with descriptions
            font_card = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
            font_desc = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 16)
            y_offset = 80
            
            for i, card_info in enumerate(self.new_cards):
                card_type = card_info['type']
                card_name = card_info['name']
                
                # Card name with type
                card_text = font_card.render(f"{card_type}: {card_name}", True, Config.WHITE_COLOR)
                card_rect = card_text.get_rect(centerx=screen_width//2, top=y_pos + y_offset)
                self.screen.blit(card_text, card_rect)
                
                # Card description
                if card_type in card_descriptions and card_name in card_descriptions[card_type]:
                    desc_text = font_desc.render(card_descriptions[card_type][card_name], True, (200, 200, 200))
                    desc_rect = desc_text.get_rect(centerx=screen_width//2, top=y_pos + y_offset + 30)
                    self.screen.blit(desc_text, desc_rect)
                    
                y_offset += 70  # Increased spacing between cards
                
            # Display hint
            font_hint = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 18)
            hint_text = font_hint.render("Press SPACE to start new game", True, Config.WHITE_COLOR)
            hint_rect = hint_text.get_rect(centerx=screen_width//2, bottom=y_pos + notification_height - 20)
            self.screen.blit(hint_text, hint_rect)
            
        except Exception as e:
            print(f"Error drawing new cards notification: {e}")
            # Continue without crashing
    
    def update_level_buttons(self):
        """
        Update the state of level change buttons
        """
        try:
            current_level = self.game_state.get_current_level()
            print(f"[GameManager] Updating level buttons for level {current_level}")
            
            # Find buttons from the button list
            left_valid_button = None
            left_invalid_button = None
            right_valid_button = None
            right_invalid_button = None
            
            for button in self.stage.buttons:
                if button.action_name == "prev_level_valid":
                    left_valid_button = button
                elif button.action_name == "prev_level_invalid":
                    left_invalid_button = button
                elif button.action_name == "next_level_valid":
                    right_valid_button = button
                elif button.action_name == "next_level_invalid":
                    right_invalid_button = button
            
            # If at first level, left button will be invalid
            if current_level <= 1:
                if left_valid_button:
                    left_valid_button.set_visible(False)
                if left_invalid_button:
                    left_invalid_button.set_visible(True)
            else:
                if left_valid_button:
                    left_valid_button.set_visible(True)
                if left_invalid_button:
                    left_invalid_button.set_visible(False)
                    
            # Check if can advance to next level
            can_advance = self.game_state.can_advance_to_level(current_level + 1)
            print(f"[GameManager] Can advance to next level: {can_advance}")
            
            # If at last level or cannot advance to next level, right button will be invalid
            if current_level >= 11 or not can_advance:
                if right_valid_button:
                    right_valid_button.set_visible(False)
                if right_invalid_button:
                    right_invalid_button.set_visible(True)
            else:
                if right_valid_button:
                    right_valid_button.set_visible(True)
                if right_invalid_button:
                    right_invalid_button.set_visible(False)
                    
            # Print button visibility status for debugging
            if left_valid_button and right_valid_button:
                print(f"[GameManager] Left button visible: {left_valid_button.is_visible}, Right button visible: {right_valid_button.is_visible}")
                
        except Exception as e:
            print(f"Error updating level buttons: {e}")
            # Continue without crashing
            
    def go_to_previous_level(self):
        """
        Go back to the previous level
        """
        try:
            current_level = self.game_state.get_current_level()
            
            # If already at the first level, do nothing
            if current_level <= 1:
                print("Already at the first level")
                return
                
            # หยุดอัลกอริทึมที่กำลังทำงานอยู่
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                print("[GameManager] Stopping current algorithm due to level change")
                self.current_algorithm.stop()
                self.current_algorithm = None
                
                # หยุดการจับเวลาหากกำลังจับเวลาอยู่
                if self.statistics.is_timing:
                    self.statistics.stop_timer()
                    print("[GameManager] Stopped timer due to level change")
                
                # แสดงข้อความเตือนว่าหุ่นยนต์ถูก reset
                self.__show_reset_warning()
                
            # Reduce level
            self.game_state.current_level -= 1
            new_level = self.game_state.get_current_level()
            print(f"Going back to level {new_level}")
            
            # เก็บสถานะปัจจุบัน
            current_state = self.game_state.get_state()
            
            # Load map for the new level
            self.load_current_level_map()
            
            # รีเซ็ตการ์ดกลับเข้า deck
            self.card_deck.reset_cards()
            print("[GameManager] All cards have been reset to deck")
            
            # รีเซ็ตแผนที่
            self.costmap.reset()
            
            # อัปเดตปุ่มตามสถานะปัจจุบัน
            if current_state == GameStateEnum.PLAYING.value:
                # ถ้าอยู่ในโหมด PLAYING ให้ซ่อนปุ่มทั้งหมด (ยกเว้นปุ่มเลือกด่าน)
                for button in self.stage.buttons:
                    if not hasattr(button, 'is_level_button') or not button.is_level_button:
                        button.set_visible(False)
            else:
                # ถ้าไม่ได้อยู่ในโหมด PLAYING ให้แสดงปุ่มทั้งหมด
                for button in self.stage.buttons:
                    button.set_visible(True)
            
            # อัปเดตปุ่มเลือกด่าน
            self.update_level_buttons()
            
            # คงสถานะเดิมไว้
            self.game_state.change_state(current_state)
            print(f"[GameManager] Maintained state as: {current_state}")
            
        except Exception as e:
            print(f"Error going to previous level: {e}")
            # Continue without crashing
            
    def advance_to_next_level(self):
        """Advance to the next level and unlock new cards"""
        try:
            current_level = self.game_state.get_current_level()
            print(f"[GameManager] Attempting to advance from level {current_level} to level {current_level+1}")
            
            # Check if player can advance to next level
            if not self.game_state.can_advance_to_level(current_level + 1):
                print(f"[GameManager] Cannot advance to level {current_level + 1} yet. Complete level {current_level} first.")
                return False
            
            # หยุดอัลกอริทึมที่กำลังทำงานอยู่
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                print("[GameManager] Stopping current algorithm due to level change")
                self.current_algorithm.stop()
                self.current_algorithm = None
                
                # หยุดการจับเวลาหากกำลังจับเวลาอยู่
                if self.statistics.is_timing:
                    self.statistics.stop_timer()
                    print("[GameManager] Stopped timer due to level change")
                
                # แสดงข้อความเตือนว่าหุ่นยนต์ถูก reset
                self.__show_reset_warning()
                
            # เก็บสถานะปัจจุบัน
            current_state = self.game_state.get_state()
            
            # Mark current level as completed (in case it wasn't already)
            completed = self.game_state.complete_current_level()
            print(f"[GameManager] Marking level {current_level} as completed: {completed}")
            
            # Advance to next level
            next_level = current_level + 1
            
            # Check if there are cards to unlock at this level
            potential_unlocks = self.game_state.level_unlocks.get(next_level, [])
            print(f"[GameManager] Level {next_level} has {len(potential_unlocks)} potential cards to unlock")
            
            # Actually advance the level in game state
            newly_unlocked = self.game_state.advance_level()
            print(f"[GameManager] Advanced to level {next_level}, unlocked {len(newly_unlocked)} new cards")
            
            # Load map for new level
            self.load_current_level_map()
            print(f"[GameManager] Loaded map for level {self.game_state.get_current_level()}")
            
            # If cards were unlocked, show notification and update available cards
            if newly_unlocked:
                # Setup notification data
                self.new_cards = newly_unlocked
                self.new_cards_notification = True
                self.notification_start_time = time.time()
                
                # Log unlocked cards
                print("[GameManager] Unlocked new cards:")
                for card_info in newly_unlocked:
                    print(f"  - {card_info['type']}: {card_info['name']}")
                
                # Update available cards in card deck (critical step)
                cards_added = self.card_deck.update_available_cards()
                if cards_added:
                    print("[GameManager] Successfully added new cards to deck")
                else:
                    print("[GameManager] Warning: No new cards were added to deck")
            else:
                print("[GameManager] No new cards unlocked for this level")
                
            # Save player data after advancing level
            self.player_data.save_player_data(self.game_state.get_username())
            
            # รีเซ็ตการ์ดกลับเข้า deck
            self.card_deck.reset_cards()
            print("[GameManager] All cards have been reset to deck")
            
            # รีเซ็ตแผนที่
            self.costmap.reset()
            
            # อัปเดตปุ่มตามสถานะปัจจุบัน
            if current_state == GameStateEnum.PLAYING.value:
                # ถ้าอยู่ในโหมด PLAYING ให้ซ่อนปุ่มทั้งหมด (ยกเว้นปุ่มเลือกด่าน)
                for button in self.stage.buttons:
                    if not hasattr(button, 'is_level_button') or not button.is_level_button:
                        button.set_visible(False)
            else:
                # ถ้าไม่ได้อยู่ในโหมด PLAYING ให้แสดงปุ่มทั้งหมด
                for button in self.stage.buttons:
                    button.set_visible(True)
            
            # อัปเดตปุ่มเลือกด่าน
            self.update_level_buttons()
            
            # คงสถานะเดิมไว้
            self.game_state.change_state(current_state)
            print(f"[GameManager] Maintained state as: {current_state}")
            
            return True
            
        except Exception as e:
            print(f"[GameManager] Error advancing to next level: {e}")
            # Continue without crashing
            return False
    
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

    def __show_reset_warning(self):
        """แสดงข้อความเตือนว่าหุ่นยนต์ถูก reset"""
        # Create overlay for warning message
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Transparent black background
        self.screen.blit(overlay, (0, 0))
        
        # Create warning message
        warning_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 42)
        title_text = warning_font.render("Operation Interrupted!", True, (255, 50, 50))  # Red for main message
        
        warning_text = warning_font.render("Robot is being reset", True, (255, 255, 0))
        sub_text = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 30).render("Returning to initial position of this map...", True, (255, 255, 255))
        
        # Position and display warning
        title_rect = title_text.get_rect(centerx=self.window_width // 2, centery=self.window_height // 2 - 80)
        warning_rect = warning_text.get_rect(centerx=self.window_width // 2, centery=self.window_height // 2 - 20)
        sub_rect = sub_text.get_rect(centerx=self.window_width // 2, centery=self.window_height // 2 + 40)
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(warning_text, warning_rect)
        self.screen.blit(sub_text, sub_rect)
        pygame.display.flip()
        
        # Pause briefly to make sure user sees the message
        pygame.time.delay(1500)  # 1.5 seconds

    def __check_and_reset_robot_position(self):
        """
        ตรวจสอบว่าหุ่นยนต์อยู่ที่จุดเริ่มต้นหรือไม่
        ถ้าไม่ใช่ ให้รีเซ็ตแมพและตำแหน่งหุ่นยนต์
        """
        try:
            # ตรวจสอบว่า costmap มีการกำหนดตำแหน่งหุ่นยนต์และตำแหน่งเริ่มต้นหรือไม่
            if hasattr(self.costmap, 'robot_pos') and hasattr(self.costmap, 'start_pos') and self.costmap.robot_pos and self.costmap.start_pos:
                # ตรวจสอบว่าตำแหน่งปัจจุบันของหุ่นยนต์ตรงกับตำแหน่งเริ่มต้นหรือไม่
                if self.costmap.robot_pos != self.costmap.start_pos:
                    print(f"[GameManager] Robot not at start position. Resetting map.")
                    print(f"[GameManager] Current: {self.costmap.robot_pos}, Start: {self.costmap.start_pos}")
                    
                    # รีเซ็ตแมพและตำแหน่งหุ่นยนต์
                    self.costmap.reset()
                    
                    # เซ็ตตำแหน่งหุ่นยนต์ไปที่จุดเริ่มต้น
                    if self.costmap.start_pos:
                        start_row, start_col = self.costmap.start_pos
                        self.costmap.set_robot_position(start_row, start_col)
                        print(f"[GameManager] Robot reset to start position: {self.costmap.start_pos}")
        except Exception as e:
            print(f"[GameManager] Error checking/resetting robot position: {e}")
            # Continue without crashing
