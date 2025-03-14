from pydantic import BaseModel


class ControllerListResponse(BaseModel):
    isActive: bool
    controllerId: str
    controllerVersion: str
    camera: str
    cameraRatio: str
