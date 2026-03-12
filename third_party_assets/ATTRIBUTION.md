# Third-Party Assets

This directory stores upstream asset packages before they are curated into runtime asset folders.

## Kenney UI Pack
- Source: https://kenney.nl/assets/ui-pack
- Downloaded: 2026-03-12
- Author: Kenney
- License: CC0 1.0 Universal
- Local package: `third_party_assets/kenney/kenney_ui-pack.zip`
- Extracted folder: `third_party_assets/kenney/ui-pack/`
- Intended use:
  - shared UI buttons
  - shared icons
  - optional UI font evaluation

## Kenney Game Icons
- Source: https://kenney.nl/assets/game-icons
- Downloaded: 2026-03-12
- Author: Kenney
- License: CC0 1.0 Universal
- Local package: `third_party_assets/kenney/kenney_game-icons.zip`
- Extracted folder: `third_party_assets/kenney/game-icons/`
- Intended use:
  - runtime button icons
  - back / confirm / close / settings iconography
  - lightweight 2D icon source for help and result flows

## Integration Rules
- Do not use assets from this directory directly in runtime code.
- Curate selected files into `assets/` or `games/<category>/<game>/assets/`.
- Preserve the original package and license files.
- Record any copied or modified assets in the target folder attribution file.
