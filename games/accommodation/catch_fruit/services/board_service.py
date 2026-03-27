import random

from core.asset_loader import project_path


class CatchFruitBoardService:
    def __init__(self):
        self.fruit_assets = {
            name: project_path("games", "accommodation", "catch_fruit", "assets", "objects", f"{name}.png")
            for name in ("apple", "banana", "orange", "strawberry", "grapes", "watermelon")
        }
        self.basket_asset = project_path("games", "accommodation", "catch_fruit", "assets", "objects", "basket.png")
        self.fruit_points = {"apple": 10, "banana": 10, "orange": 10, "strawberry": 12, "grapes": 12, "watermelon": 18}

    def _random_fruit_name(self, stage_index):
        if stage_index == 0:
            return random.choice(("apple", "banana", "orange"))
        if stage_index == 1:
            return random.choice(("apple", "orange", "strawberry", "grapes"))
        return random.choice(tuple(self.fruit_assets.keys()))

    def _fruit_speed(self, stage_index, difficulty_level):
        fruit_speed = random.uniform(3.2, 4.8) + difficulty_level * 0.25
        if stage_index == 0:
            fruit_speed -= 0.4
        elif stage_index == 1:
            fruit_speed += 0.2
        else:
            fruit_speed += 0.8
        return fruit_speed

    def create_fruit(self, play_area, stage_index, difficulty_level, occupied_x=None):
        occupied_x = occupied_x or []
        attempts = 0
        fruit_x = play_area.centerx
        while attempts < 12:
            candidate = random.randint(play_area.left + 60, play_area.right - 60)
            if all(abs(candidate - other) >= 76 for other in occupied_x):
                fruit_x = candidate
                break
            attempts += 1
        spawn_lane = random.randint(0, 3)
        return {
            "x": fruit_x,
            "y": play_area.top + 24 - spawn_lane * 54,
            "speed": self._fruit_speed(stage_index, difficulty_level),
            "fruit_name": self._random_fruit_name(stage_index),
            "start_size": 88,
            "end_size": 36,
        }

    def create_round(self, play_area, stage_index, difficulty_level, basket_x=None):
        fruit_count = random.randint(2, 3) if stage_index < 2 else random.randint(3, 4)
        fruits = []
        for _ in range(fruit_count):
            fruits.append(self.create_fruit(play_area, stage_index, difficulty_level, [fruit["x"] for fruit in fruits]))
        return {
            "basket_x": play_area.centerx if basket_x is None else basket_x,
            "fruits": fruits,
            "move_dir": 0,
            "stage_index": stage_index,
            "catch_window_top": play_area.bottom - 118,
        }

    def stage_label_key(self, stage_index):
        return (
            "catch_fruit.stage.warmup",
            "catch_fruit.stage.steady",
            "catch_fruit.stage.sprint",
        )[stage_index]

    def goal_label_key(self, stage_index):
        return (
            "catch_fruit.goal.warmup",
            "catch_fruit.goal.steady",
            "catch_fruit.goal.sprint",
        )[stage_index]

