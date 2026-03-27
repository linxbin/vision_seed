from pathlib import Path

import pygame


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_IMAGE_CACHE = {}


def project_path(*parts):
    return PROJECT_ROOT.joinpath(*parts)


def load_image_if_exists(path, size=None):
    asset_path = Path(path)
    if not asset_path.exists():
        return None

    cache_key = (str(asset_path.resolve()), size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key].copy()

    image = pygame.image.load(str(asset_path))
    if pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    if size:
        image = pygame.transform.smoothscale(image, size)
    _IMAGE_CACHE[cache_key] = image
    return image.copy()
