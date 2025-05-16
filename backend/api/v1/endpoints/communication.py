from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.v1.schemas import (
    CommonResponse,
    CommunicationSaveSettingsData,
    CommunicationUpdateSettingsData,
)
from backend.logger import Logger
from typing import List
from backend.database import db_instance
from typing import Optional

communicationRouter = APIRouter()

global_communication_data = {}


@communicationRouter.get("/data", response_model=CommonResponse)
def get_communication_data(
    communication_type: int = Query(2, description=""),
    part_type: Optional[str] = Query(None, description=""),
    part_interval: Optional[int] = Query(None, description=""),
):
    data_dict = {}
    data_dict["communication_type"] = communication_type
    if part_type:
        data_dict["part_type"] = part_type
    if part_interval:
        data_dict["part_interval"] = part_interval
    data = db_instance.query_data(
        table_name="communication_config", data_dict=data_dict
    )
    result = []
    for comm_config in data:
        result.append(comm_config.get("communication_config"))
    return CommonResponse(msg="获取成功", data=result)


@communicationRouter.post("/save", response_model=CommonResponse)
async def save(data: CommunicationSaveSettingsData):
    print(f"创建通讯:{data}")
    db_instance.add_data(table_name="communication_config", data_dict=data.dict())
    Logger.log_action(f"创建通讯:{data.dict()}")
    return CommonResponse(msg="创建成功", data={})


@communicationRouter.post("/update", response_model=CommonResponse)
async def update(data: CommunicationUpdateSettingsData):
    db_instance.update_data(table_name="communication_config", data_dict=data.dict())
    Logger.log_action(f"修改通讯:{data}")
    return CommonResponse(msg="修改成功", data={})


@communicationRouter.post("/delete", response_model=CommonResponse)
async def delete_communication_data(
    id: Optional[int] = None,
    communication_type: Optional[int] = None,
):
    if id is None or communication_type is None:
        raise HTTPException(
            status_code=400,
            detail="Both 'id' and 'communication_type' must be provided.",
        )

    db_instance.delete_data(table_name="communication_config", data_id=id)
    Logger.log_action(f"删除通讯ID为{id},communication_type{communication_type}的通讯")
    return CommonResponse(msg="删除成功", data={})


@communicationRouter.post("/apply", response_model=CommonResponse)
async def apply(data: CommunicationUpdateSettingsData):
    if data.id <= 0:
        id = db_instance.add_data(
            table_name="communication_config", data_dict=data.dict()
        )
        if id is None:
            raise HTTPException(
                status_code=400,
                detail="应用失败.",
            )
        data.id = id
    global global_communication_data
    data_dict = {}
    data_dict["id"] = data.id
    dbData = db_instance.query_data(
        table_name="communication_config", data_dict=data_dict
    )
    if dbData:
        global_communication_data = dbData[0]
        Logger.log_action(f"应用通讯:{dbData[0]}")
    return CommonResponse(msg="应用通成功", data={})


@communicationRouter.get("/applied_data", response_model=CommonResponse)
async def get_applied_data():
    return CommonResponse(msg="获取成功", data=global_communication_data)
