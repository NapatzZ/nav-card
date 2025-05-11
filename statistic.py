"""
Statistics module for tracking and recording game data.
"""
import os
import csv
import time
from datetime import datetime
import numpy as np
from player_data import PlayerData

class Statistics:
    """
    Class for tracking and recording game statistics.
    
    This class handles:
    - Timing game sessions
    - Recording robot positions
    - Tracking algorithm performance
    - Saving data to CSV files
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Statistics, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize statistics tracking."""
        # Player data
        self.username = ""
        
        # Time data
        self.start_time = 0
        self.end_time = 0
        self.elapsed_time = 0
        self.is_timing = False
        self.time_limit = 300  # เวลาจำกัดเริ่มต้น 5 นาที (300 วินาที)
        
        # Level data
        self.current_level = 0
        self.attempt_count = {}  # {level: count}
        
        # Algorithm data
        self.current_algorithm = ""
        self.algorithm_type = ""
        
        # Robot movement data
        self.robot_positions = []  # [(x, y, timestamp), ...]
        self.robot_stuck_count = 0
        self.recovery_attempts = 0
        
        # Completion data
        self.completion_success = False
        
        # สถานะว่าเป็นผู้เล่นใหม่หรือไม่
        self.is_new_player = True
        
        # Create directory for storing data
        self._ensure_data_directories()
    
    def _ensure_data_directories(self):
        """Create directory for storing data"""
        os.makedirs("statistics", exist_ok=True)
        os.makedirs("statistics/completion", exist_ok=True)
        os.makedirs("statistics/robot_positions", exist_ok=True)
        os.makedirs("statistics/recovery", exist_ok=True)
    
    def set_username(self, username):
        """Set player username"""
        self.username = username
        
        # ตรวจสอบว่าเป็นผู้เล่นใหม่หรือไม่
        player_data = PlayerData()
        self.is_new_player = not player_data.player_exists(username)
    
    def set_level(self, level):
        """Set current level"""
        self.current_level = level
        
        # Add count of playing this level
        if level not in self.attempt_count:
            self.attempt_count[level] = 1
        else:
            self.attempt_count[level] += 1
    
    def set_algorithm(self, algorithm_name, algorithm_type):
        """Set algorithm used"""
        self.current_algorithm = algorithm_name
        self.algorithm_type = algorithm_type
    
    def start_timer(self):
        """Start timer"""
        self.start_time = time.time()
        self.is_timing = True
        
        # Reset data
        self.robot_positions = []
        self.robot_stuck_count = 0
        self.recovery_attempts = 0
        self.completion_success = False
    
    def stop_timer(self, pause=False):
        """
        Stop timer
        
        Args:
            pause (bool): ถ้าเป็น True หมายถึงเป็นการหยุดชั่วคราว ไม่ใช่การสิ้นสุด
        """
        if self.is_timing:
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
            if not pause:
                # เมื่อสิ้นสุดการจับเวลาจริงๆ ให้ตั้งค่า is_timing เป็น False
                self.is_timing = False
            return self.elapsed_time
        return 0
    
    def get_elapsed_time(self):
        """Calculate elapsed time"""
        if self.is_timing:
            return time.time() - self.start_time
        return self.elapsed_time
    
    def format_time(self, seconds):
        """Convert time to MM:SS.ms format"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{minutes:02d}:{int(seconds):02d}.{milliseconds:03d}"
    
    def add_robot_position(self, x, y):
        """Record robot position"""
        if self.is_timing:
            timestamp = time.time() - self.start_time
            self.robot_positions.append((x, y, timestamp))
    
    def increment_stuck_count(self):
        """Increment robot stuck count"""
        self.robot_stuck_count += 1
    
    def increment_recovery_attempts(self):
        """Increment recovery attempts"""
        self.recovery_attempts += 1
    
    def set_completion_success(self, success):
        """Set completion success or failure"""
        self.completion_success = success
    
    def save_completion_data(self):
        """Save completion data to CSV file"""
        # ถ้าไม่ใช่ผู้เล่นใหม่ ไม่ต้องบันทึกข้อมูลใหม่
        if not self.is_new_player:
            print(f"[Statistics] Skipping completion data save for returning player: {self.username}")
            return
            
        filename = "statistics/completion/completion_data.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'timestamp', 'username', 'level', 'attempt', 'algorithm_name', 
                    'algorithm_type', 'time_seconds', 'time_formatted', 'success',
                    'stuck_count', 'recovery_attempts'
                ])
            
            # Write data
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.username,
                self.current_level,
                self.attempt_count.get(self.current_level, 0),
                self.current_algorithm,
                self.algorithm_type,
                round(self.elapsed_time, 3),
                self.format_time(self.elapsed_time),
                int(self.completion_success),
                self.robot_stuck_count,
                self.recovery_attempts
            ])
    
    def save_robot_positions(self):
        """Save robot positions data to CSV file"""
        # ถ้าไม่ใช่ผู้เล่นใหม่ ไม่ต้องบันทึกข้อมูลใหม่
        if not self.is_new_player:
            print(f"[Statistics] Skipping robot positions save for returning player: {self.username}")
            return
            
        if not self.robot_positions:
            return
            
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistics/robot_positions/{self.username}_level{self.current_level}_attempt{self.attempt_count.get(self.current_level, 0)}_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['x', 'y', 'timestamp', 'username', 'level', 'algorithm'])
            
            # Write data
            for x, y, t in self.robot_positions:
                writer.writerow([x, y, round(t, 3), self.username, self.current_level, self.current_algorithm])
    
    def save_recovery_data(self):
        """Save recovery data to CSV file"""
        # ถ้าไม่ใช่ผู้เล่นใหม่ ไม่ต้องบันทึกข้อมูลใหม่
        if not self.is_new_player:
            print(f"[Statistics] Skipping recovery data save for returning player: {self.username}")
            return
            
        if self.recovery_attempts == 0:
            return
            
        filename = "statistics/recovery/recovery_data.csv"
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'timestamp', 'username', 'level', 'algorithm_name', 
                    'algorithm_type', 'recovery_attempts', 'success'
                ])
            
            # Write data
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.username,
                self.current_level,
                self.current_algorithm,
                self.algorithm_type,
                self.recovery_attempts,
                int(self.completion_success)
            ])
    
    def save_all_data(self):
        """Save all data"""
        # แสดงข้อความเกี่ยวกับสถานะผู้เล่น
        if not self.is_new_player:
            print(f"[Statistics] Player {self.username} is a returning player. Statistics will be preserved.")
        else:
            print(f"[Statistics] Player {self.username} is a new player. Saving statistics...")
            
        # Check and create directory if it doesn't exist
        self._ensure_data_directories()
        
        self.save_completion_data()
        self.save_robot_positions()
        self.save_recovery_data()
        
        # Prepare data for visualization (บันทึกไม่ว่าจะเป็นผู้เล่นใหม่หรือเก่า)
        self.prepare_visualization_data()
    
    def prepare_visualization_data(self):
        """Prepare data for Data Visualization"""
        # Create directory for visualization data
        os.makedirs("statistics/visualization", exist_ok=True)
        
        # 1. Create data for Heatmap
        self.prepare_heatmap_data()
        
        # 2. Create data for Time vs Attempts graph
        self.prepare_time_vs_attempts_data()
        
        # 3. Create data for Recovery Attempts by Algorithm graph
        self.prepare_recovery_by_algorithm_data()
        
        # 4. Create summary table for all player data
        self.prepare_user_summary_data()
    
    def prepare_heatmap_data(self):
        """Create data for Heatmap showing robot movement positions"""
        heatmap_file = "statistics/visualization/heatmap_data.csv"
        
        # New file or empty file
        file_exists = os.path.isfile(heatmap_file) and os.path.getsize(heatmap_file) > 0
        
        with open(heatmap_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'x', 'y', 'frequency', 'username', 'level', 'algorithm', 'success'
                ])
            
            # Combine repeated positions and count frequency
            position_freq = {}
            for x, y, _ in self.robot_positions:
                pos = (x, y)
                if pos in position_freq:
                    position_freq[pos] += 1
                else:
                    position_freq[pos] = 1
            
            # Write data to file
            for pos, freq in position_freq.items():
                writer.writerow([
                    pos[0], pos[1], freq, self.username, self.current_level, 
                    self.current_algorithm, int(self.completion_success)
                ])
    
    def prepare_time_vs_attempts_data(self):
        """Create data for graph showing time used vs number of attempts"""
        # Read data from completion_data.csv
        completion_file = "statistics/completion/completion_data.csv"
        time_vs_attempts_file = "statistics/visualization/time_vs_attempts.csv"
        
        if not os.path.isfile(completion_file):
            return
            
        # Prepare data for graph
        data = {}
        
        with open(completion_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['username']
                level = int(row['level'])
                attempt = int(row['attempt'])
                time_seconds = float(row['time_seconds'])
                algorithm = row['algorithm_name']
                
                key = (username, level, algorithm)
                if key not in data:
                    data[key] = []
                
                data[key].append((attempt, time_seconds))
        
        # Write data to new file
        file_exists = os.path.isfile(time_vs_attempts_file)
        
        with open(time_vs_attempts_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'username', 'level', 'algorithm', 'attempt', 'time_seconds'
            ])
            
            # Write data
            for (username, level, algorithm), attempts in data.items():
                for attempt, time_seconds in attempts:
                    writer.writerow([
                        username, level, algorithm, attempt, time_seconds
                    ])
    
    def prepare_recovery_by_algorithm_data(self):
        """Create data for graph showing recovery attempts by algorithm used"""
        recovery_file = "statistics/recovery/recovery_data.csv"
        recovery_by_algorithm_file = "statistics/visualization/recovery_by_algorithm.csv"
        
        if not os.path.isfile(recovery_file):
            return
            
        # Prepare data for graph
        data = {}
        
        with open(recovery_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['username']
                algorithm = row['algorithm_name']
                algorithm_type = row['algorithm_type']
                recovery_attempts = int(row['recovery_attempts'])
                success = int(row['success'])
                
                key = (username, algorithm, algorithm_type)
                if key not in data:
                    data[key] = {
                        'total_attempts': 0,
                        'success_count': 0,
                        'sessions': 0
                    }
                
                data[key]['total_attempts'] += recovery_attempts
                data[key]['success_count'] += success
                data[key]['sessions'] += 1
        
        # Write data to new file
        with open(recovery_by_algorithm_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'username', 'algorithm', 'algorithm_type', 'total_recovery_attempts', 
                'success_rate', 'sessions'
            ])
            
            # Write data
            for (username, algorithm, algorithm_type), stats in data.items():
                success_rate = (stats['success_count'] / stats['sessions']) * 100 if stats['sessions'] > 0 else 0
                
                writer.writerow([
                    username, algorithm, algorithm_type, stats['total_attempts'],
                    round(success_rate, 2), stats['sessions']
                ])
    
    def prepare_user_summary_data(self):
        """Create summary table for all player data"""
        completion_file = "statistics/completion/completion_data.csv"
        user_summary_file = "statistics/visualization/user_summary.csv"
        
        if not os.path.isfile(completion_file):
            return
            
        # Prepare player summary data
        user_data = {}
        
        with open(completion_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['username']
                level = int(row['level'])
                time_seconds = float(row['time_seconds'])
                success = int(row['success'])
                
                if username not in user_data:
                    user_data[username] = {
                        'total_plays': 0,
                        'success_count': 0,
                        'levels_played': set(),
                        'best_times': {},  # { level: best_time }
                        'total_time': 0
                    }
                
                user_data[username]['total_plays'] += 1
                user_data[username]['success_count'] += success
                user_data[username]['levels_played'].add(level)
                user_data[username]['total_time'] += time_seconds
                
                # Record best time for each level
                if success == 1:
                    if level not in user_data[username]['best_times'] or time_seconds < user_data[username]['best_times'][level]:
                        user_data[username]['best_times'][level] = time_seconds
        
        # Write data to new file
        with open(user_summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'username', 'total_plays', 'success_count', 'success_rate', 
                'levels_played', 'average_time', 'best_level_times'
            ])
            
            # Write data
            for username, stats in user_data.items():
                success_rate = (stats['success_count'] / stats['total_plays'] * 100) if stats['total_plays'] > 0 else 0
                average_time = stats['total_time'] / stats['total_plays'] if stats['total_plays'] > 0 else 0
                
                # Combine best times for each level
                best_times_str = "; ".join([f"Level {level}: {self.format_time(time)}" 
                                          for level, time in stats['best_times'].items()])
                
                writer.writerow([
                    username,
                    stats['total_plays'],
                    stats['success_count'],
                    round(success_rate, 2),
                    ",".join(map(str, sorted(stats['levels_played']))),
                    self.format_time(average_time),
                    best_times_str
                ])
    
    def generate_heatmap_data(self):
        """Generate data for Heatmap"""
        if not self.robot_positions:
            return None
            
        # Convert position data to numpy array
        positions = np.array([(x, y) for x, y, _ in self.robot_positions])
        
        return {
            'positions': positions,
            'level': self.current_level,
            'algorithm': self.current_algorithm,
            'username': self.username
        }
    
    def get_completion_time_data(self):
        """Get completion time data for each attempt"""
        filename = "statistics/completion/completion_data.csv"
        
        if not os.path.isfile(filename):
            return {}
            
        data = {}
        
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['username']
                level = int(row['level'])
                attempt = int(row['attempt'])
                time_seconds = float(row['time_seconds'])
                
                if username not in data:
                    data[username] = {}
                
                if level not in data[username]:
                    data[username][level] = []
                
                data[username][level].append((attempt, time_seconds))
        
        return data
    
    def set_time_limit(self, seconds):
        """
        ตั้งค่าเวลาจำกัดสำหรับด่านปัจจุบัน
        
        Args:
            seconds (int): เวลาจำกัดในหน่วยวินาที
        """
        self.time_limit = seconds
        print(f"[Statistics] Set time limit to {seconds} seconds")
        
    def get_time_limit(self):
        """
        รับค่าเวลาจำกัดสำหรับด่านปัจจุบัน
        
        Returns:
            int: เวลาจำกัดในหน่วยวินาที
        """
        return self.time_limit
