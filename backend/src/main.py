from fastapi import FastAPI
from sqlmodel import SQLModel

from src.db import engine
from src.presentation.rest import hello_world_resource


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


create_db_and_tables()
app = FastAPI()
app.include_router(hello_world_resource.router)
