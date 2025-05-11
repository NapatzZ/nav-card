# Nav Card - Robot Navigation Strategy Game

## Napat Sirichan (6710545571)
**Student ID:** 6710545571  
**GitHub Repository:** [https://github.com/NapatzZ/nav-card](https://github.com/NapatzZ/nav-card)  
**Presentation Video:** [https://youtu.be/UiahhboP96E](https://youtu.be/UiahhboP96E)  
**Project Proposal Document:** [https://docs.google.com/document/d/1mw-oxGlZhXtPc57PVRvUYbVn2kGAJZG0VwvRZMZ3bZ4/edit?usp=sharing](https://docs.google.com/document/d/1mw-oxGlZhXtPc57PVRvUYbVn2kGAJZG0VwvRZMZ3bZ4/edit?usp=sharing)

## ♥︎ Overview and Concept

Nav Card is a 2D strategy game developed with Python and Pygame that combines algorithm card selection with robot navigation. Players choose three cards before starting each level: one card for navigation, one card for obstacle avoidance, and one card for recovery behavior. The selected algorithm set determines how the robot navigates through environments filled with obstacles and hazards.

The Nav Card project presents a unique approach to studying robot navigation algorithms with the following key features:

- **Login System and Progress Tracking:** Players can create profiles and save their progress, including unlocking new algorithm cards as they complete levels.
- **Diverse Card System:** Various navigation algorithms ranging from basic ones like DFS, BFS to advanced ones like A*, RRT.
- **In-depth Data Presentation:** Records and analyzes the performance of each algorithm set, allowing players to understand the strengths and weaknesses of each algorithm.
- **Clean User Interface:** Designed for ease of use, emphasizing clear visualization of algorithm operations. During gameplay, all UI buttons are hidden to maximize display area.

The main concept of Nav Card is to make learning robot navigation algorithms fun and accessible by combining engaging game mechanics with in-depth data analysis.

## 📜 UML Class Diagram

```mermaid
classDiagram
    class GameManager {
        -window_width: int
        -window_height: int
        -screen: Surface
        -game_state: GameState
        -statistics: Statistics
        -player_data: PlayerData
        -login_screen: LoginScreen
        -stage: Stage
        -card_deck: CardDeck
        -costmap: Costmap
        -camera_y: float
        -running: boolean
        +run()
        +update()
        +handle_events()
        +draw()
        +reset_game()
        +start_game()
        +run_algorithm()
        +handle_button_action(action)
        +load_map()
        +load_current_level_map()
    }
    
    class CardDeck {
        -cards: List~Card~
        -placed_cards: dict
        -stage: Stage
        -preview_mode: boolean
        -in_game_stage: boolean
        -game_state: GameState
        +reset()
        +handle_events(events)
        +update()
        +draw(screen, camera_offset)
        +reset_cards()
        +update_available_cards()
        +set_game_stage(is_in_game_stage)
    }
    
    class Card {
        -card_type: string
        -card_name: string
        -position: tuple
        -original_position: tuple
        -image: Surface
        -shadow: Surface
        -dragging: boolean
        -hovering: boolean
        -in_preview: boolean
        -current_area: string
        +draw(surface)
        +update_dragging(mouse_pos)
        +contains_point(point)
        +set_preview_mode(index, total_cards)
        +exit_preview_mode()
        +start_dragging(mouse_pos)
        +stop_dragging(reset_position)
        +update()
    }
    
    class CardType {
        <<enumeration>>
        NAVIGATION
        COLLISION_AVOIDANCE
        RECOVERY_BEHAVIOR
    }
    
    class Stage {
        -slots: List~CardSlot~
        -buttons: List~Button~
        -background: Surface
        +draw(screen, dragging_card, camera_offset)
        +handle_mouse_motion(mouse_pos)
        +handle_button_click(mouse_pos)
        +place_card(card, position, camera_offset)
        +get_slot_at_position(pos)
        +get_selected_algorithm()
        +run_algorithm(costmap, statistics)
    }
    
    class CardSlot {
        -position: tuple
        -card_type: CardType
        -card: Card
        -is_highlighted: boolean
        +draw(surface, camera_offset)
        +can_accept_card(card)
        +place_card(card)
        +remove_card()
    }
    
    class Button {
        -position: tuple
        -image: Surface
        -action_name: string
        -is_visible: boolean
        -is_hovered: boolean
        -is_level_button: boolean
        +draw(screen, camera_offset)
        +check_hover(mouse_pos)
        +is_clicked(mouse_pos)
        +set_visible(visible)
    }
    
    class GameState {
        -current_state: string
        -current_level: int
        -highest_completed_level: int
        -unlocked_cards: dict
        -username: string
        -_instance: GameState$
        +change_state(new_state)
        +get_state()
        +advance_level()
        +get_unlocked_cards()
        +get_current_level()
        +set_username(username)
        +get_username()
    }
    
    class GameStateEnum {
        <<enumeration>>
        LOGIN
        CARD_CHOOSING
        PLAYING
        FINISH
        PAUSE
    }
    
    class Statistics {
        -username: string
        -start_time: float
        -end_time: float
        -elapsed_time: float
        -current_level: int
        -robot_positions: List~tuple~
        -recovery_attempts: int
        -completion_success: boolean
        -_instance: Statistics$
        +set_username(username)
        +set_level(level)
        +start_timer()
        +stop_timer(pause)
        +add_robot_position(x, y)
        +increment_recovery_attempts()
        +save_completion_data()
        +save_robot_positions()
        +save_recovery_data()
        +save_all_data()
    }
    
    class LoginScreen {
        -window_width: int
        -window_height: int
        -username_input: TextInput
        -login_button: Button
        -is_returning_player: boolean
        +handle_events(events)
        +draw(screen)
        +get_username()
    }
    
    class PlayerData {
        -data_folder: string
        +save_player_data(username, data)
        +load_player_data(username)
        +player_exists(username)
        +get_all_players()
    }
    
    class Costmap {
        -rect_width: int
        -rect_height: int
        -resolution: int
        -grid: array
        -start_pos: tuple
        -goal_pos: tuple
        +set_obstacle(x, y, value)
        +get_value(x, y)
        +draw(surface)
        +load_from_pgm(file_path)
        +set_start_position(x, y)
        +set_goal_position(x, y)
    }
    
    GameManager --> Stage : manages
    GameManager --> CardDeck : contains
    GameManager --> GameState : uses
    GameManager --> Statistics : uses
    GameManager --> PlayerData : uses
    GameManager --> LoginScreen : contains
    GameManager --> Costmap : contains
    
    Stage --> CardSlot : contains
    Stage --> Button : contains
    
    CardDeck --> Card : contains
    CardDeck --> GameState : uses
    
    CardSlot --> Card : can hold
    CardSlot --> CardType : accepts type
    
    Card ..> CardType : has type
    
    Statistics ..> PlayerData : uses
    
    GameState ..> GameStateEnum : uses
    
    note for GameState "Uses Singleton Pattern"
    note for Statistics "Uses Singleton Pattern"
```

## 🔑 Key Features

- **User Account System:** Create accounts and store individual player progress
- **Algorithm Card System:** Select three types of cards to control robot behavior
- **Multiple Difficulty Levels:** Each level presents different challenges
- **Algorithm Card Unlocking:** Players receive new cards as they complete levels
- **Fan-out Card Display Mode:** Display all cards in a fan layout for easy selection
- **Robot Path Visualization:** View the path the robot takes based on the selected algorithms
- **Recovery System:** Manage situations when the robot gets stuck or can't find a path
- **Detailed Statistics Collection:** Record and analyze the performance of each algorithm
- **Collected Data Visualization:** Display statistics through easy-to-understand tables and graphs
- **Clean User Interface:** During gameplay, all UI buttons are hidden to focus on algorithm operation
- **Singleton Pattern Implementation:** Game state and statistics management use the Singleton pattern to ensure consistent data across the application

## 🧮 User Interface

### Card Selection View
![Card Selection View](screenshots/gameplay/normal_stage.png)

### Fan-out Display Mode
![Fan-out Display Mode](screenshots/gameplay/fanout.png)

### Game Stage View
![Game Stage View](screenshots/gameplay/slice_up.png)

## 📊 Data Analysis

Nav Card helps players understand the performance of various algorithms through collection and analysis of multi-dimensional data:

### Collected Data:
1. **Robot Positions:** Records x-y coordinates and time throughout the game
2. **Recovery Data:** Records points where recovery was needed and the type of recovery used
3. **Mission Time:** Tracks time taken to complete each level
4. **Attempts and Success:** Records number of attempts and successes for each level
5. **Algorithm Performance:** Compares performance of different algorithm sets

### Analysis and Visualization:
- **Recovery Heat Maps:** Shows where robots frequently get stuck on maps
- **Algorithm Comparison Graphs:** Compares time and efficiency of different algorithms
- **Progress Charts:** Shows player development and learning over time

## 📡 Core Technologies
- Python 3.8+
- Pygame 2.0.1+
- NumPy (for calculations and data management)
- JSON (for user data storage)
- CSV (for game statistics recording)

## 🖥️ Installation
1. Make sure you have Python 3.8 or newer installed on your system
2. Install required Python packages: `pip install -r requirements.txt`

## 🧑‍💻 Starting the Game
1. Navigate to the project directory in your terminal
2. Start the game using the command: `python main.py`

## Controls
- **Spacebar**: Toggle card view mode
- **Left Click**: Select and place cards
- **Start Button**: Begin simulation when cards are placed
- **Reset Button**: Reset game state to choose cards again
- **ESC**: Pause game/resume play

## Developed by
Napat Sirichan (6710545571)

## Version
**Version:** 1.0