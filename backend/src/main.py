from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from src.db import engine
from src.presentation.rest import compute_resource, delete_resource, get_resource, hello_world_resource, patch_resource

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


create_db_and_tables()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(hello_world_resource.router)
app.include_router(get_resource.router)
app.include_router(compute_resource.router)
app.include_router(delete_resource.router)
app.include_router(patch_resource.router)
