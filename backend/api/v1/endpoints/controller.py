from fastapi import APIRouter, Depends, HTTPException, Query
import requests
from backend.api.v1.schemas import (
    ControllerListResponse,
    CommonResponse,
    ControllerSettingsData,
)
from backend.logger import Logger
from backend.image_count_util import ImageCountUtil
from typing import List
from backend.database import db_instance
from typing import Optional

from pathlib import Path

controllerRouter = APIRouter()


@controllerRouter.get("/list", response_model=CommonResponse)
def get_controller_list():
    url = (
        "http://localhost:10001/perception/api/v1/hardware/all_cameras_controllers_info"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果状态码不是200，会抛出异常
        data = response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="端口未开或无法连接到服务")
    # 获取映射数据
    mapping = data.get("mapping", {})

    controller_list = []

    for camera_id, camera_info in mapping.items():
        # 获取 max_width 和 max_height
        max_width = camera_info.get("max_width", 0)
        max_height = camera_info.get("max_height", 0)
        channel = camera_info.get("channel", 3)
        model = camera_info.get("model", "")
        has_version = False
        # 遍历所有控制器类型
        for controller_type, data in camera_info.items():
            # 跳过 max_width 和 max_height，处理版本信息
            if controller_type in ["max_width", "max_height", "channel", "model"]:
                continue

            # 如果 controller_type 是控制器ID（例如 "/dev/ttyS3"），并且 data 是版本列表
            if isinstance(data, list):  # 版本列表
                controller_id = controller_type  # 这里是控制器ID，例如 "/dev/ttyS3"
                result = next(
                    (
                        item
                        for item in data
                        if item.startswith("V") and item[1:].isdigit()
                    ),
                    None,
                )
                if result:
                    has_version = True
                    capture_images_count, networks_inference_count = (
                        ImageCountUtil.get_controller_pic_all_count(controller_id)
                    )
                    controller_list.append(
                        ControllerListResponse(
                            controller_id=controller_id,  # 这里是控制器ID，例如 "/dev/ttyS3"
                            controller_version=result,
                            cameras_id=[camera_id],
                            image_width=max_width,
                            image_height=max_height,
                            image_channel=channel,
                            cameras_type=[model],
                            capture_images_count=capture_images_count,
                            network_inference_count=networks_inference_count,
                            isActive=True,
                        )
                    )
        if not has_version:
            # 添加没有版本的控制器条目
            controller_list.append(
                ControllerListResponse(
                    controller_id="",  # 这里是控制器ID，例如 "/dev/ttyS3"
                    controller_version="",
                    cameras_id=[camera_id],
                    image_width=max_width,
                    image_height=max_height,
                    image_channel=channel,
                    cameras_type=[model],
                    capture_images_count=0,
                    network_inference_count=0,
                    isActive=True,
                )
            )

    return CommonResponse(msg="", data=controller_list)


@controllerRouter.get("/data", response_model=CommonResponse)
def get_controller_data(
    controller_id: Optional[str] = Query(None, description=""),
    controller_version: Optional[str] = Query(None, description=""),
    cameras_id: Optional[str] = Query(None, description=""),
):
    data_dict = {}
    if controller_id:
        data_dict["controller_id"] = controller_id
    if controller_version:
        data_dict["controller_version"] = controller_version
    if cameras_id:
        data_dict["cameras_id"] = [cameras_id]
    data = db_instance.query_data(table_name="controller_config", data_dict=data_dict)
    print(data)
    return CommonResponse(msg="获取成功", data=data)


@controllerRouter.post("/save", response_model=CommonResponse)
async def save(data: List[ControllerSettingsData] = []):
    data_dicts = [item.dict() for item in data]
    if data_dicts:
        # 遍历 data，逐个插入数据库
        for data_dict in data_dicts:
            new_data_id = db_instance.add_data(
                table_name="controller_config", data_dict=data_dict
            )
            if new_data_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="创建失败.",
                )
    Logger.log_action(f"创建控制器配置:{data_dicts}")
    return CommonResponse(msg="创建成功", data={})


