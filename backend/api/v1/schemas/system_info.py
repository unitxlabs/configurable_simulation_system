from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    cpu: str
    gpu: str
    ram: str
    ssds: str
    name: str
