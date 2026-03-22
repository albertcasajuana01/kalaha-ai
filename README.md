# Board game assignment - KALAHA AI
This project is a Python-based game application featuring a Graphical User Interface (GUI), game state management, and search-based AI players.

## Project Structure
The project is organized to keep the source code separated from the main execution script:

run.py: The entry point of the application. It configures the environment and launches the interface.
src/: Contains the core logic of the game:
- ui_gui.py: Handles the graphical user interface and the start menu.
- state.py: Defines the game state and board representation.
- rules.py: Contains the game logic and legal move definitions.
- search.py: Implements search algorithms for AI decision-making.
- players.py: Defines different types of players (Human, AI, etc.).
- test_rules.py: Script for verifying game rules and logic.

## How to Run
To start the application, you only need to execute the run.py file located in the root directory. The script automatically handles the internal paths to the src folder.

## Prerequisites
Python 3.x installed on your system.
Ensure all files remain in their respective folders (run.py outside and the rest inside src/).

## Execution Steps
Open your terminal or command prompt.
Navigate to the project's root folder.
Run the following command:
  python run.py
