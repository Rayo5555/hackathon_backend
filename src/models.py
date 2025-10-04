from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, func
from .database import metadata

users = Table(
    "users",
    metadata,
    Column("users", Integer, primary_key=True),
)