from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.v1.schemas import DataResponse, CommonResponse
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
    data_dict = {}
    if cpu:
        data_dict["cpu"] = cpu
    if gpu:
        data_dict["gpu"] = gpu.split(",")
    if camera_count:
        data_dict["camera_count"] = [camera_count]
    if camera_resolution:
        data_dict["camera_resolution"] = camera_resolution
    if material_image_count:
        data_dict["material_image_count"] = material_image_count
    if material_inference_times:
        data_dict["material_inference_times"] = [material_inference_times]
    if model_count:
        data_dict["model_count"] = model_count
    if defect_count:
        data_dict["defect_count"] = defect_count
    print(data_dict)
    query_data = db_instance.query_data(
        table_name="simulation_result", data_dict=data_dict
    )
    print(query_data)
    return CommonResponse(msg="", data=query_data)


@dataRouter.get("/select", response_model=CommonResponse)
def get_data_select():
    cpuData = db_instance.get_used_cpu()
    cpu_select_options = [{"label": f"{cpu}", "value": cpu} for cpu in cpuData]
    gpuData = db_instance.get_used_gpus()
    gpu_select_options = [
        {"label": f"{','.join(gpu)}", "value": ",".join(gpu)} for gpu in gpuData
    ]
    select_options = {
        "cpu_select_options": cpu_select_options,
        "gpu_select_options": gpu_select_options,
    }
    return CommonResponse(msg="获取成功", data=select_options)
