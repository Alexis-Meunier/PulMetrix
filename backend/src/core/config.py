from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
IMAGES_PATH: Path = PROJECT_ROOT / "data"
SQLITE_PATH: Path = IMAGES_PATH / "database.db"

SQLITE_URL: str = f"sqlite:///{SQLITE_PATH}"
