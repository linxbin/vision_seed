# v1.1 Content Backlog

Goal: ship a more complete VisionSeed release with at least 3 games per category, while preserving current product quality, UI consistency, bilingual support, data recording, and regression safety.

## Shared Done Criteria

Each new game must satisfy all of the following:

- Registered through `GameRegistry` with a unique `game_id`
- Category page entry works
- Home, Help, Play, Result flow works
- `zh-CN` and `en-US` copy is complete
- Result is saved with `training_metrics`
- At least one scene test covers entry, play, and save flow
- No HUD overlap in 900x700 baseline layout
- Return path is clear: `Esc` or Back returns correctly

## Batch A

### 1. suppression.find_same

Template:
- `games/simultaneous/spot_difference`

Files:
- `games/suppression/find_same/game.py`
- `games/suppression/find_same/i18n.py`
- `games/suppression/find_same/scenes/root_scene.py`
- `games/suppression/find_same/services/board_service.py`
- `games/suppression/find_same/services/scoring_service.py`
- `games/suppression/find_same/services/session_service.py`
- `tests/games/suppression/find_same/test_find_same_scene.py`

Tasks:
- Build pair-matching board with clue-compatible same-shape targets
- Reuse red/blue filter picker and help/result structure from simultaneous games
- Add suppression metrics:
  - `match_accuracy`
  - `best_combo`
  - `avg_find_time`
- Add board hit-test and confirm flow
- Add registry wiring and language merge validation

### 2. amblyopia.whack_a_mole

Template:
- `games/amblyopia/precision_aim`

Files:
- `games/amblyopia/whack_a_mole/game.py`
- `games/amblyopia/whack_a_mole/i18n.py`
- `games/amblyopia/whack_a_mole/scenes/root_scene.py`
- `games/amblyopia/whack_a_mole/services/board_service.py`
- `games/amblyopia/whack_a_mole/services/scoring_service.py`
- `games/amblyopia/whack_a_mole/services/session_service.py`
- `tests/games/amblyopia/whack_a_mole/test_whack_a_mole_scene.py`

Tasks:
- Build 6-9 hole layout with high-contrast mole and decoy states
- Preserve black/white stimulus background and keep HUD separate
- Add weak-vision metrics:
  - `hit_accuracy`
  - `avg_reaction_time`
  - `best_streak`
- Add stage progression by dwell time and target density
- Add miss and false-hit feedback

### 3. accommodation.snake

Template:
- `games/accommodation/catch_fruit`

Files:
- `games/accommodation/snake/game.py`
- `games/accommodation/snake/i18n.py`
- `games/accommodation/snake/scenes/root_scene.py`
- `games/accommodation/snake/services/board_service.py`
- `games/accommodation/snake/services/scoring_service.py`
- `games/accommodation/snake/services/session_service.py`
- `tests/games/accommodation/snake/test_snake_scene.py`

Tasks:
- Build grid movement, snake body update, food spawning
- Shift training focus to visual tracking and size/clarity changes
- Add accommodation metrics:
  - `longest_length`
  - `foods_caught`
  - `best_survival_time`
- Add stage-based speed and food size progression
- Add fail/restart loop and result page

## Batch B

### 4. suppression.red_blue_catch

Template:
- `games/simultaneous/pong`

Tasks:
- Convert paddle return flow into color-matched falling-ball catch flow
- Reuse red/blue mode UX exactly
- Add suppression metrics:
  - `color_match_accuracy`
  - `miss_count`
  - `best_combo`

### 5. stereopsis.brick_breaker

Template:
- `games/stereopsis/depth_grab`
- `games/simultaneous/pong`

Tasks:
- Build paddle-ball-brick collision loop
- Express depth through layered brick placement, not size-only cues
- Add stereopsis metrics:
  - `brick_clear_count`
  - `front_back_confusion_count`
  - `avg_reaction_time`

### 6. amblyopia.fruit_slice

Template:
- `games/amblyopia/precision_aim`

Tasks:
- Build click-based slice flow first, no gesture dependency in v1
- Keep weak-vision high-contrast stimulus rules
- Add metrics:
  - `slice_accuracy`
  - `bonus_hits`
  - `best_combo`

## Batch C

### 7. stereopsis.frogger

Template:
- `games/stereopsis/depth_grab`

Tasks:
- Build lane/platform movement with layered distance cues
- Reuse red/blue mode UX from depth category
- Add metrics:
  - `safe_crosses`
  - `fall_count`
  - `depth_accuracy`

### 8. fusion.tetris

Template:
- `games/fusion/push_box`

Tasks:
- Build minimal falling-block flow
- Use fusion-specific left/right visual split instead of pure arcade presentation
- Add metrics:
  - `lines_cleared`
  - `max_speed_level`
  - `fusion_accuracy`

### 9. fusion.path_fusion

Template:
- `games/fusion/push_box`

Tasks:
- Build left/right partial path fusion puzzle
- Add metrics:
  - `fusion_path_accuracy`
  - `best_streak`
  - `avg_solve_time`

## Regression Pass

After each batch:

- Run targeted scene tests for all new games
- Run:
  - `tests.core.test_game_registry`
  - `tests.core.test_scene_flow_integration`
- Re-check menu/category summaries for new metric labels
- Verify new i18n keys appear in both languages
