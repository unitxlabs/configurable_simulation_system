from fastapi import APIRouter, Depends, HTTPException
import requests
from backend.api.v1.schemas import ControllerListResponse, CommonResponse
from backend.logger import Logger

controllerRouter = APIRouter()


@controllerRouter.get("/list", response_model=CommonResponse)
def get_controller_list():
    url = "http://localhost:10001/perception/api/v1/hardware/all_cameras_controllers_mapping"

    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果状态码不是200，会抛出异常
        data = response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="端口未开或无法连接到服务")
    # 获取映射数据
    mapping = data.get("mapping", {})
    occupied_cameras = data.get("occupied_cameras", {})

    controller_list = []

    for camera_id, camera_info in mapping.items():
        print(camera_id, camera_info)
        # 获取 max_width 和 max_height
        max_width = camera_info.get("max_width", 0)
        max_height = camera_info.get("max_height", 0)
        has_version = False
        # 遍历所有控制器类型
        for controller_type, data in camera_info.items():
            # 跳过 max_width 和 max_height，处理版本信息
            if controller_type in ["max_width", "max_height"]:
                continue

            # 如果 controller_type 是控制器ID（例如 "/dev/ttyS3"），并且 data 是版本列表
            if isinstance(data, list):  # 版本列表
                controller_id = controller_type  # 这里是控制器ID，例如 "/dev/ttyS3"
                versions = data
                has_version = True
                # 遍历所有版本
                for version in versions:
                    # 检查该控制器是否已分配给相机
                    camera = next(
                        (
                            camera
                            for camera, controllers in occupied_cameras.items()
                            if controller_id in controllers
                        ),
                        None,
                    )

                    is_active = camera is not None
                    camera_ratio = f"{max_width} X {max_height}"

                    controller_list.append(
                        ControllerListResponse(
                            isActive=is_active,
                            controllerId=controller_id,  # 这里是控制器ID，例如 "/dev/ttyS3"
                            controllerVersion=version,
                            camera=camera_id,
                            cameraRatio=camera_ratio,
                        )
                    )
        if not has_version:
            # 默认处理没有版本的控制器
            camera = next(
                (
                    camera
                    for camera, controllers in occupied_cameras.items()
                    if camera_id in controllers
                ),
                None,
            )
            is_active = camera is not None
            camera_ratio = f"{max_width} X {max_height}"

            # 添加没有版本的控制器条目
            controller_list.append(
                ControllerListResponse(
                    isActive=is_active,
                    controllerId="",  # 这里是控制器ID，例如 "/dev/ttyS3"
                    controllerVersion="",
                    camera=camera_id,
                    cameraRatio=camera_ratio,
                )
            )

    return CommonResponse(msg="", data=controller_list)


@controllerRouter.post("/save")
async def save():
    Logger.log_action("创建了新控制器配置:")
    return CommonResponse(msg="创建成功", data={})


# @router.get("/", response_model=list[ControllerListResponse])
# def get_controller_list(name: str = None, db: Session = Depends(get_db)):
#     filters = {"name": name} if name else {}
#     return db.query_data("ipc_config", filters)
