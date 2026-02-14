"""EPG数据抓取模块，从erw.cc API获取电视节目指南数据。

该模块通过调用erw.cc的API接口，获取指定日期的电视频道节目信息，
并将数据转换为标准的EPG XML格式文件。

Example:
    $ python main.py
    # 生成当天的EPG数据文件e.xml

Attributes:
    CHANNEL_NAMES: 支持的电视频道名称列表
"""

import logging
from datetime import datetime

import requests

from epg.common import save_epg_file
from epg.models import Data, Channel, Programme

logger = logging.getLogger(__name__)

# 支持的电视频道名称列表，用于从API获取节目数据
CHANNEL_NAMES = (
    'CCTV1',
    'CCTV2',
    'CCTV3',
    'CCTV4',
    'CCTV5',
    'CCTV5+',
    'CCTV6',
    'CCTV7',
    'CCTV8',
    'CCTV9',
    'CCTV10',
    'CCTV11',
    'CCTV12',
    'CCTV13',
    'CCTV14',
    'CCTV15',
    'CCTV16',
    'CCTV17',
    '风云音乐',
    '第一剧场',
    '风云剧场',
    '风云足球',
    '世界地理',
    '电视指南',
    '怀旧剧场',
    '兵器科技',
    'CCTV4K超高清',
    'CHC动作电影',
    'CHC家庭影院',
    'CHC影迷电影',
    '辽宁公共',
    '辽宁北方',
    '辽宁生活',
    '辽宁经济',
    '辽宁都市',
    '辽宁影视剧',
    '辽宁体育休闲',
    '深圳卫视',
    '重庆卫视',
    '广东卫视',
    '北京卫视',
    '湖南卫视',
    '东方卫视',
    '四川卫视',
    '天津卫视',
    '安徽卫视',
    '山东卫视',
    '广西卫视',
    '江苏卫视',
    '江西卫视',
    '河北卫视',
    '河南卫视',
    '浙江卫视',
    '海南卫视',
    '湖北卫视',
    '东南卫视',
    '贵州卫视',
    '云南卫视',
    '辽宁卫视',
    '黑龙江卫视',
    '吉林卫视',
    '宁夏卫视',
    '新疆卫视',
    '兵团卫视',
    '甘肃卫视',
    '内蒙古卫视',
    '青海卫视',
    '三沙卫视',
    '厦门卫视',
    '陕西卫视',
)


def get_epg(channel_name: str, date: str) -> dict | None:
    """从erw.cc API获取指定频道和日期的EPG数据。

    Args:
        channel_name: 频道名称，如 'CCTV1'
        date: 日期字符串，格式为 'YYYYMMDD'

    Returns:
        包含节目数据的字典，如果请求失败则返回None

    Raises:
        requests.RequestException: 网络请求异常
    """
    try:
        req = requests.get(
            f"https://api.erw.cc/?ch={channel_name}&date={date}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            },
            timeout=3,
        )
        return req.json()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None


def get_data(date: str) -> Data:
    """获取所有频道的EPG数据并转换为标准格式。

    遍历所有支持的电视频道，调用API获取节目数据，
    并将数据转换为标准的EPG数据模型。

    Args:
        date: 日期字符串，格式为 'YYYYMMDD'

    Returns:
        包含所有频道和节目数据的Data对象
    """
    data = Data(data_from='https://api.erw.cc/')

    # 遍历所有频道，获取每个频道的节目数据
    for channel_name in CHANNEL_NAMES:
        epg = get_epg(channel_name, date)
        if epg is None:
            continue

        # 添加频道信息
        data.channels.append(Channel(id=channel_name, display_name=channel_name))

        # 添加节目信息
        for item in epg["epg_data"]:
            data.programmes.append(Programme(
                channel=channel_name,
                start=f'{date}{item["start"].replace(":", "")}00 +0800',
                stop=f'{date}{item["end"].replace(":", "")}00 +0800',
                title=item["title"],
            ))
    return data


if __name__ == '__main__':
    """主函数入口，生成当天的EPG数据文件。"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")  # 格式：20260312
    epg_data = get_data(date_str)
    save_epg_file(epg_data)
