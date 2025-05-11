# Nav Card

## Project Overview
Nav Card is a 2D strategy game that combines card selection with algorithmic robot navigation. Players select three cards before starting each level: one for navigation, one for obstacle avoidance, and one for recovery behavior. The chosen algorithms determine how the robot navigates through environments with various obstacles and hazards. The goal is to complete levels within a specified number of recovery attempts and/or achieve the best time, with a leaderboard for comparing performance.

For more project details, see the [DESCRIPTION.md](DESCRIPTION.md) file.

## Game Screenshots

### Gameplay View
![Card Selection View](screenshots/gameplay/gameplay.png)

### Fan-out Display Mode
![Fan-out Display Mode](screenshots/gameplay/fanout.png)

### Card Placement View
![Game Stage View](screenshots/gameplay/gameplay2.png)

### Statistics
![Game Stage View](screenshots/data/Data_Visulize.png)

### Statistics
![Game Stage View](screenshots/data/Data_Visulize3.png)

### Statistics
![Game Stage View](screenshots/data/Data_Visulize2.png)

## Game Mechanics
- At the start of each level, players select one card each for navigation, obstacle avoidance, and recovery behavior
- The robot navigates a 2D map filled with both static and movable obstacles according to the chosen algorithms
- Levels are completed by reaching the goal using the minimum number of recoveries and achieving the best time
- When the game starts, all UI buttons disappear for a cleaner interface, with algorithm operations controlled via keyboard

## Game Objectives
- Complete levels within the specified number of recovery attempts
- Beat time records of previous attempts and other players

## Key Features
1. **Algorithm Selection via Cards**: Instead of predefined robot behaviors, players can select and customize algorithm cards, adding strategic depth
2. **Data Analytics Integration**: Detailed tracking of player performance statistics (e.g., movement efficiency, recovery counts) for analysis and in-depth feedback
3. **Dynamic Environments**: Levels feature dynamically changing obstacles, making real-time algorithm adjustments crucial
4. **Interactive Leaderboards**: Players can compare performance metrics globally, encouraging continuous improvement of algorithm strategies
5. **Clean UI Design**: During gameplay, all UI buttons are hidden for an unobstructed view of algorithm operations
6. **Singleton Pattern Usage**: Game state management uses the Singleton pattern to ensure consistent state across all game components
7. **Login System**: Players can create profiles and store progress, including cards unlocked at different levels
8. **Statistics and Analytics System**: Records and analyzes gameplay data to show performance and gameplay trends

## Project Architecture

### UML Class Diagram
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

## Algorithm Cards
The game features a variety of algorithm cards that players can choose from:

### Navigation Algorithms
- **DFS (Depth-First Search)** - Explores as far as possible along a branch before backtracking
- **BFS (Breadth-First Search)** - Explores all paths at equal distance from the starting point
- **A*** - Efficient search algorithm that uses heuristics to find the shortest path
- **Dijkstra** - Classic pathfinding algorithm that guarantees the shortest path
- **RRT (Rapidly-exploring Random Tree)** - Randomized algorithm for efficient space exploration

### Collision Avoidance Algorithms
- **DWA (Dynamic Window Approach)** - Considers robot dynamics for smooth obstacle avoidance
- **VFH (Vector Field Histogram)** - Uses a two-dimensional histogram of obstacles for efficient avoidance
- **BUG** - Simple algorithm that runs in a straight line to the goal and turns when encountering obstacles
- **Wall Following** - Simple algorithm that follows walls to navigate around obstacles

### Recovery Behaviors
- **SpinInPlace** - Spins in place to find a clear path
- **StepBack** - Steps backward before trying another path

## Design Patterns
This game utilizes several design patterns to ensure a clean architecture and maintainable code:

1. **Singleton Pattern**: Used for the GameState class to ensure only one instance throughout the application, maintaining consistent game state management
2. **Observer Pattern**: Used for event handling and user interactions, allowing components to respond to changes in game state

## Statistical Tracking
The game tracks the following metrics during gameplay:
1. **Robot Position Tracking**: Records x-y coordinates and distance traveled over time
2. **Recovery Attempts**: Logs each time a recovery action is executed
3. **Level Completion Time**: Total time taken to complete each level
4. **Player Score/Time Records**: Tracks performance metrics for comparison against leaderboards
5. **Obstacle Interactions**: Records number of collisions or interactions with obstacles

## Installation and Usage
1. Clone or download this repository
2. Install required libraries by running `pip install -r requirements.txt`
3. Start the game by running `python main.py`

## Controls
- **Spacebar**: Toggle card view mode
- **Left Click**: Select and place cards
- **Start Button**: Begin simulation once cards are placed
- **Reset Button**: Reset game state to select cards again
- **ESC**: Pause game/resume playing

## Development
This project was developed using Python and Pygame. The system features a card-based interface for algorithm selection, with a clean UI design that hides UI elements during gameplay for better focus on algorithm operation.

## Copyright and License
The Nav Card project is licensed under the [MIT License](LICENSE). See the [LICENSE](LICENSE) file for more details.

## Version
**Version:** 1.0

## Author
Napat Sirichan (6710545571)