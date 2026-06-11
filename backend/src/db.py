# db.py
from sqlalchemy import Engine
from sqlmodel import create_engine

import src.data.model.analysis_model  # noqa: F401
from src.core.config import SQLITE_URL

engine: Engine = create_engine(SQLITE_URL, echo=True)
