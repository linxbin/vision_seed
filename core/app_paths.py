import os
import sys


APP_NAME = "VisionSeed"


def get_install_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_root() -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return get_install_root()


def get_resource_path(*parts: str) -> str:
    return os.path.join(get_resource_root(), *parts)


def get_user_root_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if not base:
        base = os.path.expanduser("~")
    user_root = os.path.join(base, APP_NAME)
    os.makedirs(user_root, exist_ok=True)
    return user_root


def get_user_data_dir() -> str:
    data_dir = os.path.join(get_user_root_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_user_config_dir() -> str:
    config_dir = os.path.join(get_user_root_dir(), "config")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir
