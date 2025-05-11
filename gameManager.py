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
                    # บันทึกตำแหน่งเมาส์เมื่อคลิก (ข้อมูลสำคัญ - level 1)
                    if Config.LOG_MOUSE_POSITION:
                        Config.log("GameManager", f"Mouse clicked", level=2, show_pos=True, mouse_pos=event.pos)
                        
                    # Send camera position as well
                    button_action = self.stage.handle_button_click(event.pos)
                    if button_action:
                        self.handle_button_action(button_action)
                except Exception as e:
                    Config.log("GameManager", f"Error handling button click: {e}", level=1)
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
        # แสดงข้อมูลการคลิกปุ่ม (ข้อมูลสำคัญ - level 1)
        Config.log("GameManager", f"Button clicked: {action}", level=1)
        
        try:
            # Try to perform the action
            if action == "start":
                # Start game with current card configuration
                self.start_game()
                
            elif action == "reset":
                # Reset game
                self.reset_game()
                
            elif action == "stats":
                # Show statistics window
                self.show_statistics()
                
            elif action == "show_message":
                # Show message about stats feature
                self._show_stats_message()
                
            elif action == "next_level":
                # Go to next level
                self.advance_to_next_level()
                
            elif action == "prev_level":
                # Go to previous level
                self.go_to_previous_level()
            
            # After handling button action, update button visibility
            self.update_level_buttons()
            
        except Exception as e:
            print(f"Error handling button action: {e}")
    
    def _show_stats_message(self):
        """Show message about stats feature."""
        try:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
            
            # Create message font
            try:
                font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 36)
            except:
                font = pygame.font.SysFont(None, 36)
            
            # Messages to display
            messages = [
                "คุณสมบัติสถิติยังไม่พร้อมใช้งาน",
                "เกิดปัญหาความไม่เข้ากันระหว่าง TKinter และ PyGame บน macOS",
                "",
                "ข้อมูลสถิติถูกบันทึกไว้ใน โฟลเดอร์ statistics/",
                "",
                "กดปุ่มใดก็ได้เพื่อกลับไปยังเกม"
            ]
            
            # Render and blit each message
            y_offset = self.window_height // 3
            for msg in messages:
                text_surface = font.render(msg, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(self.window_width // 2, y_offset))
                overlay.blit(text_surface, text_rect)
                y_offset += 50
            
            # Blit overlay to screen
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
            
            # Wait for any key press to continue
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        waiting = False
                    elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        waiting = False
                pygame.time.wait(50)
        
        except Exception as e:
            print(f"Error showing stats message: {e}")
            # Continue without crashing
    
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
            
            # Set state to card selection mode (not gameplay mode)
            self.card_deck.set_game_stage(False)
            
            # Show all buttons again, including start and reset buttons
            print("Showing all buttons including start and reset")
            for button in self.stage.buttons:
                button.set_visible(True)
            
            # Stop any running algorithm
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                self.current_algorithm.stop()
                self.current_algorithm = None
                
            # Close new cards notification
            self.new_cards_notification = False
        except Exception as e:
            print(f"Error resetting game: {e}")
            # Continue without crashing
    
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
            
            # Set camera target position to move down half the screen (use positive value)
            self.target_camera_y = self.window_height / 1.8
            self.camera_animating = True
            
            # Hide all game buttons
            for button in self.stage.buttons:
                button.set_visible(False)
            
            # Set timer for auto-starting algorithm after delay
            self.algorithm_start_time = time.time()
            self.should_auto_start = True
            
            # Start timer
            self.statistics.start_timer()
            
            # Show message to user about auto-starting
            print("--------------------------------------------")
            print(f"Game will start automatically in {self.auto_start_delay} seconds")
            print("--------------------------------------------")
        except Exception as e:
            print(f"Error starting game: {e}")
            # Continue without crashing
    
    def run_algorithm(self):
        """Run the selected algorithm."""
        try:
            Config.log("GameManager", "Running algorithm...", level=1)
            
            # บันทึกอัลกอริทึมที่ใช้
            algorithm_name, algorithm_type = self.stage.get_selected_algorithm()
            if algorithm_name:
                self.statistics.set_algorithm(algorithm_name, algorithm_type)
                # แสดงข้อมูลอัลกอริทึมที่เลือกใช้ (ข้อมูลสำคัญ - level 1)
                Config.log("GameManager", f"Selected algorithm: {algorithm_name} ({algorithm_type})", level=1)
            
            # แสดงตำแหน่งปัจจุบันของหุ่นยนต์และเป้าหมาย
            if self.costmap.robot_pos and self.costmap.goal_pos:
                Config.log("GameManager", f"Robot position: {self.costmap.robot_pos}, Goal position: {self.costmap.goal_pos}", level=1)
            
            # เรียกอัลกอริทึมจาก stage
            result = self.stage.run_algorithm(self.costmap, self.statistics)
            
            if not result:
                Config.log("GameManager", "Failed to start algorithm", level=1)
                return
                
            algorithm_class, costmap = result
            
            # สร้างอินสแตนซ์ของอัลกอริทึม
            self.current_algorithm = algorithm_class(costmap)
            
            # เริ่มอัลกอริทึม
            success = self.current_algorithm.start()
            if not success:
                Config.log("GameManager", "Failed to start algorithm", level=1)
                self.current_algorithm = None
                return
                
            Config.log("GameManager", f"Algorithm {algorithm_name} is now running", level=1)
            
        except Exception as e:
            Config.log("GameManager", f"Error running algorithm: {e}", level=1)
            # Continue without crashing
    
    def on_algorithm_complete(self, success, path_length=0):
        """Handle completion of algorithm (robot reached goal or failed)."""
        try:
            # ข้อมูลสรุปผลการทำงานของอัลกอริทึม (ข้อมูลสำคัญ - level 1)
            Config.log("GameManager", f"Algorithm completed with success: {success}, path length: {path_length}", level=1)
            
            # แสดงเวลาที่ใช้ในการทำงาน
            if self.statistics.is_timing:
                elapsed_time = self.statistics.get_elapsed_time()
                time_limit = self.statistics.get_time_limit()
                Config.log("GameManager", f"Time used: {elapsed_time:.2f}/{time_limit} seconds", level=1)
            
            # Stop timer and save statistics
            if self.statistics.is_timing:
                self.statistics.stop_timer()
                self.statistics.set_completion_success(success)
                # ลดระดับความสำคัญของข้อความนี้ลง (level 2)
                Config.log("GameManager", f"Setting completion_success to: {success}", level=2)
                self.statistics.save_all_data()
            
            # Mark level as completed if successful and change state to FINISH
            if success:
                # Record that player has completed this level
                completed = self.game_state.complete_current_level()
                current_level = self.game_state.get_current_level()
                Config.log("GameManager", f"Level {current_level} completed: {completed}", level=1)
                
                # Check if there are new cards to unlock for the next level
                next_level = current_level + 1
                if next_level <= 11:  # Ensure we're not beyond the last level
                    potential_unlocks = self.game_state.level_unlocks.get(next_level, [])
                    if potential_unlocks:
                        # ข้อมูลเกี่ยวกับการปลดล็อคการ์ด (level 2)
                        Config.log("GameManager", f"Potential cards to unlock at level {next_level}: {len(potential_unlocks)}", level=2)
                
                # Save player data
                self.player_data.save_player_data(self.game_state.get_username())
            
            # Change to FINISH state after processing completion
            self.game_state.change_state(GameStateEnum.FINISH.value)
            # แสดงข้อความการเปลี่ยนสถานะเกม (level 2)
            Config.log("GameManager", f"State changed to FINISH. Success: {success}", level=2)
            
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
            Config.log("GameManager", f"Error in algorithm complete callback: {e}", level=1)
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
                    
                    # If robot is at goal or within 1 cell, consider goal reached
                    distance = abs(robot_row - goal_row) + abs(robot_col - goal_col)
                    if distance <= 1:  # Manhattan distance <= 1 (adjacent)
                        print(f"[GameManager] Robot reached goal! Distance: {distance}")
                        
                        # Force algorithm to stop running
                        self.current_algorithm.is_running = False
                        still_running = False
                        
                        # Mark algorithm as completed
                        self.current_algorithm.is_completed = True
                        
                        # Create path if none exists
                        if not hasattr(self.current_algorithm, 'path') or not self.current_algorithm.path:
                            self.current_algorithm.path = [(robot_row, robot_col)]
                
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
            
            # Draw costmap inside the rectangle
            self.costmap.draw(self.screen, rect_start)
            
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
                    # Level buttons should always stay at the top (use camera_offset at the top)
                    if self.camera_y > 0:
                        # When camera moves down, display buttons at the original position
                        original_pos = button.position
                        button.rect.center = (original_pos[0], original_pos[1] + self.camera_y)
                        button.draw(self.screen)
                        button.rect.center = original_pos
                    else:
                        # When camera is at the top, display buttons normally
                        button.draw(self.screen)
                else:
                    # Other buttons display normally
                    button.draw(self.screen)
            
            # Display information only when camera is at the top (camera_y > 0)
            # Do not display information when camera moves down (camera_y <= 0)
            if self.camera_y > 0:
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
            # ใช้ log แทน print และใช้ระดับความสำคัญ 3 (verbose)
            Config.log("GameManager", f"Updating level buttons for level {current_level}", level=3)
            
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
            # แสดงข้อมูลนี้เฉพาะเมื่อมีการเปลี่ยนแปลงหรือเมื่อจำเป็น (level 2)
            Config.log("GameManager", f"Can advance to next level: {can_advance}", level=2)
            
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
                    
            # แสดงข้อมูลนี้เฉพาะสำหรับการ debug (level 3)
            if left_valid_button and right_valid_button:
                Config.log("GameManager", f"Left button visible: {left_valid_button.is_visible}, Right button visible: {right_valid_button.is_visible}", level=3)
                
        except Exception as e:
            # ยังคงแสดงข้อความ error เสมอ (level 1)
            Config.log("GameManager", f"Error updating level buttons: {e}", level=1)
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
                
            # Reduce level
            self.game_state.current_level -= 1
            new_level = self.game_state.get_current_level()
            print(f"Going back to level {new_level}")
            
            # Load map for the new level
            self.load_current_level_map()
            
            # Reset game
            self.reset_game()
            
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
            
            # Update level buttons to reflect the new level
            self.update_level_buttons()
            
            # Reset game for the new level (resets camera, buttons, etc)
            self.reset_game()
            
            return True
            
        except Exception as e:
            print(f"[GameManager] Error advancing to next level: {e}")
            # Continue without crashing
            return False
    
    def show_statistics(self):
        """
        Show statistics window with data visualization.
        
        Creates a Tkinter window with:
        1. Heatmap of robot positions
        2. Line graph of completion time vs attempts
        3. Bar chart of recovery attempts by algorithm
        4. Table of analyzed data
        """
        try:
            print("[GameManager] Showing statistics window...")
            
            # Import necessary libraries
            try:
                import tkinter as tk
                from tkinter import ttk
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                import pandas as pd
                import numpy as np
                from matplotlib.figure import Figure
            except ImportError as e:
                print(f"Error importing required libraries: {e}")
                print("Please make sure you have tkinter, matplotlib, and pandas installed.")
                return
            
            # Create main window
            root = tk.Tk()
            root.title("Nav Card - Statistics")
            root.geometry("1200x800")
            
            # Create a notebook (tabbed interface)
            notebook = ttk.Notebook(root)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Prepare tabs
            heatmap_tab = ttk.Frame(notebook)
            line_graph_tab = ttk.Frame(notebook)
            bar_chart_tab = ttk.Frame(notebook)
            table_tab = ttk.Frame(notebook)
            
            notebook.add(heatmap_tab, text="Robot Positions Heatmap")
            notebook.add(line_graph_tab, text="Time vs Attempts")
            notebook.add(bar_chart_tab, text="Recovery Attempts")
            notebook.add(table_tab, text="Analysis Table")
            
            # Generate data from the statistics module
            heatmap_data = self.statistics.prepare_heatmap_data()
            time_vs_attempts_data = self.statistics.prepare_time_vs_attempts_data()
            recovery_data = self.statistics.prepare_recovery_by_algorithm_data()
            table_data = self.statistics.prepare_user_summary_data()
            
            # 1. Create Heatmap Tab
            if heatmap_data is not None and len(heatmap_data) > 0:
                fig1 = Figure(figsize=(10, 6), dpi=100)
                ax1 = fig1.add_subplot(111)
                
                # Create heatmap from data
                if isinstance(heatmap_data, dict) and 'heatmap' in heatmap_data:
                    heatmap_img = ax1.imshow(heatmap_data['heatmap'], cmap='hot', interpolation='nearest')
                    ax1.set_title('Robot Position Heatmap')
                    ax1.set_xlabel('X Position')
                    ax1.set_ylabel('Y Position')
                    
                    # Add colorbar
                    from mpl_toolkits.axes_grid1 import make_axes_locatable
                    divider = make_axes_locatable(ax1)
                    cax = divider.append_axes("right", size="5%", pad=0.1)
                    fig1.colorbar(heatmap_img, cax=cax, orientation='vertical')
                    
                canvas1 = FigureCanvasTkAgg(fig1, heatmap_tab)
                canvas1.draw()
                canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add explanation label
                explanation = "This heatmap shows where robots most frequently travel or get stuck. \nHotter (brighter) areas indicate higher frequency."
                lbl_explain1 = tk.Label(heatmap_tab, text=explanation, justify="left", anchor="w")
                lbl_explain1.pack(fill=tk.X, padx=10, pady=5)
            else:
                lbl_no_data1 = tk.Label(heatmap_tab, text="Not enough data to generate heatmap", font=("Arial", 14))
                lbl_no_data1.pack(pady=50)
            
            # 2. Create Line Graph Tab
            if time_vs_attempts_data is not None and len(time_vs_attempts_data) > 0:
                fig2 = Figure(figsize=(10, 6), dpi=100)
                ax2 = fig2.add_subplot(111)
                
                # Create line graph from data
                if isinstance(time_vs_attempts_data, dict) and 'x' in time_vs_attempts_data and 'y' in time_vs_attempts_data:
                    ax2.plot(time_vs_attempts_data['x'], time_vs_attempts_data['y'], 'o-', linewidth=2)
                    ax2.set_title('Time to Completion vs. Attempt Number')
                    ax2.set_xlabel('Attempt Number')
                    ax2.set_ylabel('Time to Completion (seconds)')
                    ax2.grid(True)
                    
                canvas2 = FigureCanvasTkAgg(fig2, line_graph_tab)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add explanation label
                explanation = "This graph shows how completion time changes with each attempt, \nillustrating player improvement over time."
                lbl_explain2 = tk.Label(line_graph_tab, text=explanation, justify="left", anchor="w")
                lbl_explain2.pack(fill=tk.X, padx=10, pady=5)
            else:
                lbl_no_data2 = tk.Label(line_graph_tab, text="Not enough data to generate line graph", font=("Arial", 14))
                lbl_no_data2.pack(pady=50)
            
            # 3. Create Bar Chart Tab
            if recovery_data is not None and len(recovery_data) > 0:
                fig3 = Figure(figsize=(10, 6), dpi=100)
                ax3 = fig3.add_subplot(111)
                
                # Create bar chart from data
                if isinstance(recovery_data, dict) and 'algorithms' in recovery_data and 'attempts' in recovery_data:
                    x_pos = np.arange(len(recovery_data['algorithms']))
                    ax3.bar(x_pos, recovery_data['attempts'], align='center', alpha=0.7)
                    ax3.set_xticks(x_pos)
                    ax3.set_xticklabels(recovery_data['algorithms'], rotation=45, ha="right")
                    ax3.set_title('Recovery Attempts by Algorithm Combination')
                    ax3.set_xlabel('Algorithm Combinations')
                    ax3.set_ylabel('Average Recovery Attempts')
                    fig3.tight_layout()
                    
                canvas3 = FigureCanvasTkAgg(fig3, bar_chart_tab)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add explanation label
                explanation = "This chart compares average recovery attempts across different algorithm combinations, \nhelping identify the most effective approaches."
                lbl_explain3 = tk.Label(bar_chart_tab, text=explanation, justify="left", anchor="w")
                lbl_explain3.pack(fill=tk.X, padx=10, pady=5)
            else:
                lbl_no_data3 = tk.Label(bar_chart_tab, text="Not enough data to generate bar chart", font=("Arial", 14))
                lbl_no_data3.pack(pady=50)
            
            # 4. Create Table Tab
            if table_data is not None and len(table_data) > 0:
                # Create a frame for the table
                table_frame = ttk.Frame(table_tab)
                table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Create scrollbars
                v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
                h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
                
                # Create Treeview with scrollbars
                tree = ttk.Treeview(table_frame, selectmode="extended", 
                                    yscrollcommand=v_scrollbar.set,
                                    xscrollcommand=h_scrollbar.set)
                
                v_scrollbar.config(command=tree.yview)
                h_scrollbar.config(command=tree.xview)
                
                # Place scrollbars
                v_scrollbar.pack(side="right", fill="y")
                h_scrollbar.pack(side="bottom", fill="x")
                tree.pack(side="left", fill="both", expand=True)
                
                # Assuming table_data is a pandas DataFrame or has a similar structure
                if hasattr(table_data, 'columns'):
                    # Configure columns
                    tree["columns"] = list(table_data.columns)
                    tree["show"] = "headings"
                    
                    # Set column headings
                    for column in tree["columns"]:
                        tree.heading(column, text=column)
                        tree.column(column, width=100, anchor="center")
                    
                    # Insert data
                    for i, row in table_data.iterrows():
                        tree.insert("", "end", values=list(row))
                else:
                    # Handle if table_data is in another format (e.g., list of dictionaries)
                    # Example for list of dictionaries:
                    if isinstance(table_data, list) and len(table_data) > 0 and isinstance(table_data[0], dict):
                        # Get column names from first row
                        columns = list(table_data[0].keys())
                        
                        # Configure columns
                        tree["columns"] = columns
                        tree["show"] = "headings"
                        
                        # Set column headings
                        for column in columns:
                            tree.heading(column, text=column)
                            tree.column(column, width=100, anchor="center")
                        
                        # Insert data
                        for item in table_data:
                            tree.insert("", "end", values=[item.get(col, "") for col in columns])
                
                # Add explanation label
                explanation = "This table shows analyzed game data across all users, highlighting key performance metrics."
                lbl_explain4 = tk.Label(table_tab, text=explanation, justify="left", anchor="w")
                lbl_explain4.pack(fill=tk.X, padx=10, pady=5)
            else:
                lbl_no_data4 = tk.Label(table_tab, text="Not enough data to generate table", font=("Arial", 14))
                lbl_no_data4.pack(pady=50)
            
            # Run the Tkinter event loop
            root.mainloop()
            
        except Exception as e:
            print(f"Error showing statistics window: {e}")
            # Continue without crashing
    
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
