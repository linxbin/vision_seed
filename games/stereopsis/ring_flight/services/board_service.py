import random


class RingFlightBoardService:
    DEPTHS = (0, 1, 2)
    DEPTH_DISPARITY = {0: 28, 1: 18, 2: 10}
    DEPTH_LABELS = {0: "front", 1: "middle", 2: "back"}

    def create_wave(self, play_area):
        lanes = [
            play_area.left + int(play_area.width * 0.22),
            play_area.centerx,
            play_area.right - int(play_area.width * 0.22),
        ]
        random.shuffle(lanes)
        rings = []
        for depth, x in zip(self.DEPTHS, lanes):
            rings.append(
                {
                    "depth": depth,
                    "x": float(x),
                    "progress": 0.0,
                    "base_radius": 22,
                    "target_radius": 68,
                    "thickness": 16,
                    "disparity": self.DEPTH_DISPARITY[depth],
                }
            )
        return {"rings": rings}

    def ring_display_state(self, play_area, ring):
        progress = max(0.0, min(1.0, float(ring["progress"])))
        y = play_area.top + 54 + progress * (play_area.height - 134)
        radius = ring["base_radius"] + (ring["target_radius"] - ring["base_radius"]) * progress
        thickness = max(10, min(int(ring["thickness"]), int(radius * 0.55)))
        return {
            "center": (int(ring["x"]), int(y)),
            "radius": int(radius),
            "thickness": thickness,
            "inner_radius": max(8, int(radius - thickness)),
            "disparity": int(ring["disparity"]),
        }
