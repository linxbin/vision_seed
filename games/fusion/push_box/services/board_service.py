from collections import deque


class FusionPushBoxBoardService:
    LEVELS = (
        (
            "#########",
            "#   #   #",
            "#   # . #",
            "#   $   #",
            "#   @   #",
            "#       #",
            "#########",
        ),
        (
            "##########",
            "#   #   .#",
            "#   # $  #",
            "#   # $  #",
            "#   @    #",
            "#        #",
            "##########",
        ),
        (
            "#########",
            "#   .   #",
            "#   $   #",
            "### # ###",
            "#   @   #",
            "#       #",
            "#########",
        ),
        (
            "###########",
            "#   .   # #",
            "# ### $   #",
            "#   # ### #",
            "# $   @   #",
            "#     #   #",
            "###########",
        ),
        (
            "#########",
            "# .   . #",
            "# $   $ #",
            "#   @   #",
            "#   #   #",
            "#       #",
            "#########",
        ),
    )

    MOVE_DELTAS = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
    }

    def create_level(self, level_index):
        layout = self.LEVELS[level_index % len(self.LEVELS)]
        walls = set()
        targets = set()
        boxes = set()
        player = (1, 1)
        for y, row in enumerate(layout):
            for x, cell in enumerate(row):
                if cell == "#":
                    walls.add((x, y))
                elif cell == ".":
                    targets.add((x, y))
                elif cell == "$":
                    boxes.add((x, y))
                elif cell == "@":
                    player = (x, y)
                elif cell == "*":
                    targets.add((x, y))
                    boxes.add((x, y))
                elif cell == "+":
                    targets.add((x, y))
                    player = (x, y)
        return {
            "width": len(layout[0]),
            "height": len(layout),
            "walls": walls,
            "targets": targets,
            "boxes": boxes,
            "player": player,
            "steps": 0,
            "pushes": 0,
            "level_index": level_index % len(self.LEVELS),
        }

    def attempt_move(self, state, direction):
        dx, dy = self.MOVE_DELTAS[direction]
        px, py = state["player"]
        next_pos = (px + dx, py + dy)
        if next_pos in state["walls"]:
            return False, False
        boxes = set(state["boxes"])
        pushed = False
        if next_pos in boxes:
            beyond = (next_pos[0] + dx, next_pos[1] + dy)
            if beyond in state["walls"] or beyond in boxes:
                return False, False
            boxes.remove(next_pos)
            boxes.add(beyond)
            pushed = True
            state["pushes"] += 1
        state["boxes"] = boxes
        state["player"] = next_pos
        state["steps"] += 1
        return True, pushed

    def is_cleared(self, state):
        return bool(state["targets"]) and state["targets"].issubset(state["boxes"])

    def has_any_pushable_box(self, state):
        boxes = set(state["boxes"])
        reachable = self._reachable_tiles(state["player"], state["walls"], boxes)
        for box_x, box_y in boxes:
            for dx, dy in self.MOVE_DELTAS.values():
                player_spot = (box_x - dx, box_y - dy)
                beyond = (box_x + dx, box_y + dy)
                if player_spot not in reachable:
                    continue
                if beyond in state["walls"] or beyond in boxes:
                    continue
                return True
        return False

    def is_level_solvable(self, level_index):
        initial = self.create_level(level_index)
        return self.is_state_solvable(initial)

    def is_state_solvable(self, state):
        start_key = (state["player"], frozenset(state["boxes"]))
        queue = deque([state])
        visited = {start_key}
        while queue:
            current = queue.popleft()
            if self.is_cleared(current):
                return True
            boxes = set(current["boxes"])
            reachable = self._reachable_tiles(current["player"], current["walls"], boxes)
            for box_x, box_y in boxes:
                for dx, dy in self.MOVE_DELTAS.values():
                    player_spot = (box_x - dx, box_y - dy)
                    beyond = (box_x + dx, box_y + dy)
                    if player_spot not in reachable:
                        continue
                    if beyond in current["walls"] or beyond in boxes:
                        continue
                    next_boxes = set(boxes)
                    next_boxes.remove((box_x, box_y))
                    next_boxes.add(beyond)
                    next_state = {
                        "width": current["width"],
                        "height": current["height"],
                        "walls": current["walls"],
                        "targets": current["targets"],
                        "boxes": next_boxes,
                        "player": (box_x, box_y),
                        "steps": current["steps"] + 1,
                        "pushes": current["pushes"] + 1,
                        "level_index": current["level_index"],
                    }
                    key = (next_state["player"], frozenset(next_boxes))
                    if key in visited:
                        continue
                    visited.add(key)
                    queue.append(next_state)
        return False

    def _reachable_tiles(self, start, walls, boxes):
        queue = deque([start])
        visited = {start}
        blockers = set(walls) | set(boxes)
        while queue:
            x, y = queue.popleft()
            for dx, dy in self.MOVE_DELTAS.values():
                nxt = (x + dx, y + dy)
                if nxt in blockers or nxt in visited:
                    continue
                visited.add(nxt)
                queue.append(nxt)
        return visited
