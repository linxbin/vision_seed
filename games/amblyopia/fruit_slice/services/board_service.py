import random


class FruitSliceBoardService:
    FRUIT_COLORS = ((238, 120, 96), (244, 196, 80), (116, 196, 122))
    OBJECT_PADDING = 20

    def _random_center(self, play_area, radius):
        return (
            random.randint(play_area.left + radius, play_area.right - radius),
            random.randint(play_area.top + radius, play_area.bottom - radius),
        )

    def _distance_sq(self, point_a, point_b):
        dx = point_a[0] - point_b[0]
        dy = point_a[1] - point_b[1]
        return dx * dx + dy * dy

    def _create_object(self, play_area, is_bomb, existing=None):
        radius = random.randint(28, 42)
        center = self._random_center(play_area, radius)
        existing = existing or ()
        for _ in range(24):
            overlaps = False
            for item in existing:
                min_distance = radius + item["radius"] + self.OBJECT_PADDING
                if self._distance_sq(center, item["center"]) < min_distance * min_distance:
                    overlaps = True
                    break
            if not overlaps:
                break
            center = self._random_center(play_area, radius)
        return {
            "center": (
                center[0],
                center[1],
            ),
            "radius": radius,
            "is_bomb": is_bomb,
            "color": (58, 58, 58) if is_bomb else random.choice(self.FRUIT_COLORS),
        }

    def create_round(self, play_area):
        fruit = self._create_object(play_area, is_bomb=False)
        items = [fruit]
        if random.random() < 0.35:
            items.append(self._create_object(play_area, is_bomb=True, existing=items))
        return {
            "items": items,
            "target_index": 0,
        }