@controllerRouter.post("/delete", response_model=CommonResponse)
def delete_controller_data(
    id: int = Query(None, description=""),
    controller_id: str = Query(None, description=""),
):
    if id is None or controller_id is None:
        raise HTTPException(
            status_code=400, detail="Both 'id' and 'controller_id' must be provided."
        )
    used = db_instance.is_controller_used(id)
    if used:
        return CommonResponse(msg="该控制器已被使用,无法删除", data={})
    db_instance.delete_data(table_name="controller_config", data_id=id)
    Logger.log_action(f"删除控制器ID为{id},controller_id为{controller_id}的配置:")
    return CommonResponse(msg="创建成功", data={})


@controllerRouter.get("/select", response_model=CommonResponse)
def get_controller_select_data(
    status: str = Query(None, description=""),
):
    dbData = db_instance.get_all_controller_ids()
    select_options = [
        {"label": f"{controller_id}", "value": controller_config_id}
        for controller_config_id, controller_id in dbData
    ]
    if status:
        url = "http://localhost:10001/perception/api/v1/hardware/all_cameras_controllers_mapping"

        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果状态码不是200，会抛出异常
            data = response.json()
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=503, detail="端口未开或无法连接到服务")
        # 获取映射数据
        mapping = data.get("mapping", {})
        valid_controller_types = {
            controller_type
            for camera_info in mapping.values()
            for controller_type in camera_info.keys()
        }
        select_options = [
            option
            for option in select_options
            if option["label"] in valid_controller_types
        ]
    #select_options = list({frozenset(option.items()): option for option in select_options}.values())
    return CommonResponse(msg="获取成功", data=select_options)


# @controllerRouter.get("/list", response_model=CommonResponse)
# def get_controller_list():
#     url = "http://localhost:10001/perception/api/v1/hardware/all_cameras_controllers_mapping"

#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # 如果状态码不是200，会抛出异常
#         data = response.json()
#     except requests.exceptions.RequestException:
#         raise HTTPException(status_code=503, detail="端口未开或无法连接到服务")
#     # 获取映射数据
#     mapping = data.get("mapping", {})
#     occupied_cameras = data.get("occupied_cameras", {})

#     controller_list = []

#     for camera_id, camera_info in mapping.items():
#         print(camera_id, camera_info)
#         # 获取 max_width 和 max_height
#         max_width = camera_info.get("max_width", 0)
#         max_height = camera_info.get("max_height", 0)
#         has_version = False
#         # 遍历所有控制器类型
#         for controller_type, data in camera_info.items():
#             # 跳过 max_width 和 max_height，处理版本信息
#             if controller_type in ["max_width", "max_height"]:
#                 continue

#             # 如果 controller_type 是控制器ID（例如 "/dev/ttyS3"），并且 data 是版本列表
#             if isinstance(data, list):  # 版本列表
#                 controller_id = controller_type  # 这里是控制器ID，例如 "/dev/ttyS3"
#                 versions = data
#                 has_version = True
#                 # 遍历所有版本
#                 for version in versions:
#                     # 检查该控制器是否已分配给相机
#                     camera = next(
#                         (
#                             camera
#                             for camera, controllers in occupied_cameras.items()
#                             if controller_id in controllers
#                         ),
#                         None,
#                     )

#                     is_active = camera is not None
#                     camera_ratio = f"{max_width} X {max_height}"

#                     controller_list.append(
#                         ControllerListResponse(
#                             isActive=is_active,
#                             controllerId=controller_id,  # 这里是控制器ID，例如 "/dev/ttyS3"
#                             controllerVersion=version,
#                             camera=camera_id,
#                             cameraRatio=camera_ratio,
#                         )
#                     )
#         if not has_version:
#             # 默认处理没有版本的控制器
#             camera = next(
#                 (
#                     camera
#                     for camera, controllers in occupied_cameras.items()
#                     if camera_id in controllers
#                 ),
#                 None,
#             )
#             is_active = camera is not None
#             camera_ratio = f"{max_width} X {max_height}"

#             # 添加没有版本的控制器条目
#             controller_list.append(
#                 ControllerListResponse(
#                     isActive=is_active,
#                     controllerId="",  # 这里是控制器ID，例如 "/dev/ttyS3"
#                     controllerVersion="",
#                     camera=camera_id,
#                     cameraRatio=camera_ratio,
#                 )
#             )

#     return CommonResponse(msg="", data=controller_list)


# @router.get("/", response_model=list[ControllerListResponse])
# def get_controller_list(name: str = None, db: Session = Depends(get_db)):
#     filters = {"name": name} if name else {}
#     return db.query_data("ipc_config", filters)
