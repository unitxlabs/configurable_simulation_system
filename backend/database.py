from fastapi import Depends
from src.database.base import ConfigurableSimulationSystemDB

db_instance = ConfigurableSimulationSystemDB()


def get_db():
    return next(db_instance.get_db())
