# ★ LarpSnake

**A fast terminal snake with warp zones, multiple levels and bonus orbs.**

Made by [artiknite](https://github.com/artiknite)

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## About

LarpSnake is a classic snake game that lives entirely in your terminal.  
Cross the edges of the map and you reappear on the opposite side.  
Collect red orbs for points, and watch out for the rare golden orbs that give double score.

Simple, colorful, and surprisingly addictive.

## Features

- **Warp edges** — go through the border, appear on the other side
- **5 unique levels** with different wall layouts
- **Bonus orbs** — rarer, bigger, give 2× points
- High scores saved per level
- Clean colorful interface
- Works on Windows, Linux and macOS

### Levels

| # | Name     | Description                     |
|---|----------|---------------------------------|
| 1 | Classic  | Empty field — pure skill        |
| 2 | Borders  | Walls on every edge             |
| 3 | Cross    | Big cross with open center      |
| 4 | Boxes    | Four boxes in the corners       |
| 5 | Maze     | Labyrinth with passages         |

## Controls

| Key           | Action              |
|---------------|---------------------|
| Arrows / WASD | Move                |
| P             | Pause               |
| Q             | Back to menu / Quit |
| R             | Retry               |
| M             | Return to menu      |

## Run from source

### Windows

```powershell
pip install windows-curses
python snake.py
```

### Linux / macOS

```bash
python3 snake.py
```

## Build executable

### Windows

Run `build_windows.bat` or:

```powershell
pip install windows-curses pyinstaller
pyinstaller --onefile --name larpsnake snake.py
```

### Linux / macOS

```bash
pip install pyinstaller
pyinstaller --onefile --name larpsnake snake.py
```

## License

MIT
