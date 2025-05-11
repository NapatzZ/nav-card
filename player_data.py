"""
Player Data module for storing and retrieving player progress.
"""
import os
import json
import pickle
from state import GameState

class PlayerData:
    """
    Class for managing player data and progress.
    
    This class handles:
    - Saving player progress
    - Loading player progress
    - Checking if player exists
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlayerData, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize player data manager."""
        self.players_directory = "data/players"
        self.ensure_directory_exists()
        
    def ensure_directory_exists(self):
        """Create directory for storing player data."""
        os.makedirs(self.players_directory, exist_ok=True)
        
    def get_player_file_path(self, username):
        """
        Get the file path for a player's data.
        
        Args:
            username (str): The player's username
            
        Returns:
            str: Path to the player's data file
        """
        # Make sure username is safe for filenames
        safe_username = "".join(c for c in username if c.isalnum() or c in " _-")
        return os.path.join(self.players_directory, f"{safe_username}.json")
        
    def player_exists(self, username):
        """
        Check if a player exists.
        
        Args:
            username (str): The player's username
            
        Returns:
            bool: True if player exists, False otherwise
        """
        player_file = self.get_player_file_path(username)
        return os.path.exists(player_file)
        
    def save_player_data(self, username):
        """
        Save player data to file.
        
        Args:
            username (str): The player's username
        """
        try:
            # Get the game state instance
            game_state = GameState()
            
            # Create data dictionary
            player_data = {
                "username": username,
                "current_level": game_state.current_level,
                "highest_completed_level": game_state.highest_completed_level,
                "unlocked_cards": game_state.unlocked_cards
            }
            
            # Save to file
            player_file = self.get_player_file_path(username)
            with open(player_file, 'w', encoding='utf-8') as f:
                json.dump(player_data, f, indent=4)
                
            print(f"[PlayerData] Saved player data for {username}")
            return True
        except Exception as e:
            print(f"[PlayerData] Error saving player data: {e}")
            return False
        
    def load_player_data(self, username):
        """
        Load player data from file.
        
        Args:
            username (str): The player's username
            
        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        try:
            player_file = self.get_player_file_path(username)
            
            if not os.path.exists(player_file):
                print(f"[PlayerData] No data found for player {username}")
                return False
                
            with open(player_file, 'r', encoding='utf-8') as f:
                player_data = json.load(f)
            
            # ตรวจสอบว่าข้อมูลมีครบทุกฟิลด์
            required_fields = ["username", "current_level", "highest_completed_level", "unlocked_cards"]
            for field in required_fields:
                if field not in player_data:
                    print(f"[PlayerData] Warning: Missing field '{field}' in player data")
                    # กำหนดค่าเริ่มต้น
                    if field == "username":
                        player_data[field] = username
                    elif field == "current_level":
                        player_data[field] = 1
                    elif field == "highest_completed_level":
                        player_data[field] = 0
                    elif field == "unlocked_cards":
                        player_data[field] = {
                            "Navigation": ["DFS"],
                            "Collision avoidance": [],
                            "Recovery": []
                        }
            
            # Get the game state instance
            game_state = GameState()
            
            # Restore data to game state
            game_state.current_level = player_data["current_level"]
            game_state.highest_completed_level = player_data["highest_completed_level"]
            game_state.unlocked_cards = player_data["unlocked_cards"]
            
            print(f"[PlayerData] Loaded player data for {username}")
            print(f"  Level: {game_state.current_level}")
            print(f"  Highest completed level: {game_state.highest_completed_level}")
            
            # แสดงรายละเอียดการ์ดที่ปลดล็อกทั้งหมด
            print(f"  Unlocked cards details:")
            for card_type, cards in game_state.unlocked_cards.items():
                print(f"    {card_type}: {cards}")
            
            return True
        except Exception as e:
            print(f"[PlayerData] Error loading player data: {e}")
            return False
            
    def get_all_players(self):
        """
        Get a list of all players.
        
        Returns:
            list: List of player usernames
        """
        try:
            self.ensure_directory_exists()
            players = []
            
            for filename in os.listdir(self.players_directory):
                if filename.endswith(".json"):
                    players.append(filename[:-5])  # Remove .json extension
                    
            return players
        except Exception as e:
            print(f"[PlayerData] Error getting player list: {e}")
            return [] 