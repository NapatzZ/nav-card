"""
Visualization module for displaying statistics.

This module provides a visualization interface for game statistics using pygame.
It includes visualizations for:
- Heatmap of robot positions
- Line graph of completion time vs attempts
- Bar chart of recovery attempts by algorithm
"""
import os
import pygame
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Must be set before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
import sys

class StatisticsVisualization:
    """Class for displaying statistical visualizations."""
    
    def __init__(self, screen_width, screen_height):
        """
        Initialize visualization display.
        
        Args:
            screen_width (int): Width of the pygame window
            screen_height (int): Height of the pygame window
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_viz = None  # 'heatmap', 'line_graph', 'bar_chart', or 'data_table'
        
        # Font setup
        self.title_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 36)
        self.button_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
        self.info_font = pygame.font.Font("font/PixelifySans-Regular.ttf", 18)
        self.table_font = pygame.font.Font("font/PixelifySans-Regular.ttf", 16)
        
        # Create buttons
        button_width = 160
        button_height = 50
        button_margin = 15
        total_width = (button_width * 4) + (button_margin * 3)
        start_x = (screen_width - total_width) // 2
        
        self.buttons = {
            'heatmap': pygame.Rect(start_x, 50, button_width, button_height),
            'line_graph': pygame.Rect(start_x + button_width + button_margin, 50, button_width, button_height),
            'bar_chart': pygame.Rect(start_x + (button_width + button_margin) * 2, 50, button_width, button_height),
            'data_table': pygame.Rect(start_x + (button_width + button_margin) * 3, 50, button_width, button_height)
        }
        
        # Close button
        self.close_button = pygame.Rect(50, 50, 120, 50)
        
        # Graph display area
        self.graph_area = pygame.Rect(50, 120, screen_width - 100, screen_height - 170)
        
        # Cache for graph surfaces
        self.graph_surfaces = {
            'heatmap': None,
            'line_graph': None, 
            'bar_chart': None,
            'data_table': None
        }
        
        # Map selector for heatmap
        self.map_selector = {
            'visible': False,
            'current_map': 1,
            'buttons': {},
            'max_maps': 11
        }
        
        # Init map selector buttons
        self.create_map_selector_buttons()
        
        # Load data for all graphs
        self.load_data()
        
        # Processed data for data table
        self.processed_data = None
    
    def create_map_selector_buttons(self):
        """Create map selection buttons for heatmap view."""
        button_width = 40
        button_height = 40
        button_margin = 10
        total_width = min(700, (button_width + button_margin) * self.map_selector['max_maps'])
        start_x = (self.screen_width - total_width) // 2
        
        # Create map selector buttons 1-11
        for i in range(1, self.map_selector['max_maps'] + 1):
            x_pos = start_x + (i-1) * (button_width + button_margin)
            self.map_selector['buttons'][i] = pygame.Rect(x_pos, 90, button_width, button_height)
    
    def load_data(self):
        """Load data from CSV files."""
        # Check if files exist
        self.data = {
            'heatmap': None,
            'time_vs_attempts': None,
            'recovery_by_algorithm': None
        }
        
        # Load Heatmap data
        heatmap_file = "statistics/visualization/heatmap_data.csv"
        if os.path.exists(heatmap_file):
            try:
                self.data['heatmap'] = pd.read_csv(heatmap_file)
            except Exception as e:
                print(f"Error loading heatmap data: {e}")
        
        # Load Time vs Attempts data
        time_file = "statistics/visualization/time_vs_attempts.csv"
        if os.path.exists(time_file):
            try:
                self.data['time_vs_attempts'] = pd.read_csv(time_file)
            except Exception as e:
                print(f"Error loading time vs attempts data: {e}")
        
        # Load Recovery Attempts data
        recovery_file = "statistics/visualization/recovery_by_algorithm.csv"
        if os.path.exists(recovery_file):
            try:
                self.data['recovery_by_algorithm'] = pd.read_csv(recovery_file)
            except Exception as e:
                print(f"Error loading recovery data: {e}")
    
    def handle_events(self, events):
        """
        Handle events for the visualization screen.
        
        Args:
            events (list): List of pygame events
            
        Returns:
            bool: True if user wants to exit visualization, False otherwise
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check button clicks
                if self.close_button.collidepoint(mouse_pos):
                    # Just return True to signal we want to exit this window
                    # but don't call pygame.quit() which would close the whole game
                    return True
                
                # Check visualization type buttons
                for viz_type, button in self.buttons.items():
                    if button.collidepoint(mouse_pos):
                        self.current_viz = viz_type
                        # Show map selector only for heatmap
                        self.map_selector['visible'] = (viz_type == 'heatmap')
                        # Reset cached surface
                        self.graph_surfaces[viz_type] = None
                        self.generate_visualization(viz_type)
                        break
                
                # Check map selector buttons if visible and in heatmap view
                if self.map_selector['visible'] and self.current_viz == 'heatmap':
                    for map_num, button in self.map_selector['buttons'].items():
                        if button.collidepoint(mouse_pos):
                            if map_num != self.map_selector['current_map']:
                                self.map_selector['current_map'] = map_num
                                # Reset cached heatmap to regenerate for new map
                                self.graph_surfaces['heatmap'] = None
                                self.generate_visualization('heatmap')
                            break
        
        return False  # Stay in visualization screen
    
    def generate_visualization(self, viz_type):
        """
        Generate a visualization and cache it.
        
        Args:
            viz_type (str): Type of visualization ('heatmap', 'line_graph', 'bar_chart', or 'data_table')
        """
        # Check if we need to regenerate
        if self.graph_surfaces[viz_type] is not None:
            return  # Use cached graph
            
        if viz_type == 'heatmap':
            self.graph_surfaces[viz_type] = self.generate_heatmap()
        elif viz_type == 'line_graph':
            self.graph_surfaces[viz_type] = self.generate_line_graph()
        elif viz_type == 'bar_chart':
            self.graph_surfaces[viz_type] = self.generate_bar_chart()
        elif viz_type == 'data_table':
            self.graph_surfaces[viz_type] = self.generate_data_table()
    
    def generate_heatmap(self):
        """Generate heatmap showing robot position data for the selected map."""
        if self.data['heatmap'] is None or len(self.data['heatmap']) == 0:
            return self.create_empty_graph("No data available for heatmap")
        
        # Filter data for the selected map level
        selected_map = self.map_selector['current_map']
        filtered_data = self.data['heatmap'][self.data['heatmap']['level'] == selected_map]
        
        if len(filtered_data) == 0:
            return self.create_empty_graph(f"No data available for Map {selected_map}")
        
        # Create large figure with high resolution
        plt.figure(figsize=(10, 8), dpi=100)
        plt.title(f'Robot Position Heatmap - Map {selected_map}', fontsize=20)
        
        # Get x, y positions and frequency
        x = filtered_data['x']
        y = filtered_data['y']
        frequency = filtered_data['frequency']
        
        # Use hexbin plot instead of regular heatmap
        plt.hexbin(x, y, C=frequency, gridsize=20, cmap='inferno', alpha=0.8)
        plt.colorbar(label='Frequency')
        
        # Invert y-axis to match game coordinate system
        plt.gca().invert_yaxis()
        
        # Add labels
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.grid(alpha=0.3)
        
        # Set appropriate aspect ratio
        plt.tight_layout()
        
        # Convert to pygame surface
        return self.plt_to_surface()
    
    def generate_line_graph(self):
        """Generate line graph showing relationship between completion time and attempts."""
        if self.data['time_vs_attempts'] is None or len(self.data['time_vs_attempts']) == 0:
            return self.create_empty_graph("No data available for Time vs Attempts graph")
        
        plt.figure(figsize=(10, 8), dpi=100)
        plt.title('Completion Time vs Attempts', fontsize=20)
        
        df = self.data['time_vs_attempts']
        
        # Group data by player, level, and algorithm
        groups = df.groupby(['username', 'level', 'algorithm'])
        
        # Create different colors for each group
        colors = plt.cm.tab10.colors
        color_idx = 0
        
        for name, group in groups:
            username, level, algorithm = name
            label = f"{username} (Level {level}, {algorithm})"
            
            # Sort data by attempt number
            group = group.sort_values('attempt')
            
            plt.plot(group['attempt'], group['time_seconds'], 
                    marker='o', linestyle='-', 
                    color=colors[color_idx % len(colors)],
                    label=label)
            
            color_idx += 1
        
        plt.xlabel('Attempt Number')
        plt.ylabel('Time (seconds)')
        plt.grid(True, alpha=0.3)
        
        # Add horizontal line at average
        avg_time = df['time_seconds'].mean()
        plt.axhline(y=avg_time, color='r', linestyle='--', alpha=0.6, 
                   label=f'Average ({avg_time:.2f} seconds)')
        
        # Limit legend size if too many groups
        if len(groups) > 5:
            plt.legend(loc='upper right', fontsize='small', ncol=2)
        else:
            plt.legend(loc='upper right')
        
        plt.tight_layout()
        
        return self.plt_to_surface()
    
    def generate_bar_chart(self):
        """Generate bar chart showing recovery attempts by algorithm."""
        if self.data['recovery_by_algorithm'] is None or len(self.data['recovery_by_algorithm']) == 0:
            return self.create_empty_graph("No data available for Recovery graph")
        
        plt.figure(figsize=(10, 8), dpi=100)
        plt.title('Recovery Attempts by Algorithm', fontsize=20)
        
        df = self.data['recovery_by_algorithm']
        
        # Set colors
        colors = plt.cm.Paired.colors
        
        # Get unique algorithm types
        algorithm_types = df['algorithm_type'].unique()
        
        # Data for bar chart
        x = np.arange(len(df))
        width = 0.7  # Bar width
        
        # Create bar chart
        bars = plt.bar(x, df['total_recovery_attempts'], width, 
                     color=[colors[i % len(colors)] for i in range(len(df))])
        
        # Add axis labels
        plt.xlabel('Algorithm')
        plt.ylabel('Recovery Attempts')
        
        # Add algorithm names on x-axis
        labels = [f"{row.algorithm}\n({row.algorithm_type})" for idx, row in df.iterrows()]
        plt.xticks(x, labels, rotation=45, ha='right')
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}',
                    ha='center', va='bottom', rotation=0)
        
        # Add success rate information
        for i, (idx, row) in enumerate(df.iterrows()):
            success_rate = row['success_rate']
            plt.text(i, bars[i].get_height() + 1.5,
                    f'Success Rate: {success_rate:.1f}%',
                    ha='center', va='bottom', rotation=0)
        
        plt.tight_layout()
        
        return self.plt_to_surface()
    
    def generate_data_table(self):
        """Generate a data table showing processed statistics."""
        # Process the data
        data = self.process_data()
        
        if not data:
            return self.create_empty_graph("No data available for analysis")
        
        # Create surface to draw the table
        surface = pygame.Surface((self.graph_area.width, self.graph_area.height))
        surface.fill((255, 255, 255))  # White background
        
        # Define table colors
        header_color = (50, 100, 150)  # Blue for headers
        row_colors = [(240, 240, 255), (255, 255, 255)]  # Alternating row colors
        text_color = (0, 0, 0)  # Black text
        border_color = (200, 200, 200)  # Light gray borders
        
        # Draw title
        title_font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 24)
        title = title_font.render("Game Statistics Analysis", True, (0, 0, 100))
        title_rect = title.get_rect(center=(surface.get_width()//2, 30))
        surface.blit(title, title_rect)
        
        # Setup table position and dimensions
        margin = 20
        y_pos = 70
        max_width = surface.get_width() - (margin * 2)
        
        # Draw completion stats section
        self.draw_section_header(surface, "Completion Statistics", margin, y_pos)
        y_pos += 35
        
        # Format completion stats table
        if 'completion_stats' in data:
            stats = data['completion_stats']
            rows = []
            
            if 'total_sessions' in stats:
                rows.append(["Total Game Sessions", f"{stats['total_sessions']}"])
            
            if 'overall_success_rate' in stats:
                success_rate = stats['overall_success_rate']
                if isinstance(success_rate, (int, float)):
                    rows.append(["Overall Success Rate", f"{success_rate:.1f}%"])
                else:
                    rows.append(["Overall Success Rate", str(success_rate)])
            
            # Draw table
            y_pos = self.draw_table(surface, ["Metric", "Value"], rows, margin, y_pos, max_width//2)
            y_pos += 20
        
        # Time distribution section
        if 'time_distribution' in data:
            self.draw_section_header(surface, "Time Distribution", margin, y_pos)
            y_pos += 35
            
            times = data['time_distribution']
            rows = []
            
            # Basic stats
            if 'mean' in times:
                rows.append(["Average Time", f"{times['mean']:.2f}s"])
            if 'median' in times:
                rows.append(["Median Time", f"{times['median']:.2f}s"])
            if 'min' in times and 'max' in times:
                rows.append(["Time Range", f"{times['min']:.2f}s - {times['max']:.2f}s"])
            
            # Draw basic time stats
            y_pos = self.draw_table(surface, ["Metric", "Value"], rows, margin, y_pos, max_width//2)
            y_pos += 20
            
            # Player percentage by time brackets
            if 'brackets' in times:
                bracket_rows = []
                
                for label, data in times['brackets'].items():
                    if 'percentage' in data:
                        bracket_rows.append([label, f"{data['count']} players", f"{data['percentage']:.1f}%"])
                
                # Draw time brackets table
                if bracket_rows:
                    y_pos = self.draw_table(surface, ["Time Bracket", "Count", "Percentage"], bracket_rows, margin, y_pos, max_width)
                    y_pos += 20
        
        # Level success rates
        if 'success_rate_by_level' in data and data['success_rate_by_level']:
            self.draw_section_header(surface, "Success Rate by Level", margin, y_pos)
            y_pos += 35
            
            level_rows = []
            level_data = data['success_rate_by_level']
            
            for level in sorted(level_data.keys()):
                level_info = level_data[level]
                if 'success_rate' in level_info and 'total_attempts' in level_info:
                    level_rows.append([
                        f"Level {level}",
                        f"{level_info['total_attempts']}",
                        f"{level_info['success_rate']:.1f}%"
                    ])
            
            # Draw level success table
            if level_rows:
                y_pos = self.draw_table(surface, ["Level", "Attempts", "Success Rate"], level_rows, margin, y_pos, max_width)
                y_pos += 20
        
        # Algorithm performance
        if 'algorithm_usage' in data and data['algorithm_usage']:
            self.draw_section_header(surface, "Algorithm Performance", margin, y_pos)
            y_pos += 35
            
            alg_rows = []
            for alg_name, info in data['algorithm_usage'].items():
                if 'success_rate' in info:
                    alg_rows.append([
                        alg_name,
                        f"{info['success_rate']:.1f}%",
                        f"{info['recovery_attempts']}" if 'recovery_attempts' in info else "N/A"
                    ])
            
            # Draw algorithm table
            if alg_rows:
                y_pos = self.draw_table(surface, ["Algorithm", "Success Rate", "Recovery Attempts"], alg_rows, margin, y_pos, max_width)
                y_pos += 20
        
        # Player performance comparison (if multiple players)
        if 'player_performance' in data and len(data['player_performance']) > 1:
            self.draw_section_header(surface, "Player Performance Comparison", margin, y_pos)
            y_pos += 35
            
            player_rows = []
            for player, stats in data['player_performance'].items():
                player_rows.append([
                    player,
                    f"{stats['average_time']:.2f}s" if 'average_time' in stats else "N/A",
                    f"{stats['best_time']:.2f}s" if 'best_time' in stats else "N/A",
                    f"{stats['levels_played']}" if 'levels_played' in stats else "N/A"
                ])
            
            # Sort by average time
            player_rows.sort(key=lambda x: float(x[1].replace("s", "")) if x[1] != "N/A" else float('inf'))
            
            # Draw player table
            if player_rows:
                y_pos = self.draw_table(surface, ["Player", "Avg Time", "Best Time", "Levels"], player_rows, margin, y_pos, max_width)
        
        return surface
    
    def process_data(self):
        """Process raw data into meaningful statistics for data table."""
        if self.processed_data is not None:
            return self.processed_data
            
        # Initialize processed data
        processed_data = {
            'completion_stats': {},
            'algorithm_usage': {},
            'time_distribution': {},
            'success_rate_by_level': {},
            'player_performance': {}
        }
        
        # Check if we have completion data
        if self.data['time_vs_attempts'] is not None and len(self.data['time_vs_attempts']) > 0:
            df = self.data['time_vs_attempts']
            
            # Total game sessions
            total_sessions = len(df)
            processed_data['completion_stats']['total_sessions'] = total_sessions
            
            # Success rate overall
            if 'success' in df.columns:
                success_rate = (df['success'].sum() / total_sessions) * 100
                processed_data['completion_stats']['overall_success_rate'] = success_rate
            else:
                # Try to get from completion data
                comp_file = "statistics/completion/completion_data.csv"
                if os.path.exists(comp_file):
                    try:
                        comp_df = pd.read_csv(comp_file)
                        if 'success' in comp_df.columns:
                            success_rate = (comp_df['success'].sum() / len(comp_df)) * 100
                            processed_data['completion_stats']['overall_success_rate'] = success_rate
                    except:
                        processed_data['completion_stats']['overall_success_rate'] = "N/A"
            
            # Time distribution
            if 'time_seconds' in df.columns:
                times = df['time_seconds']
                processed_data['time_distribution'] = {
                    'mean': times.mean(),
                    'median': times.median(),
                    'min': times.min(),
                    'max': times.max(),
                    'std': times.std()
                }
                
                # Calculate percentiles of completion time
                processed_data['time_distribution']['percentiles'] = {
                    '25%': times.quantile(0.25),
                    '50%': times.quantile(0.50),
                    '75%': times.quantile(0.75),
                    '90%': times.quantile(0.90)
                }
                
                # Calculate percentage of players completing in time brackets
                time_brackets = [
                    (0, 30, "< 30s"),
                    (30, 60, "30s-1m"),
                    (60, 120, "1m-2m"),
                    (120, 300, "2m-5m"),
                    (300, float('inf'), "> 5m")
                ]
                
                brackets_data = {}
                for start, end, label in time_brackets:
                    count = ((times >= start) & (times < end)).sum()
                    percentage = (count / len(times)) * 100
                    brackets_data[label] = {
                        'count': count,
                        'percentage': percentage
                    }
                
                processed_data['time_distribution']['brackets'] = brackets_data
            
            # Level success rates
            if 'level' in df.columns and 'success' in df.columns:
                level_groups = df.groupby('level')
                level_success = {}
                
                for level, group in level_groups:
                    total = len(group)
                    if 'success' in group.columns:
                        successes = group['success'].sum()
                        rate = (successes / total) * 100 if total > 0 else 0
                    else:
                        rate = 0
                    
                    level_success[int(level)] = {
                        'total_attempts': total,
                        'success_rate': rate
                    }
                
                processed_data['success_rate_by_level'] = level_success
        
        # Algorithm usage and performance
        if self.data['recovery_by_algorithm'] is not None and len(self.data['recovery_by_algorithm']) > 0:
            alg_df = self.data['recovery_by_algorithm']
            
            alg_usage = {}
            for idx, row in alg_df.iterrows():
                alg_name = row['algorithm']
                alg_type = row['algorithm_type']
                success_rate = row['success_rate']
                recovery_attempts = row['total_recovery_attempts']
                
                alg_usage[f"{alg_name} ({alg_type})"] = {
                    'success_rate': success_rate,
                    'recovery_attempts': recovery_attempts
                }
            
            processed_data['algorithm_usage'] = alg_usage
        
        # Player performance comparison
        if self.data['time_vs_attempts'] is not None and 'username' in self.data['time_vs_attempts'].columns:
            player_df = self.data['time_vs_attempts']
            player_groups = player_df.groupby('username')
            
            player_stats = {}
            for player, group in player_groups:
                if 'time_seconds' in group.columns:
                    avg_time = group['time_seconds'].mean()
                    best_time = group['time_seconds'].min()
                    levels_played = len(group['level'].unique())
                    attempts = len(group)
                    
                    player_stats[player] = {
                        'average_time': avg_time,
                        'best_time': best_time,
                        'levels_played': levels_played,
                        'attempts': attempts
                    }
            
            processed_data['player_performance'] = player_stats
        
        self.processed_data = processed_data
        return processed_data
        
    def draw_section_header(self, surface, text, x, y):
        """Draw a section header on the table."""
        font = pygame.font.Font("font/PixelifySans-SemiBold.ttf", 20)
        header = font.render(text, True, (50, 50, 100))
        surface.blit(header, (x, y))
        
        # Draw line under header
        pygame.draw.line(surface, (100, 100, 150), 
                         (x, y + 25), 
                         (x + header.get_width() + 50, y + 25), 2)
    
    def draw_table(self, surface, headers, rows, x, y, width):
        """
        Draw a table on the surface.
        
        Args:
            surface: Surface to draw on
            headers: List of column headers
            rows: List of rows, each row is a list of cell values
            x, y: Top-left position of table
            width: Maximum width of table
            
        Returns:
            New y position after the table
        """
        if not rows:
            return y
            
        # Constants
        padding = 10
        row_height = 30
        header_color = (50, 100, 150)
        header_text_color = (255, 255, 255)
        row_colors = [(240, 240, 255), (255, 255, 255)]
        text_color = (0, 0, 0)
        border_color = (200, 200, 200)
        
        # Determine column widths
        num_cols = len(headers)
        col_width = width // num_cols
        
        # Draw headers
        for i, header in enumerate(headers):
            # Draw header background
            header_rect = pygame.Rect(x + (i * col_width), y, col_width, row_height)
            pygame.draw.rect(surface, header_color, header_rect)
            pygame.draw.rect(surface, border_color, header_rect, 1)  # Border
            
            # Draw header text
            text_surf = self.table_font.render(header, True, header_text_color)
            text_rect = text_surf.get_rect(center=header_rect.center)
            surface.blit(text_surf, text_rect)
        
        # Draw rows
        for row_idx, row in enumerate(rows):
            row_color = row_colors[row_idx % len(row_colors)]
            row_y = y + row_height + (row_idx * row_height)
            
            for col_idx, cell in enumerate(row):
                # Check if we're still within bounds
                if row_y + row_height > surface.get_height():
                    # We've reached the bottom of the available space
                    return row_y
                    
                # Draw cell background
                cell_rect = pygame.Rect(x + (col_idx * col_width), row_y, col_width, row_height)
                pygame.draw.rect(surface, row_color, cell_rect)
                pygame.draw.rect(surface, border_color, cell_rect, 1)  # Border
                
                # Draw cell text
                text_surf = self.table_font.render(str(cell), True, text_color)
                text_rect = text_surf.get_rect(center=cell_rect.center)
                surface.blit(text_surf, text_rect)
        
        # Return the new y position
        return y + row_height + (len(rows) * row_height)
    
    def plt_to_surface(self):
        """Convert matplotlib figure to pygame Surface."""
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        
        # Load image from buffer as pygame Surface
        graph_img = pygame.image.load(buf)
        buf.close()
        
        return graph_img
    
    def create_empty_graph(self, message):
        """Create an empty graph with a message."""
        # Create empty surface
        surface = pygame.Surface((self.graph_area.width, self.graph_area.height))
        surface.fill((240, 240, 240))  # Light gray background
        
        # Create message
        font = pygame.font.Font("font/PixelifySans-Regular.ttf", 24)
        text = font.render(message, True, (100, 100, 100))
        text_rect = text.get_rect(center=(surface.get_width()//2, surface.get_height()//2))
        
        surface.blit(text, text_rect)
        
        return surface
    
    def draw(self, screen):
        """
        Draw the visualization screen.
        
        Args:
            screen (pygame.Surface): The main display surface
        """
        # Draw background
        screen.fill((255, 255, 255))
        
        # Draw all buttons
        button_colors = {
            'heatmap': (50, 168, 82),  # Green
            'line_graph': (66, 135, 245),  # Blue
            'bar_chart': (219, 68, 55),   # Red
            'data_table': (148, 59, 173)   # Purple
        }
        
        button_texts = {
            'heatmap': "Heatmap",
            'line_graph': "Line Graph",
            'bar_chart': "Bar Chart",
            'data_table': "Data Table"
        }
        
        # Draw close button
        pygame.draw.rect(screen, (150, 150, 150), self.close_button)
        close_text = self.button_font.render("Close", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=self.close_button.center)
        screen.blit(close_text, close_text_rect)
        
        # Draw visualization buttons
        for viz_type, button in self.buttons.items():
            # Select color based on button selection
            color = button_colors[viz_type]
            if viz_type == self.current_viz:
                # Make selected button brighter
                color = tuple(min(c + 30, 255) for c in color)
                pygame.draw.rect(screen, color, button)
                pygame.draw.rect(screen, (255, 255, 255), button, 3)  # White border
            else:
                pygame.draw.rect(screen, color, button)
            
            # Draw button text
            text = self.button_font.render(button_texts[viz_type], True, (255, 255, 255))
            text_rect = text.get_rect(center=button.center)
            screen.blit(text, text_rect)
        
        # Draw map selector buttons if visible and in heatmap view
        if self.map_selector['visible'] and self.current_viz == 'heatmap':
            for map_num, button in self.map_selector['buttons'].items():
                # Highlight selected map
                if map_num == self.map_selector['current_map']:
                    pygame.draw.rect(screen, (50, 168, 82), button)  # Bright green for selected
                    pygame.draw.rect(screen, (255, 255, 255), button, 2)  # White border
                else:
                    pygame.draw.rect(screen, (100, 100, 100), button)  # Gray for others
                
                # Draw map number
                map_text = pygame.font.Font("font/PixelifySans-Regular.ttf", 18).render(
                    str(map_num), True, (255, 255, 255))
                map_text_rect = map_text.get_rect(center=button.center)
                screen.blit(map_text, map_text_rect)
        
        # Draw graph area
        pygame.draw.rect(screen, (240, 240, 240), self.graph_area)
        
        # If visualization is selected, display that graph
        if self.current_viz and self.graph_surfaces[self.current_viz]:
            # Scale graph to fit area
            graph = self.graph_surfaces[self.current_viz]
            
            # Calculate position to center graph
            scale_factor = min(
                self.graph_area.width / graph.get_width(),
                self.graph_area.height / graph.get_height()
            )
            
            scaled_width = int(graph.get_width() * scale_factor)
            scaled_height = int(graph.get_height() * scale_factor)
            
            # Scale graph
            scaled_graph = pygame.transform.smoothscale(graph, (scaled_width, scaled_height))
            
            # Calculate center position
            graph_x = self.graph_area.x + (self.graph_area.width - scaled_width) // 2
            graph_y = self.graph_area.y + (self.graph_area.height - scaled_height) // 2
            
            # Draw graph
            screen.blit(scaled_graph, (graph_x, graph_y))
        elif self.current_viz:
            # If visualization selected but no graph, generate it
            self.generate_visualization(self.current_viz)
        else:
            # If no visualization selected, show prompt
            welcome_text = self.title_font.render("Please select a graph type above", True, (50, 50, 50))
            welcome_rect = welcome_text.get_rect(center=(
                self.graph_area.x + self.graph_area.width // 2,
                self.graph_area.y + self.graph_area.height // 2
            ))
            screen.blit(welcome_text, welcome_rect)

# Function to open visualization in separate window
def open_visualization(screen_width, screen_height):
    """
    Open visualization statistics in a separate window
    
    Args:
        screen_width (int): Width of the screen
        screen_height (int): Height of the screen
    """
    pygame.init()
    
    # Create new window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Statistics Visualization")
    
    # Create visualizer
    viz = StatisticsVisualization(screen_width, screen_height)
    
    # Set default viz to heatmap
    viz.current_viz = 'heatmap'
    viz.map_selector['visible'] = True
    viz.generate_visualization('heatmap')
    
    # Display loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                
        # Send events to visualizer
        if viz.handle_events(events):
            running = False
        
        # Draw screen
        viz.draw(screen)
        pygame.display.flip()
        clock.tick(30)
    
    # Return to main game by recreating the game window with the same dimensions
    # This ensures we don't disrupt the game's pygame instance
    pygame.display.set_mode((screen_width, screen_height)) 