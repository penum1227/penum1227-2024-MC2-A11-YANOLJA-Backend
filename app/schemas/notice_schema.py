from pydantic import BaseModel
from typing import List

class Notice(BaseModel):
    date: str
    notice_name: str
    notice_comment: str

class NoticeListResponse(BaseModel):
    notices: List[Notice]

