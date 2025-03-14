from pydantic import BaseModel
from typing import Union


class CommonResponse(BaseModel):
    msg: str
    data: Union[list, dict, str, int, float]
