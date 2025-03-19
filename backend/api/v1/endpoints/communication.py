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


@communicationRouter.get("/data", response_model=CommonResponse)
def get_communication_data(
    communication_type: int = Query(1, description=""),
    part_type: Optional[str] = Query(None, description=""),
    part_interval: Optional[int] = Query(None, description=""),
):
    data_dict = {}
    if communication_type:
        data_dict["communication_type"] = communication_type
    if part_type:
        data_dict["part_type"] = part_type
    if part_interval:
        data_dict["part_interval"] = part_interval
    data = db_instance.query_data(
        table_name="communication_config", data_dict=data_dict
    )
    return CommonResponse(msg="获取成功", data=data)


@communicationRouter.post("/save", response_model=CommonResponse)
async def save(data: CommunicationSaveSettingsData):
    print(f"创建通讯:{data}")
    db_instance.add_data(table_name="communication_config", data_dict=data.dict())
    Logger.log_action(f"创建通讯:{data}")
    return CommonResponse(msg="创建成功", data={})


@communicationRouter.post("/update", response_model=CommonResponse)
async def update(data: CommunicationUpdateSettingsData):
    db_instance.update_data(table_name="communication_config", data_dict=data.dict())
    Logger.log_action(f"修改通讯:{data}")
    return CommonResponse(msg="修改成功", data={})


@communicationRouter.post("/delete", response_model=CommonResponse)
async def delete_communication_data(
    id: Optional[int] = None,
    communication_id: Optional[int] = None,
):
    if id is None or communication_id is None:
        raise HTTPException(
            status_code=400, detail="Both 'id' and 'communication_id' must be provided."
        )

    db_instance.delete_data(table_name="communication_config", data_id=id)
    Logger.log_action(f"删除通讯ID为{id},communication_id为{communication_id}的通讯:")
    return CommonResponse(msg="删除成功", data={})
