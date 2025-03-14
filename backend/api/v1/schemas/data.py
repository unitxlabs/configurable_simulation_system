from pydantic import BaseModel


class DataResponse(BaseModel):
    id: str  # id
    cpu: str  # cpu
    gpu: str  # gpu
    camera_count: int  # 相机数量
    camera_resolution: str  # 相机分辨率
    material_image_count: int  # 物料图片数量
    material_inference_times: int  # 物料图片推理次数
    model_count: int  # 模型数量
    defect_count: int  # 缺陷数量
