# 2048: Expanded - An Enhanced Version of the Classic Game

---

## Overview

**2048: Expanded** is an enhanced version of the classic 2048 game, developed during the first year of my university course for an end of year project. This project aims to build upon the original 2048 game by adding new features and functionalities. The enhancements include a leaderboard to track high scores and save/load functionality for game states. This project was a valuable learning experience in game development and software engineering, providing insights into user interaction, data management, UI design, and the use of libraries.

2048 was originaly created in 2014 by [Gabriele Cirulli](https://github.com/gabrielecirulli/2048)[^1]. The game can be played online at [play2048.co](https://play2048.co/)[^2]

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Customization](#customization)
5. [License](#license)
6. [References](#references)

---

## Features

- **Leaderboard**:
  - `leaderboard.csv`: Tracks and displays the top 5 scores with player names and highest tile values.

- **Score Tracking**:
  - Real-time display of current score and highest tile value during gameplay.

- **Game Controls**:
  - `W`, `A`, `S`, `D`: Move tiles up, left, down, and right.
  - Arrow keys to move tiles
  - `F5`: Activates a "boss key" to hide the game window quickly.
  - `F6`: Activates a "cheat key" to manipulate game settings.

- **Save/Load Functionality**:
  - Save your game progress and load previous game states using unique usernames.

- **User Authentication**:
  - Manage user accounts with secure login and password features.

---

## Installation

To use this library, you will need Python 3.6 and the following Python packages:
- `numpy`
- `tkinter`

You can install these dependencies using pip:
```sh
pip install numpy tkinter
```

You can run the game using:
```sh
python 2048.py
```

---

## Usage

**Playing the Game**:
- Use the arrow keys or `W`, `A`, `S`, `D` to move tiles in the corresponding directions.
- Combine tiles of the same value by moving them into each other to create larger tiles and increase your score.

**Managing Scores**:
- View the top scores and player names on the leaderboard, accessible from the game’s main menu.

**Saving and Loading**:
- **Save Game**: To save your current game progress, use the save feature available in the game’s menu. You will be prompted to enter a username under which your progress will be saved.
- **Load Game**: To load a previously saved game, select the load feature from the game’s menu and enter the username associated with the saved game.

**Special Features**:
- **Boss Key**: Press `F5` to quickly hide the game window. This feature is useful if you need to discreetly exit or hide the game.
- **Cheat Key**: Press `F6` to open a cheat menu that allows you to manipulate game settings, such as adjusting tile values or modifying game rules.

---
## License
---

Feel free to contribute to this project by submitting issues or pull requests. For any questions or further information, please contact the project maintainer.

---

**Notice**: You are free to use, modify, and distribute this code as needed. The author of this project is Lewis Murphy, @defalt0402. If you have any questions or need further clarification, please reach out!
---

## References

[^1]: [2048 Game](https://play2048.co/): Play the classic 2048 game online.
[^2]: [Gabriele Cirulli's GitHub](https://github.com/gabrielecirulli/2048): Original repository for the 2048 game.
