from fastapi import APIRouter, Depends, HTTPException, Query
import requests
from backend.api.v1.schemas import (
    WorkstationListResponse,
    CommonResponse,
    WorkstationSaveSettingsData,
    WorkstationUpdateSettingsData,
)
from backend.logger import Logger
from typing import List
from backend.database import db_instance
from typing import Optional

workstationRouter = APIRouter()


# @workstationRouter.get("/list", response_model=CommonResponse)
# def get_workstation_list():
#     url = "http://localhost:10001/perception/api/v1/hardware/all_cameras_workstations_mapping"

#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # 如果状态码不是200，会抛出异常
#         data = response.json()
#     except requests.exceptions.RequestException:
#         raise HTTPException(status_code=503, detail="端口未开或无法连接到服务")
#     # 获取映射数据
#     mapping = data.get("mapping", {})

#     workstation_list = []

#     for camera_id, camera_info in mapping.items():
#         print(camera_id, camera_info)
#         # 获取 max_width 和 max_height
#         max_width = camera_info.get("max_width", 0)
#         max_height = camera_info.get("max_height", 0)
#         has_version = False
#         # 遍历所有控制器类型
#         for workstation_type, data in camera_info.items():
#             # 跳过 max_width 和 max_height，处理版本信息
#             if workstation_type in ["max_width", "max_height"]:
#                 continue

#             # 如果 workstation_type 是控制器ID（例如 "/dev/ttyS3"），并且 data 是版本列表
#             if isinstance(data, list):  # 版本列表
#                 workstation_id = workstation_type  # 这里是控制器ID，例如 "/dev/ttyS3"
#                 result = next(
#                     (
#                         item
#                         for item in data
#                         if item.startswith("V") and item[1:].isdigit()
#                     ),
#                     None,
#                 )
#                 if result:
#                     has_version = True
#                     workstation_list.append(
#                         WorkstationListResponse(
#                             workstation_id=workstation_id,  # 这里是控制器ID，例如 "/dev/ttyS3"
#                             workstation_version=result,
#                             cameras_id=[camera_id],
#                             image_width=max_width,
#                             image_height=max_height,
#                             image_channel=3,
#                             capture_images_count=11,
#                             network_inference_count=31,
#                             isActive=True,
#                         )
#                     )
#         if not has_version:
#             # 添加没有版本的控制器条目
#             workstation_list.append(
#                 WorkstationListResponse(
#                     workstation_id="",  # 这里是控制器ID，例如 "/dev/ttyS3"
#                     workstation_version="",
#                     cameras_id=[camera_id],
#                     image_width=max_width,
#                     image_height=max_height,
#                     image_channel=3,
#                     capture_images_count=11,
#                     network_inference_count=31,
#                     isActive=True,
#                 )
#             )

#     return CommonResponse(msg="", data=workstation_list)


@workstationRouter.get("/data", response_model=CommonResponse)
def get_workstation_data(
    # workstation_id: Optional[str] = Query(None, description=""),
    # workstation_version: Optional[str] = Query(None, description=""),
    # cameras_id: Optional[str] = Query(None, description=""),
):
    data_dict = {}
    # if workstation_id:
    #     data_dict["workstation_id"] = workstation_id
    # if workstation_version:
    #     data_dict["workstation_version"] = workstation_version
    # if cameras_id:
    #     data_dict["cameras_id"] = [cameras_id]
    data = db_instance.query_data(table_name="workstation_config", data_dict=data_dict)
    return CommonResponse(msg="获取成功", data=data)


@workstationRouter.post("/save", response_model=CommonResponse)
async def save(data: WorkstationSaveSettingsData):
    db_instance.add_data(table_name="workstation_config", data_dict=data.dict())
    Logger.log_action(f"创建工位:{data}")
    return CommonResponse(msg="创建成功", data={})


@workstationRouter.post("/update", response_model=CommonResponse)
async def update(data: WorkstationUpdateSettingsData):
    db_instance.update_data(table_name="workstation_config", data_dict=data.dict())
    Logger.log_action(f"修改工位:{data}")
    return CommonResponse(msg="修改成功", data={})


@workstationRouter.post("/delete", response_model=CommonResponse)
async def delete_workstation_data(
    id: Optional[int] = None,
    workstation_id: Optional[int] = None,
):
    if id is None or workstation_id is None:
        raise HTTPException(
            status_code=400, detail="Both 'id' and 'workstation_id' must be provided."
        )

    db_instance.delete_data(table_name="workstation_config", data_id=id)
    Logger.log_action(f"删除工位ID为{id},workstation_id为{workstation_id}的工位:")
    return CommonResponse(msg="删除成功", data={})
