# AGENTS.md

## Project

VisionSeed is a Python + Pygame multi-game visual training application.

The current architecture is:

- `core/`: platform infrastructure
- `scenes/`: global pages only
- `games/`: game-specific modules
- `tests/`: unit and UI-oriented regression tests

The project is Windows-first and currently targets desktop usage.

## Current training categories

Keep these six top-level categories stable unless the user explicitly asks to change product taxonomy:

1. `accommodation`
2. `simultaneous`
3. `fusion`
4. `suppression`
5. `stereopsis`
6. `amblyopia`

`fusion` is currently a retained category with no active games. Do not remove the category unless explicitly requested.

## Current registered games

As of the current codebase, built-in games are registered through:

- `core/game_registry.py`

Current active games include:

- `accommodation.e_orientation`
- `accommodation.catch_fruit`
- `simultaneous.eye_find_patterns`
- `simultaneous.spot_difference`
- `simultaneous.pong`
- `suppression.weak_eye_key`
- `stereopsis.depth_grab`
- `amblyopia.precision_aim`

When adding or removing games, update registry, i18n, metrics labels, and tests together.

## Architecture rules

### 1. Global scenes vs game scenes

`scenes/` must only contain global platform pages, such as:

- main menu
- category page
- system settings
- onboarding
- license
- game host

Do not place game-private pages in `scenes/`.

Game-private pages belong under:

- `games/<category>/<game>/scenes/`

### 2. Game module structure

New games should follow this structure:

```text
games/<category>/<game>/
├─ game.py
├─ i18n.py
├─ scenes/
├─ services/
└─ assets/
```

Use the existing game modules as reference instead of inventing new patterns.

### 3. Entry contract

Games are integrated through `GameDescriptor`.

Do not bypass:

- `core/game_contract.py`
- `core/game_registry.py`
- `scenes/game_host_scene.py`

If a game has multiple internal pages, route them inside the game module, usually with a root scene.

### 4. Data and records

Training data is namespaced by `game_id`.

When saving or reading records:

- preserve `game_id`
- do not mix per-game history with global history
- prefer game-local services over direct scene-level record logic

Relevant infrastructure:

- `core/data_manager.py`
- `core/scene_manager.py`

### 5. i18n

Global text belongs in:

- `core/language_manager.py`

Game-private text belongs in:

- `games/<category>/<game>/i18n.py`

Do not keep growing global language tables with game-specific keys when a game-local i18n module already exists.

## UI and UX rules

### 1. Platform style

Platform pages use the shared bright theme from:

- `core/ui_theme.py`

Keep these pages visually consistent:

- `menu_scene.py`
- `category_scene.py`
- `system_settings_scene.py`
- onboarding and license pages

Do not reintroduce dark full-screen platform pages unless explicitly requested.

### 2. Training HUD

Training pages should avoid clutter.

Prefer:

- top-left: progress or game-specific counters
- top-center: countdown or primary session info
- top-right: return / secondary status

Avoid overlapping chips, labels, and helper text.

### 3. Child-friendly interaction

For children, keyboard-first interaction is preferred.

Default mapping:

- arrows: move / navigate
- `Space`: primary action
- `Enter`: continue / confirm
- `Esc`: back

Mouse can remain as compatibility input, but should not be the only viable input path for core gameplay.

### 4. Anaglyph mode

If a game uses red-blue glasses mode, reuse the existing implementation approach from:

- `games/simultaneous/eye_find_patterns`
- `games/common/anaglyph.py`

Do not invent a separate red-blue system per game.

Use the current project baseline:

- normal mode
- glasses mode
- `left_red_right_blue`
- `left_blue_right_red`

Prefer:

- strong red/blue only for training-critical elements
- neutral or weaker colors for helpers/backgrounds
- mixed overlap behavior consistent with current implementation

## Gameplay rules

### 1. Training goal first

Do not port classic games literally.

Convert them into training shells where:

- the visual task is primary
- the game loop motivates repetition
- interaction remains simple enough for children

### 2. One main training goal per game

Avoid mixing multiple training targets into one game unless explicitly requested.

Examples:

- `catch_fruit`: accommodation
- `spot_difference` / `pong`: simultaneous vision
- `precision_aim`: amblyopia

### 3. Short sessions, clear feedback

Games should provide:

- short rounds or short-session pacing
- immediate feedback
- simple success/failure logic
- clear next-step guidance

## Testing rules

Always run regression tests after meaningful code changes.

Minimum expected commands:

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

Use targeted test runs first when iterating on one module, then run the full suite.

If a fix changes gameplay, update or add tests alongside the code change.

## Editing rules

- Prefer small, local changes over broad rewrites.
- Use existing helpers, services, and scene patterns before creating new abstractions.
- Do not delete user-facing categories, games, or product flows without explicit approval.
- Do not revert unrelated work in the repository.
- Preserve current Windows compatibility.

## Documentation rules

When behavior changes, update the relevant docs if they are clearly affected, especially:

- `README.md`
- `docs/视觉训练小游戏分类指南.md`
- game-specific design docs in `docs/`

Keep planning documents and actual code status aligned. If something is only planned and not implemented, say so clearly in docs.

## Preferred implementation order

When expanding the project, prefer this sequence:

1. confirm category and training goal
2. create or update game module
3. register game
4. wire i18n
5. add or update tests
6. run full regression
7. update docs if needed

## Good reference modules

Use these modules as practical references:

- `games/accommodation/e_orientation`
- `games/simultaneous/eye_find_patterns`
- `games/simultaneous/spot_difference`
- `games/simultaneous/pong`
- `games/common/arcade_training/scene.py`

These reflect the current project direction better than older or removed experiments.
