from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.v1.schemas import (
    CommonResponse,
    WorkstationSaveSettingsData,
    WorkstationUpdateSettingsData,
)
from backend.logger import Logger
from typing import List
from backend.database import db_instance
from typing import Optional

workstationRouter = APIRouter()


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
    new_data_id = db_instance.add_data(
        table_name="workstation_config", data_dict=data.dict()
    )
    if new_data_id is None:
        raise HTTPException(
            status_code=400,
            detail="创建失败.",
        )
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
