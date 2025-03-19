from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.endpoints.controller import controllerRouter
from backend.api.v1.endpoints.system_info import systemInfoRouter
from backend.api.v1.endpoints.workstation import workstationRouter
from backend.api.v1.endpoints.communication import communicationRouter
from backend.api.v1.endpoints.data import dataRouter

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(controllerRouter, prefix="/api/v1/controller")
app.include_router(systemInfoRouter, prefix="/api/v1/system")
app.include_router(dataRouter, prefix="/api/v1/data")
app.include_router(workstationRouter, prefix="/api/v1/workstation")
app.include_router(communicationRouter, prefix="/api/v1/communication")


@app.get("/")
def root():
    return {"message": "Welcome to FastAPI"}
