# Nav Card

## Project Overview
Nav Card is a 2D strategy game that combines card selection with algorithm-driven robot navigation. Players choose three algorithm cards before starting each stage: one for navigation, one for collision avoidance, and one for recovery behavior. The selected algorithms dictate how the in-game robot navigates a dynamic environment filled with obstacles and hazards. The goal is to complete the stage within a set limit of recovery attempts and/or by beating the best time, with leaderboards to compare performances.

For a more detailed project description, check out our [DESCRIPTION.md](DESCRIPTION.md) file.

## Game Screenshots

### Card Selection View
![Card Selection View](screenshots/gameplay/normal_stage.png)

### Fan-out Display Mode
![Fan-out Display Mode](screenshots/gameplay/fanout.png)

### Game Stage View
![Game Stage View](screenshots/gameplay/slice_up.png)

## Game Mechanics
- At the start of each stage, players select one card each for navigation, collision avoidance, and recovery behavior.
- The robot navigates a 2D map filled with static and dynamic obstacles based on the selected algorithms.
- The stage is completed by reaching the goal while minimizing recovery attempts and finishing within the best possible time.
- Once the game starts, all UI buttons disappear to provide a cleaner interface, with algorithm execution handled via keyboard controls.

## Game Objectives
- Complete stages within a predefined recovery limit.
- Beat the record times of previous attempts and other players.

## Key Features
1. **Card-Based Algorithm Selection**: Instead of preset robot behaviors, players choose and tweak algorithm cards, adding strategic depth.
2. **Data Analytics Integration**: Detailed statistical tracking of player performance (e.g., movement efficiency, recovery attempts) allows for in-depth analysis and feedback.
3. **Dynamic Environments**: Levels feature dynamically changing obstacles, making real-time algorithm adjustments critical.
4. **Interactive Leaderboards**: Players can compare performance metrics globally, encouraging continual optimization of their algorithm strategies.
5. **Clean UI Design**: During gameplay, all UI buttons are hidden to provide an unobstructed view of the algorithm execution.
6. **Singleton Pattern Implementation**: Game state management utilizes the Singleton design pattern to ensure consistent state across all game components.

## Project Architecture

### UML Class Diagram
```mermaid
classDiagram
    class GameManager {
        -stage: Stage
        -card_deck: CardDeck
        -game_state: GameState
        -camera_y: float
        -running: boolean
        +run()
        +update()
        +handle_events()
        +draw()
        +reset_game()
        +start_game()
        +run_algorithm()
    }
    
    class CardDeck {
        -cards: List~Card~
        -preview_mode: boolean
        -game_stage: boolean
        +reset_cards()
        +handle_events()
        +update()
        +draw()
        +set_game_stage()
        +toggle_preview_mode()
    }
    
    class Card {
        -card_type: string
        -card_name: string
        -position: tuple
        -dragging: boolean
        -hovering: boolean
        -in_preview: boolean
        +draw()
        +update_dragging()
        +contains_point()
        +set_preview_mode()
        +start_dragging()
        +stop_dragging()
    }
    
    class CardType {
        <<enumeration>>
        NAVIGATION
        COLLISION_AVOIDANCE
        RECOVERY
    }
    
    class Stage {
        -slots: List~CardSlot~
        -buttons: List~Button~
        -background: Surface
        +draw()
        +handle_mouse_motion()
        +place_card()
        +handle_button_click()
        +get_slot_at_position()
    }
    
    class CardSlot {
        -position: tuple
        -card_type: CardType
        -card: Card
        +draw()
        +can_accept_card()
        +place_card()
        +remove_card()
    }
    
    class Button {
        -position: tuple
        -image: Surface
        -action_name: string
        -is_visible: boolean
        +draw()
        +check_hover()
        +is_clicked()
        +set_visible()
    }
    
    class GameState {
        -current_state: string
        -_instance: GameState
        +get_instance()
        +update()
        +change_state()
    }
    
    GameManager --> Stage : manages
    GameManager --> CardDeck : contains
    GameManager --> GameState : tracks
    
    Stage --> CardSlot : contains
    Stage --> Button : contains
    
    CardDeck --> Card : contains
    
    CardSlot --> Card : can hold
    CardSlot --> CardType : accepts type
    
    Card ..> CardType : has type
```

## Algorithm Cards
The game includes various algorithm cards that players can choose from:

### Navigation Algorithms
- **A*** - An efficient pathfinding algorithm that uses heuristics to find the shortest path
- **Dijkstra** - A classic pathfinding algorithm that guarantees the shortest path
- **RRT (Rapidly-exploring Random Tree)** - A randomized algorithm for efficient space exploration
- **Greedy Search** - A fast but potentially suboptimal pathfinding approach

### Collision Avoidance Algorithms
- **DWA (Dynamic Window Approach)** - Considers robot dynamics for smooth obstacle avoidance
- **Wall Following** - A simple algorithm that follows walls to navigate around obstacles

### Recovery Behaviors
- Various strategies for recovering from stuck situations or collisions

## Design Patterns
The game implements several design patterns to ensure clean architecture and maintainable code:

1. **Singleton Pattern**: Used for the GameState class to ensure only one instance exists throughout the application, maintaining a consistent game state.
2. **Observer Pattern**: Used for event handling and user interactions, allowing different components to react to changes in the game state.

## Statistical Data Tracking
The game tracks the following features during gameplay:
1. **Robot Position Tracking**: Records x-y coordinates and the distance traveled over time.
2. **Recovery Attempts**: Records each time a recovery maneuver is executed.
3. **Stage Completion Time**: Total time taken to finish each stage.
4. **Player Score/Time Records**: Tracking performance metrics to compare against leaderboards.
5. **Obstacle Interactions**: Records collision counts or interactions with obstacles.

## Installation and Usage
1. Clone or download this repository
2. Install the required libraries by running `pip install -r requirements.txt`
3. Start the game by running `python main.py`

## Controls
- **Spacebar**: Toggle card view mode
- **Left Click**: Select and place cards
- **Start Button**: Begin the simulation once cards are placed
- **Reset Button**: Reset the game state to select cards again
- **'o' Key**: Run the algorithm after the game has started
- **'r' Key**: Switch to robot placement mode
- **'g' Key**: Switch to goal placement mode

## Development
This project is developed using Python and Pygame. The system features a card-based interface for algorithm selection, with a clean UI design that hides UI elements during gameplay for better focus on algorithm execution.

## Current Version
This is version 0.75 of the project, representing 75% completion of the planned features. Recent additions include implementing the Singleton pattern for game state management and improving the UI by hiding buttons during gameplay.
