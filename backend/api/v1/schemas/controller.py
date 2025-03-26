from pydantic import BaseModel


class ControllerSettingsData(BaseModel):
    controller_id: str
    controller_version: str
    cameras_id: list[str]
    cameras_type: list[str]
    image_width: int
    image_height: int
    image_channel: int
    capture_images_count: int
    network_inference_count: int


class ControllerListResponse(BaseModel):
    isActive: bool
    controller_id: str
    controller_version: str
    cameras_id: list[str]
    cameras_type: list[str]
    image_width: int
    image_height: int
    image_channel: int
    capture_images_count: int
    network_inference_count: int
