#!/usr/bin/env python3
"""
LarpSnake — terminal snake with warp zones & levels
by artiknite
"""

import curses
import random
import time
import os
import sys
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)


@dataclass
class Point:
    y: int
    x: int

    def __add__(self, other: Tuple[int, int]) -> "Point":
        return Point(self.y + other[0], self.x + other[1])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Point):
            return False
        return self.y == other.y and self.x == other.x

    def __hash__(self) -> int:
        return hash((self.y, self.x))


def create_levels(height: int, width: int) -> List[dict]:
    levels = []

    levels.append({
        "name": "Classic",
        "description": "Empty field — pure skill",
        "walls": set(),
    })

    walls = set()
    for x in range(width):
        walls.add(Point(0, x))
        walls.add(Point(height - 1, x))
    for y in range(height):
        walls.add(Point(y, 0))
        walls.add(Point(y, width - 1))
    levels.append({
        "name": "Borders",
        "description": "Walls on every edge",
        "walls": walls,
    })

    walls = set()
    mid_y, mid_x = height // 2, width // 2
    for y in range(height):
        walls.add(Point(y, mid_x))
    for x in range(width):
        walls.add(Point(mid_y, x))
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            walls.discard(Point(mid_y + dy, mid_x + dx))
    for dx in range(-6, 7):
        walls.discard(Point(mid_y, mid_x + dx))
    for dy in range(-6, 7):
        walls.discard(Point(mid_y + dy, mid_x))
    levels.append({
        "name": "Cross",
        "description": "Big cross with open center",
        "walls": walls,
    })

    walls = set()
    box_size = 4
    positions = [
        (3, 5),
        (3, width - 5 - box_size),
        (height - 3 - box_size, 5),
        (height - 3 - box_size, width - 5 - box_size),
    ]
    for by, bx in positions:
        for y in range(by, by + box_size):
            for x in range(bx, bx + box_size):
                if y == by or y == by + box_size - 1 or x == bx or x == bx + box_size - 1:
                    if 0 <= y < height and 0 <= x < width:
                        walls.add(Point(y, x))
    levels.append({
        "name": "Boxes",
        "description": "Four boxes in the corners",
        "walls": walls,
    })

    walls = set()
    for x in range(4, width - 4):
        walls.add(Point(height // 3, x))
        walls.add(Point(2 * height // 3, x))
    for y in range(2, height // 3 - 1):
        walls.add(Point(y, width // 3))
        walls.add(Point(y, 2 * width // 3))
    for y in range(2 * height // 3 + 1, height - 2):
        walls.add(Point(y, width // 3))
        walls.add(Point(y, 2 * width // 3))
    levels.append({
        "name": "Maze",
        "description": "Labyrinth with passages",
        "walls": walls,
    })

    return levels


class LarpSnake:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()

        self.game_height = self.height - 5
        self.game_width = self.width - 2

        if self.game_height < 14 or self.game_width < 30:
            raise RuntimeError("Terminal too small. Need at least 34x19.")

        self.levels = create_levels(self.game_height, self.game_width)
        self.current_level = 0
        self.high_scores = self._load_high_scores()

        self.snake: List[Point] = []
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food: Optional[Point] = None
        self.food_is_bonus = False
        self.score = 0
        self.game_over = False
        self.paused = False
        self.muted = False
        self.speed = 0.095          # slightly faster base = smoother feel
        self.move_accumulator = 0.0

        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        # Strong colors
        curses.init_pair(1, curses.COLOR_GREEN, -1)       # body
        curses.init_pair(2, curses.COLOR_RED, -1)         # normal food
        curses.init_pair(3, curses.COLOR_CYAN, -1)        # walls
        curses.init_pair(4, curses.COLOR_YELLOW, -1)      # title / UI
        curses.init_pair(5, curses.COLOR_WHITE, -1)       # text
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)     # head
        curses.init_pair(7, curses.COLOR_BLUE, -1)        # accent
        curses.init_pair(8, curses.COLOR_YELLOW, -1)      # bonus food
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # bonus highlight

    def _score_file(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".larpsnake_scores")

    def _load_high_scores(self) -> dict:
        scores = {i: 0 for i in range(len(self.levels))}
        try:
            with open(self._score_file(), "r") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        idx, val = int(parts[0]), int(parts[1])
                        if idx in scores:
                            scores[idx] = val
        except Exception:
            pass
        return scores

    def _save_high_scores(self):
        try:
            with open(self._score_file(), "w") as f:
                for idx, val in self.high_scores.items():
                    f.write(f"{idx}:{val}\n")
        except Exception:
            pass





    def _play_sound(self, kind: str = "normal"):
        """Soft short sounds — not painful. Respects mute."""
        if self.muted:
            return
        try:
            if sys.platform == "win32":
                import winsound
                if kind == "bonus":
                    winsound.Beep(520, 45)
                    winsound.Beep(780, 55)
                else:
                    winsound.Beep(460, 35)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass


    def show_level_menu(self) -> int:
        selected = 0
        while True:
            self.stdscr.erase()

            # Big title
            title = "╔══════════════════════╗"
            title2 = "║     LarpSnake        ║"
            title3 = "╚══════════════════════╝"
            cx = max(0, (self.width - len(title)) // 2)
            self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(1, cx, title)
            self.stdscr.addstr(2, cx, title2)
            self.stdscr.addstr(3, cx, title3)
            self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

            by = "by artiknite"
            self.stdscr.attron(curses.color_pair(7))
            self.stdscr.addstr(4, max(0, (self.width - len(by)) // 2), by)
            self.stdscr.attroff(curses.color_pair(7))

            hint = "↑↓ / WS  select   Enter play   Q quit"
            self.stdscr.addstr(6, max(0, (self.width - len(hint)) // 2), hint)

            for i, level in enumerate(self.levels):
                y = 8 + i * 2
                if y >= self.height - 3:
                    break

                is_sel = i == selected
                prefix = " >> " if is_sel else "    "
                line1 = f"{prefix}{i + 1}. {level['name']}"
                line2 = f"       {level['description']}   Best: {self.high_scores.get(i, 0)}"

                if is_sel:
                    self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    self.stdscr.addstr(y, 2, line1[: self.width - 4])
                    self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
                    self.stdscr.attron(curses.color_pair(5))
                    self.stdscr.addstr(y + 1, 2, line2[: self.width - 4])
                    self.stdscr.attroff(curses.color_pair(5))
                else:
                    self.stdscr.addstr(y, 2, line1[: self.width - 4])
                    self.stdscr.addstr(y + 1, 2, line2[: self.width - 4])

            footer = "Edges of the map are portals"
            self.stdscr.attron(curses.color_pair(7))
            self.stdscr.addstr(self.height - 1, max(0, (self.width - len(footer)) // 2), footer)
            self.stdscr.attroff(curses.color_pair(7))

            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in (curses.KEY_UP, ord("w"), ord("W"), ord("ц"), ord("Ц")):
                selected = (selected - 1) % len(self.levels)
            elif key in (curses.KEY_DOWN, ord("s"), ord("S"), ord("ы"), ord("Ы")):
                selected = (selected + 1) % len(self.levels)
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected
            elif key in (ord("q"), ord("Q"), ord("й"), ord("Й")):
                return -1

    def start_level(self, level_idx: int):
        self.current_level = level_idx
        self.walls = self.levels[level_idx]["walls"]
        self.score = 0
        self.game_over = False
        self.paused = False
        self.muted = False
        self.speed = 0.095
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food_is_bonus = False
        self.move_accumulator = 0.0

        start = Point(self.game_height // 2, max(3, self.game_width // 5))
        attempts = 0
        while (start in self.walls or
               Point(start.y, start.x - 1) in self.walls or
               Point(start.y, start.x - 2) in self.walls) and attempts < 50:
            start = Point(start.y, start.x + 1)
            if start.x >= self.game_width - 4:
                start = Point(start.y + 1, 3)
            attempts += 1

        self.snake = [
            start,
            Point(start.y, start.x - 1),
            Point(start.y, start.x - 2),
        ]
        self._spawn_food()

    def _spawn_food(self):
        free = []
        for y in range(self.game_height):
            for x in range(self.game_width):
                p = Point(y, x)
                if p not in self.snake and p not in self.walls:
                    free.append(p)

        if not free:
            self.food = None
            self.food_is_bonus = False
            return

        self.food = random.choice(free)
        self.food_is_bonus = random.random() < 0.17

    def _draw_food(self):
        """Draw food bigger and more visible."""
        if not self.food:
            return

        fy = self.food.y + 2
        fx = self.food.x + 1

        try:
            if self.food_is_bonus:
                # Golden bonus — very bright, looks bigger
                self.stdscr.attron(curses.color_pair(8) | curses.A_BOLD | curses.A_REVERSE)
                self.stdscr.addstr(fy, fx, "@@")
                self.stdscr.attroff(curses.color_pair(8) | curses.A_BOLD | curses.A_REVERSE)
            else:
                # Normal red — solid and noticeable
                self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                self.stdscr.addstr(fy, fx, "()")
                self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

    def draw(self):
        self.stdscr.erase()

        level_name = self.levels[self.current_level]["name"]
        mute_tag = "  [MUTE]" if self.muted else ""
        header = f" LarpSnake  │  {level_name}  │  Score: {self.score}  │  Best: {self.high_scores.get(self.current_level, 0)}{mute_tag} "
        self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addstr(0, max(0, (self.width - len(header)) // 2), header[: self.width - 1])
        self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

        # Double-line style frame
        try:
            self.stdscr.addstr(1, 0, "╔" + "═" * self.game_width + "╗")
            self.stdscr.addstr(self.game_height + 2, 0, "╚" + "═" * self.game_width + "╝")
        except curses.error:
            pass

        for y in range(self.game_height):
            try:
                self.stdscr.addch(y + 2, 0, "║")
                self.stdscr.addch(y + 2, self.game_width + 1, "║")
            except curses.error:
                pass

        # Walls
        self.stdscr.attron(curses.color_pair(3))
        for wall in self.walls:
            try:
                self.stdscr.addch(wall.y + 2, wall.x + 1, "█")
            except curses.error:
                pass
        self.stdscr.attroff(curses.color_pair(3))

        # Food (bigger)
        self._draw_food()

        # Snake — smoother looking body
        for i, seg in enumerate(self.snake):
            try:
                y, x = seg.y + 2, seg.x + 1
                if i == 0:
                    self.stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
                    self.stdscr.addch(y, x, "◉")
                    self.stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
                else:
                    self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    # alternating for a bit of texture
                    ch = "●" if i % 2 == 0 else "•"
                    self.stdscr.addch(y, x, ch)
                    self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

        # Bottom bar
        if self.paused:
            msg = "  PAUSED  — press P to continue  "
            self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD | curses.A_REVERSE)
            self.stdscr.addstr(self.height - 2, max(0, (self.width - len(msg)) // 2), msg)
            self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD | curses.A_REVERSE)
        else:
            help1 = " Arrows/WASD move   P pause   M mute   Q menu "
            self.stdscr.addstr(self.height - 2, max(0, (self.width - len(help1)) // 2), help1[: self.width - 1])

        tip = "() red = 10 pts    @@ gold = 20 pts    edges = portals"
        self.stdscr.attron(curses.color_pair(7))
        self.stdscr.addstr(self.height - 1, max(0, (self.width - len(tip)) // 2), tip)
        self.stdscr.attroff(curses.color_pair(7))

        self.stdscr.refresh()

    def handle_input(self):
        key = self.stdscr.getch()
        if key == -1:
            return

        # Q / Й
        if key in (ord("q"), ord("Q"), ord("й"), ord("Й")):
            self.game_over = True
            return

        # P / З — pause
        if key in (ord("p"), ord("P"), ord("з"), ord("З")):
            self.paused = not self.paused
            return

        # M / ь — mute toggle
        if key in (ord("m"), ord("M"), ord("ь"), ord("Ь")):
            self.muted = not self.muted
            return

        if self.paused:
            return

        # Movement — English + Russian layout (same physical keys)
        if key in (curses.KEY_UP, ord("w"), ord("W"), ord("ц"), ord("Ц")):
            if self.direction != Direction.DOWN:
                self.next_direction = Direction.UP
        elif key in (curses.KEY_DOWN, ord("s"), ord("S"), ord("ы"), ord("Ы")):
            if self.direction != Direction.UP:
                self.next_direction = Direction.DOWN
        elif key in (curses.KEY_LEFT, ord("a"), ord("A"), ord("ф"), ord("Ф")):
            if self.direction != Direction.RIGHT:
                self.next_direction = Direction.LEFT
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D"), ord("в"), ord("В")):
            if self.direction != Direction.LEFT:
                self.next_direction = Direction.RIGHT

    def update(self):
        if self.paused or self.game_over:
            return

        self.direction = self.next_direction
        head = self.snake[0]
        new_head = head + self.direction.value

        # Wrap-around portals
        if new_head.y < 0:
            new_head = Point(self.game_height - 1, new_head.x)
        elif new_head.y >= self.game_height:
            new_head = Point(0, new_head.x)
        if new_head.x < 0:
            new_head = Point(new_head.y, self.game_width - 1)
        elif new_head.x >= self.game_width:
            new_head = Point(new_head.y, 0)

        if new_head in self.walls or new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # Food collision — also accept the second cell of the 2-char food
        ate = False
        if self.food:
            if new_head == self.food:
                ate = True
            # because food is drawn as 2 characters, also count the right cell
            elif new_head == Point(self.food.y, self.food.x + 1):
                ate = True

        if ate:
            if self.food_is_bonus:
                self.score += 20
                self._play_sound("bonus")
            else:
                self.score += 10
                self._play_sound("normal")
            self.speed = max(0.042, self.speed - 0.003)
            self._spawn_food()
        else:
            self.snake.pop()

    def show_game_over(self):
        if self.score > self.high_scores.get(self.current_level, 0):
            self.high_scores[self.current_level] = self.score
            self._save_high_scores()
            new_record = True
        else:
            new_record = False

        self.stdscr.nodelay(False)
        while True:
            self.stdscr.erase()

            box = [
                "╔════════════════════╗",
                "║    GAME OVER       ║",
                "╚════════════════════╝",
            ]
            for i, line in enumerate(box):
                self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                self.stdscr.addstr(self.height // 2 - 5 + i, max(0, (self.width - len(line)) // 2), line)
                self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

            score_txt = f"Score: {self.score}"
            self.stdscr.addstr(self.height // 2 - 1, max(0, (self.width - len(score_txt)) // 2), score_txt)

            if new_record:
                rec = "★  NEW RECORD!  ★"
                self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                self.stdscr.addstr(self.height // 2 + 1, max(0, (self.width - len(rec)) // 2), rec)
                self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

            help_txt = "R retry    M menu    Q quit"
            self.stdscr.addstr(self.height // 2 + 4, max(0, (self.width - len(help_txt)) // 2), help_txt)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            # R/К   M/Ь   Q/Й
            if key in (ord("r"), ord("R"), ord("к"), ord("К")):
                self.stdscr.nodelay(True)
                return "retry"
            elif key in (ord("m"), ord("M"), ord("ь"), ord("Ь")):
                self.stdscr.nodelay(True)
                return "menu"
            elif key in (ord("q"), ord("Q"), ord("й"), ord("Й")):
                return "quit"

    def run(self):
        while True:
            level = self.show_level_menu()
            if level == -1:
                break

            self.start_level(level)

            last = time.perf_counter()
            while not self.game_over:
                self.handle_input()

                now = time.perf_counter()
                dt = now - last
                last = now

                self.move_accumulator += dt
                if self.move_accumulator >= self.speed:
                    self.update()
                    self.move_accumulator = 0.0

                self.draw()
                time.sleep(0.008)   # higher refresh = smoother

            result = self.show_game_over()
            if result == "quit":
                break
            elif result == "menu":
                continue


def main(stdscr):
    try:
        game = LarpSnake(stdscr)
        game.run()
    except RuntimeError as e:
        stdscr.clear()
        stdscr.addstr(0, 0, str(e))
        stdscr.addstr(2, 0, "Press any key...")
        stdscr.nodelay(False)
        stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)
