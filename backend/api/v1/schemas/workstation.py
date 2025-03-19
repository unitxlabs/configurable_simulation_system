from pydantic import BaseModel


class WorkstationSaveSettingsData(BaseModel):
    workstation_id: int
    controller_config_id: int
    to_next_ws_offset: int
    camera_reset_time: float
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]


class WorkstationUpdateSettingsData(BaseModel):
    id: int
    workstation_id: int
    controller_config_id: int
    to_next_ws_offset: int
    camera_reset_time: float
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]


class WorkstationListResponse(BaseModel):
    id: int
    workstation_id: int
    controller_config_id: int
    camera_reset_time: float
    to_next_ws_offset: int
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]
