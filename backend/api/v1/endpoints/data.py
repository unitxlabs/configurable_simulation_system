from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.v1.schemas import DataResponse, CommonResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from typing import Optional
from backend.database import db_instance

dataRouter = APIRouter()


@dataRouter.get("/list", response_model=CommonResponse)
def get_data_list(
    search: Optional[str] = Query(None, description="搜索关键词"),
    cpu: Optional[str] = Query(None, description="CPU 参数"),
    gpu: Optional[str] = Query(None, description="GPU 参数"),
    camera_count: Optional[int] = Query(None, description="摄像头数量"),
    camera_resolution: Optional[str] = Query(None, description="摄像头分辨率"),
    material_image_count: Optional[int] = Query(None, description="素材图片数量"),
    material_inference_times: Optional[int] = Query(None, description="素材推理次数"),
    model_count: Optional[int] = Query(None, description="模型数量"),
    defect_count: Optional[int] = Query(None, description="缺陷数量"),
    db: Session = Depends(get_db),
):
    # todo 获取数据
    print(
        {
            "search": search,
            "cpu": cpu,
            "gpu": gpu,
            "camera_count": camera_count,
            "camera_resolution": camera_resolution,
            "material_image_count": material_image_count,
            "material_inference_times": material_inference_times,
            "model_count": model_count,
            "defect_count": defect_count,
        }
    )
    query_data = db_instance.query_data(table_name="simulation_result", data_dict={})
    print(query_data)
    data = [
        DataResponse(
            id="1",
            name="设备 A",
            cpu="Intel i7",
            gpu="NVIDIA RTX 3080",
            camera_count=4,
            camera_resolution="1920x1080",
            material_image_count=1000,
            material_inference_times=500,
            model_count=5,
            defect_count=3,
        )
    ]
    return CommonResponse(msg="", data=data)
