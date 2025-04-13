"""
Main module for the card game.
Handles game initialization and main loop.
"""
from gameManager import GameManager

def main():
    """Main function to run the card game."""
    game = GameManager()
    game.run()

if __name__ == "__main__":
    main()


