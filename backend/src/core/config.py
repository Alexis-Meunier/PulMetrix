from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
SQLITE_PATH: Path = PROJECT_ROOT / "data" / "database.db"

SQLITE_URL: str = f"sqlite:///{SQLITE_PATH}"
