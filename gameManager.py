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
        
        # Track if the last click was to place robot (True) or goal (False)
        self.place_robot_mode = True
        
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
        self.timer_rect = pygame.Rect(0, 0, 200, 50)  # Define area for time display
        self.timer_rect.centerx = self.window_width // 2
        self.timer_rect.top = 20
    
    def handle_events(self):
        """
        Handle all game events including:
        - Window events (quit)
        - Mouse movement and clicks
        - Keyboard input
        - Button interactions
        - Card interactions
        """
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
                            
                            # Print debug information
                            print(f"[GameManager] Current level: {self.game_state.get_current_level()}, Highest completed: {self.game_state.highest_completed_level}")
                            print(f"[GameManager] Completion success status: {self.statistics.completion_success}")
                                
                            # If level was completed successfully, ensure next level button is active
                            if self.statistics.completion_success:
                                for button in self.stage.buttons:
                                    if button.action_name == "next_level_valid":
                                        button.set_visible(True)
                                    elif button.action_name == "next_level_invalid":
                                        button.set_visible(False)
                    # เพิ่มปุ่ม N สำหรับเลื่อนไปด่านถัดไป (สำหรับการทดสอบ)
                    elif event.key == pygame.K_n:
                        self.advance_to_next_level()
                except Exception as e:
                    print(f"Error handling key press: {e}")
            
            # Handle button clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    # Send camera position as well
                    button_action = self.stage.handle_button_click(event.pos)
                    if button_action:
                        self.handle_button_action(button_action)
                    else:
                        # Check if click is on costmap
                        mouse_x, mouse_y = event.pos
                        rect_start = (147, -368 + self.camera_y)
                        rect_end = (1054, 87 + self.camera_y)
                        
                        if (rect_start[0] <= mouse_x <= rect_end[0] and 
                            rect_start[1] <= mouse_y <= rect_end[1]):
                            # Convert to costmap coordinates
                            costmap_x = mouse_x - rect_start[0]
                            costmap_y = mouse_y - rect_start[1]
                            
                            # Convert to grid coordinates with safety checks
                            row, col = self.costmap.px_to_grid(costmap_x, costmap_y)
                            
                            # Handle click with current mode
                            success = self.costmap.handle_click(row, col, self.place_robot_mode)
                            
                            if success:
                                if self.place_robot_mode:
                                    print(f"Robot placed at grid position ({row}, {col})")
                                    # Switch to goal placement mode after placing robot
                                    self.place_robot_mode = False
                                    print("Now placing: Goal (red)")
                                else:
                                    print(f"Goal set at grid position ({row}, {col})")
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
        """
        Handle button actions based on the action name.
        
        Args:
            action (str): The name of the action to perform
        """
        try:
            if action == "reset":
                self.reset_game()
            elif action == "start":
                self.start_game()
            elif action == "load_map":
                self.load_map()
            elif action == "place_robot":
                self.place_robot_mode = True
                print("Now placing: Robot (blue)")
            elif action == "place_goal":
                self.place_robot_mode = False
                print("Now placing: Goal (red)")
            elif action == "next_level_valid":
                self.advance_to_next_level()
            elif action == "prev_level_valid":
                self.go_to_previous_level()
        except Exception as e:
            print(f"Error handling button action: {e}")
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
        Reset the game to its initial state.
        
        This includes:
        - Resetting card deck
        - Resetting costmap
        - Recalculating camera position
        - Changing game state
        - Showing UI buttons
        """
        try:
            print("[GameManager] Resetting game...")
            
            # Stop timer and save statistics data
            if self.statistics.is_timing:
                self.statistics.stop_timer()
                self.statistics.set_completion_success(False)  # Set as not successful when resetting
                self.statistics.save_all_data()
            
            # Reset card deck to initial state
            self.card_deck.reset()
            
            # Reset costmap to initial state
            self.costmap.reset()
            
            # Recalculate camera position
            self.target_camera_y = 0
            self.camera_animating = True
            
            # Change game state to CARD_CHOOSING
            self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
            
            # Set state to card selection mode (not gameplay mode)
            self.card_deck.set_game_stage(False)
            
            # Reset to robot placement mode
            self.place_robot_mode = True
            
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
            print("[GameManager] Running algorithm...")
            
            # บันทึกอัลกอริทึมที่ใช้
            algorithm_name, algorithm_type = self.stage.get_selected_algorithm()
            if algorithm_name:
                self.statistics.set_algorithm(algorithm_name, algorithm_type)
            
            # เรียกอัลกอริทึมจาก stage
            result = self.stage.run_algorithm(self.costmap, self.statistics)
            
            if not result:
                print("[GameManager] Failed to start algorithm")
                return
                
            algorithm_class, costmap = result
            
            # สร้างอินสแตนซ์ของอัลกอริทึม
            self.current_algorithm = algorithm_class(costmap)
            
            # เริ่มอัลกอริทึม
            success = self.current_algorithm.start()
            if not success:
                print("[GameManager] Failed to start algorithm")
                self.current_algorithm = None
                return
                
            print("--------------------------------------------")
            print(f"Algorithm {algorithm_name} is running, please wait...")
            print("--------------------------------------------")
            
        except Exception as e:
            print(f"Error running algorithm: {e}")
            # Continue without crashing
    
    def on_algorithm_complete(self, success, path_length=0):
        """
        Callback when algorithm execution is completed
        
        Args:
            success (bool): Whether the algorithm completed successfully
            path_length (int): Length of the path found (if any)
        """
        try:
            print(f"[GameManager] Algorithm completed with success: {success}, path length: {path_length}")
            
            # Stop timer and save statistics
            if self.statistics.is_timing:
                self.statistics.stop_timer()
                self.statistics.set_completion_success(success)
                print(f"[GameManager] Setting completion_success to: {success}")
                self.statistics.save_all_data()
            
            # Mark level as completed if successful
            if success:
                # Record that player has completed this level
                completed = self.game_state.complete_current_level()
                print(f"[GameManager] Level completion status updated: {completed}")
                
                # Save player data
                self.player_data.save_player_data(self.game_state.get_username())
                
                # Update level buttons to show next level as available
                self.update_level_buttons()
            
        except Exception as e:
            print(f"Error in algorithm complete callback: {e}")
            # If error occurs, still set completion status to ensure proper display
            self.statistics.set_completion_success(success)
            
    def update(self):
        """Update the game state."""
        try:
            # ถ้าอยู่ในหน้าล็อกอิน ให้อัพเดตหน้าล็อกอินเท่านั้น
            if self.game_state.get_state() == GameStateEnum.LOGIN.value:
                self.login_screen.update()
                return
                
            # ถ้าอยู่ในโหมด PAUSE ไม่ต้องอัปเดตอะไร
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
                    
                    # ตรวจสอบตำแหน่งกล้องเพื่อกำหนดสถานะเกม
                    if self.camera_y > 0 and self.game_state.get_state() == GameStateEnum.CARD_CHOOSING.value:
                        self.game_state.change_state(GameStateEnum.PLAYING.value)
                    elif self.camera_y <= 0 and self.game_state.get_state() == GameStateEnum.PLAYING.value:
                        self.game_state.change_state(GameStateEnum.CARD_CHOOSING.value)
            
            # Check if algorithm should auto-start
            if self.should_auto_start and time.time() - self.algorithm_start_time >= self.auto_start_delay:
                self.should_auto_start = False
                self.run_algorithm()
                
            # Update game state
            self.game_state.update()
            
            # Update cards
            self.card_deck.update()
            
            # ตรวจสอบว่าหุ่นยนต์ถึงเป้าหมายหรือไม่ (เมื่ออยู่ในโหมด PLAYING)
            if self.game_state.get_state() == GameStateEnum.PLAYING.value and hasattr(self, 'current_algorithm') and self.current_algorithm:
                # ตรวจสอบตำแหน่งหุ่นยนต์และเป้าหมาย
                if self.costmap.robot_pos and self.costmap.goal_pos:
                    robot_row, robot_col = self.costmap.robot_pos
                    goal_row, goal_col = self.costmap.goal_pos
                    
                    # ถ้าหุ่นยนต์อยู่ที่เป้าหมาย หรืออยู่ห่างจากเป้าหมายไม่เกิน 1 ช่อง ให้ถือว่าถึงเป้าหมายแล้ว
                    distance = abs(robot_row - goal_row) + abs(robot_col - goal_col)
                    if distance <= 1:  # Manhattan distance <= 1 (อยู่ติดกัน)
                        print(f"[GameManager] Robot reached goal! Distance: {distance}")
                        
                        # กำหนดว่าอัลกอริทึมสำเร็จ
                        self.current_algorithm.is_completed = True
                        
                        # สร้างเส้นทางถ้ายังไม่มี
                        if not hasattr(self.current_algorithm, 'path') or not self.current_algorithm.path:
                            self.current_algorithm.path = [(robot_row, robot_col)]
                        
                        # เรียกใช้ callback เมื่ออัลกอริทึมทำงานเสร็จสิ้น (สำเร็จ)
                        self.on_algorithm_complete(True, len(self.current_algorithm.path))
                        
                        # เปลี่ยนสถานะเกมเป็น FINISH
                        self.game_state.change_state(GameStateEnum.FINISH.value)
                        
                        # เคลียร์อินสแตนซ์ของอัลกอริทึม
                        self.current_algorithm = None
                        
                        return  # หยุดการอัพเดตเมื่อถึงเป้าหมายแล้ว
            
            # ตรวจสอบเวลาหมดเมื่ออยู่ในโหมด PLAYING
            if self.game_state.get_state() == GameStateEnum.PLAYING.value and self.statistics.is_timing:
                elapsed_time = self.statistics.get_elapsed_time()
                time_limit = self.statistics.get_time_limit()
                
                # ถ้าเวลาเกินกำหนด ให้หยุดเกมและแสดงผลว่าล้มเหลว
                if elapsed_time > time_limit:
                    print(f"[GameManager] Time limit exceeded: {elapsed_time:.2f}/{time_limit} seconds")
                    
                    # หยุดอัลกอริทึมที่กำลังทำงาน
                    if hasattr(self, 'current_algorithm') and self.current_algorithm:
                        self.current_algorithm.stop()
                        self.current_algorithm.is_completed = False
                        
                    # เรียกใช้ callback เมื่ออัลกอริทึมทำงานเสร็จสิ้น (ล้มเหลว)
                    self.on_algorithm_complete(False, 0)
                    
                    # เปลี่ยนสถานะเกมเป็น FINISH
                    self.game_state.change_state(GameStateEnum.FINISH.value)
            
            # อัพเดตสถานะของปุ่มเปลี่ยนด่าน
            self.update_level_buttons()
                
            # Update algorithm if running
            if hasattr(self, 'current_algorithm') and self.current_algorithm:
                still_running = self.current_algorithm.update()
                
                # บันทึกตำแหน่งหุ่นยนต์ถ้ามีการเคลื่อนที่
                if self.costmap.robot_pos:
                    self.statistics.add_robot_position(
                        self.costmap.robot_pos[0], 
                        self.costmap.robot_pos[1]
                    )
                
                if not still_running:
                    print("Algorithm completed or stopped.")
                    
                    # เรียกใช้ callback เมื่ออัลกอริทึมทำงานเสร็จสิ้น
                    success = self.current_algorithm.is_completed
                    path_length = len(self.current_algorithm.path) if hasattr(self.current_algorithm, 'path') else 0
                    self.on_algorithm_complete(success, path_length)
                    
                    self.current_algorithm = None
                    
                    # เมื่ออัลกอริทึมทำงานเสร็จ ให้บันทึกว่าด่านปัจจุบันผ่านแล้ว
                    if success:
                        self.game_state.complete_current_level()
                        
                    # เปลี่ยนสถานะเกมเป็น FINISH
                    self.game_state.change_state(GameStateEnum.FINISH.value)
                    
                    # แสดงปุ่มสำหรับไปด่านถัดไป
                    self.update_level_buttons()
                    
                    # แสดงข้อความว่าผ่านด่านแล้ว
                    if success:
                        print(f"Completed level {self.game_state.get_current_level()}!")
                    
            # อัพเดตการแสดงการ์ดที่ปลดล็อกใหม่
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
                timer_bg = pygame.Surface((200, 45), pygame.SRCALPHA)
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
            notification_width = 500
            notification_height = 300
            
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
            
            # Display list of unlocked cards
            font_card = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
            for i, card_info in enumerate(self.new_cards):
                card_text = font_card.render(f"{card_info['type']}: {card_info['name']}", True, Config.WHITE_COLOR)
                card_rect = card_text.get_rect(centerx=screen_width//2, top=y_pos + 80 + i * 40)
                self.screen.blit(card_text, card_rect)
                
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
            
            # Check if player can advance to next level
            if not self.game_state.can_advance_to_level(current_level + 1):
                print(f"Cannot advance to level {current_level + 1} yet. Complete level {current_level} first.")
                return
            
            # Mark current level as completed
            self.game_state.complete_current_level()
                
            # Advance to next level
            newly_unlocked = self.game_state.advance_level()
            
            # Load map for new level
            self.load_current_level_map()
            
            # Show new level info
            current_level = self.game_state.get_current_level()
            print(f"Advanced to level {current_level}")
            
            # If new cards were unlocked, show notification
            if newly_unlocked:
                self.new_cards = newly_unlocked
                self.new_cards_notification = True
                self.notification_start_time = time.time()
                
                # Show unlocked card info
                print("Unlocked new cards:")
                for card_info in newly_unlocked:
                    print(f"- {card_info['type']}: {card_info['name']}")
                    
                # Update available cards in game
                self.card_deck.update_available_cards()
                
            # Save player data after advancing level
            self.player_data.save_player_data(self.game_state.get_username())
            
            # Reset game after advancing level
            self.reset_game()
            
        except Exception as e:
            print(f"Error advancing to next level: {e}")
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
