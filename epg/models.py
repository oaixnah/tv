from pydantic import BaseModel


class Channel(BaseModel):
    id: str  # CCTV1
    display_name: str  # CCTV1


class Programme(BaseModel):
    channel: str  # CCTV1
    start: str  # 20260213045300 +0800
    stop: str  # 20260213052700 +0800
    title: str  # 新闻联播


class Data(BaseModel):
    info_name: str = "by oaixnah"
    info_url: str = "https://tv.oaix.tech/e.xml"
    data_from: str
    channels: list[Channel] = []
    programmes: list[Programme] = []
