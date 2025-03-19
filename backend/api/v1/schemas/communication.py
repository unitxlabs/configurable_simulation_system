from pydantic import BaseModel


class CommunicationSaveSettingsData(BaseModel):
    name: str
    part_type: str
    part_interval: float
    communication_type: int
    communication_step: int
    workstation_count: int
    workstation_config_ids: list[int]
    workstations_in_use: list[bool]


class CommunicationUpdateSettingsData(BaseModel):
    id: int
    name: str
    part_type: str
    part_interval: float
    communication_type: int
    communication_step: int
    workstation_count: int
    workstation_config_ids: list[int]
    workstations_in_use: list[bool]


class CommunicationListResponse(BaseModel):
    id: int
    name: str
    part_type: str
    part_interval: float
    communication_type: int
    communication_step: int
    workstation_count: int
    workstation_config_ids: list[int]
    workstations_in_use: list[bool]
