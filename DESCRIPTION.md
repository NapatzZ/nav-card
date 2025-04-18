# Nav Card - Robot Navigation Strategy Game

## 1. Project Overview
Nav Card is a 2D strategy game that combines card selection with algorithm-driven robot navigation. Players choose three algorithm cards before starting each stage: one for navigation, one for collision avoidance, and one for recovery behavior. The selected algorithms dictate how the in-game robot navigates a dynamic environment filled with obstacles and hazards. The goal is to complete the stage within a set limit of recovery attempts and/or by beating the best time, with leaderboards to compare performances.

## 2. Project Review
Most robot navigation simulations are designed for technical users and lack the accessibility needed for beginners to understand how different algorithms work. This project aims to:
- **Enhance Learning**: By visualizing how different navigation algorithms perform in real-time
- **Increase Interactivity**: By allowing players to experiment with different algorithm combinations
- **Improve Understanding**: Through a card-based interface that makes complex algorithmic concepts more approachable

## 3. Programming Development

### 3.1 Game Concept
The game simulates robot navigation through obstacle-filled environments. The primary objective is to reach the goal position with minimal recovery attempts and in the shortest time possible. The game integrates traditional navigation algorithms with a card-based selection system to make learning these concepts fun and interactive.

### 3.2 Object-Oriented Programming Implementation
The project is structured into separate components:

**Game Manager**:
- **Role**: Manages overall game flow (board state, user input, turn switching, and statistics tracking)
- **Key Attributes**:
  - `stage`: Current level the player is attempting
  - `camera_y`: Controls the view between card selection and gameplay areas
  - `running`: Tracks if the game is currently active
- **Key Methods**: `run()`, `update()`, `handle_events()`, and `draw()`

**Card Deck**:
- **Role**: Handles the collection of algorithm cards and their interactions
- **Key Attributes**:
  - `cards`: List of available algorithm cards
  - `preview_mode`: Tracks whether cards are displayed in fan-out view
  - `game_stage`: Indicates whether gameplay has started (vs. card selection phase)
- **Key Methods**: `reset_cards()`, `handle_events()`, `update()`, and `draw()`

**Card (Base Class)**:
- **Role**: Defines common attributes and methods for algorithm cards
- **Key Attributes**:
  - `card_type`: Type of algorithm (Navigation, Collision avoidance, Recovery)
  - `card_name`: Specific algorithm name (e.g., A*, DWA)
  - `position`: Current position on screen
  - `dragging`: Whether the card is being dragged
- **Key Methods**: `draw()`, `update_dragging()`, `contains_point()`, `set_preview_mode()`

**Stage**:
- **Role**: Manages the playfield area, card slots, and game environment
- **Key Attributes**:
  - `slots`: Card placement slots for the three algorithm types
  - `buttons`: Interactive buttons (start, reset)
  - `background`: Game environment background
- **Key Methods**: `draw()`, `handle_mouse_motion()`, `place_card()`, `handle_button_click()`

**UML Diagram**:
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
        +draw()
        +check_hover()
        +is_clicked()
    }
    
    class GameState {
        -current_state: string
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

### 3.3 Algorithms Involved
- **Move Validation**: Checking if a card can be placed in a specific slot based on card type
- **Card Visualization**: Displaying cards in a fan-out pattern when in preview mode
- **Camera Animation**: Smooth transition between card selection screen and gameplay area
- **Event Handling**: Managing user inputs (mouse clicks, drags) and updating the game state
- **Data Logging**: Recording gameplay metrics (algorithm choices, completion time, etc.) for future analysis

## 4. Statistical Data (Prop Stats)

### 4.1 Data Features
The game will record:
- Robot Path Length per Stage
- Number of Recovery Attempts
- Completion Time per Stage
- Algorithm Combinations Used
- Obstacle Collision Frequency

### 4.2 Data Recording and Analysis
**Storage**:
- Data will be stored in JSON format for easy access and manipulation

**Analysis**:
- Basic statistical measures (mean, minimum, maximum, and standard deviation) will be calculated
- Performance comparisons between different algorithm combinations

### 4.3 Data Analysis Report
**Table Presentation**:
"Algorithm Performance Comparison" will be summarized in a table showing:
- Algorithm Combination
- Average Completion Time
- Average Recovery Attempts
- Success Rate

**Graph Presentation**:
Three graphs will be generated:

1. **Robot Path Efficiency**:
   - Graph Type: Line chart (attempt number vs. path length)
   - Shows improvement over multiple attempts

2. **Algorithm Combination Performance**:
   - Graph Type: Bar chart (algorithm combinations vs. completion time)
   - Compares effectiveness of different algorithm sets

3. **Recovery Attempt Distribution**:
   - Graph Type: Heatmap overlaid on stage map
   - Shows locations where recovery events frequently occur

## 5. Project Timeline

| Week | Task |
|------|------|
| Week 1 (March) | Proposal submission / Project initiation |
| Week 2 | Design system architecture, create UML diagram |
| Week 3 | Develop core classes (GameManager, Card, CardDeck) |
| Week 4 | Implement card selection interface and preview mode |
| Week 5 | Create stage environment and robot navigation display |
| Week 6 (by April 16) | Complete card placement system and camera transitions |
| Weeks 7-8 | Develop data collection framework and visualization |
| Final Week | Polish user interface, finalize documentation |

## 6. Document Version
Version: 4.0

## 7. Statistical Data Revision

### 7.1 Table Presentation
We focus on "Algorithm Performance" with:
- Success Rate: Percentage of successful stage completions
- Average Completion Time: Mean time to reach goal position
- Average Recovery Count: Mean number of recovery events triggered
- Path Efficiency: Path length vs. optimal path length

### 7.2 Graph Presentation

| Feature Name | Graph Objective | Graph Type | X-axis | Y-axis |
|--------------|----------------|------------|--------|--------|
| Algorithm Performance | Compare effectiveness of algorithms | Bar chart | Algorithm Combination | Average Completion Time |
| Recovery Attempts | Show recovery frequency by location | Heatmap | X Position | Y Position |
| Path Efficiency | Track improvement over time | Line graph | Attempt Number | Path Length Ratio |


## GitHub Repository
https://github.com/NapatzZ/nav-card 
