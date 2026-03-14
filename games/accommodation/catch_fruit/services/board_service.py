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

    def create_round(self, play_area, stage_index, difficulty_level):
        fruit_x = random.randint(play_area.left + 60, play_area.right - 60)
        fruit_y = play_area.top + 24
        fruit_speed = random.uniform(3.2, 4.8) + difficulty_level * 0.25
        if stage_index == 0:
            fruit_speed -= 0.4
            fruit_name = random.choice(("apple", "banana", "orange"))
        elif stage_index == 1:
            fruit_speed += 0.2
            fruit_name = random.choice(("apple", "orange", "strawberry", "grapes"))
        else:
            fruit_speed += 0.8
            fruit_name = random.choice(tuple(self.fruit_assets.keys()))
        return {
            "basket_x": play_area.centerx,
            "fruit_x": fruit_x,
            "fruit_y": fruit_y,
            "fruit_speed": fruit_speed,
            "fruit_name": fruit_name,
            "move_dir": 0,
            "stage_index": stage_index,
            "start_size": 88,
            "end_size": 36,
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

