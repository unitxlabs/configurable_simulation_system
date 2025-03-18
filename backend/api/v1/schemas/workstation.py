from pydantic import BaseModel


class WorkstationSaveSettingsData(BaseModel):
    controller_config_id: int
    to_next_ws_offset: float
    camera_reset_time: float
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]


class WorkstationUpdateSettingsData(BaseModel):
    workstation_id: int
    controller_config_id: int
    to_next_ws_offset: float
    camera_reset_time: float
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]


class WorkstationListResponse(BaseModel):
    workstation_id: int
    controller_config_id: int
    to_next_ws_offset: float
    camera_reset_time: float
    sequence_count: int
    sequences_id: list[int]
    sequences_interval: list[int]
