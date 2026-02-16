"""EPG (Electronic Program Guide) 数据抓取模块

该模块通过调用 erw.cc 的 API 接口，获取指定日期的电视频道节目信息，
并将数据转换为符合 XMLTV 标准的 EPG XML 格式文件。

主要功能：
- 从 erw.cc API 获取电视节目指南数据
- 支持 70+ 个主流电视频道
- 将数据转换为标准 XMLTV 格式
- 自动处理时区信息（东八区）

使用示例：
    $ python main.py
    # 生成当天的 EPG 数据文件 e.xml

模块结构：
- get_epg(): 获取单个频道的 EPG 数据
- get_data(): 获取所有频道数据并转换为标准格式
- 主程序：生成当天的 EPG 文件

注意事项：
- API 请求有超时限制（3秒）
- 使用模拟浏览器 User-Agent 避免被拦截
- 数据源时区为东八区（北京时间）

Attributes:
    CHANNEL_NAMES: 支持的电视频道名称列表，包含央视、卫视等主流频道
"""

import logging
from datetime import datetime

import requests

from epg.common import save_epg_file
from epg.models import Data, Channel, Programme

logger = logging.getLogger(__name__)

# 支持的电视频道名称列表，用于从 API 获取节目数据
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
    """从 erw.cc API 获取指定频道和日期的 EPG 数据。
    
    该函数通过 HTTP GET 请求调用 erw.cc API，获取指定频道在指定日期的
    电视节目指南数据。API 返回 JSON 格式的数据，包含节目时间、标题等信息。

    Args:
        channel_name: 频道名称，必须是 CHANNEL_NAMES 中定义的频道，如 'CCTV1'
        date: 日期字符串，格式为 'YYYYMMDD'，如 '20240216'

    Returns:
        dict | None: 包含节目数据的字典，结构为：
            {
                'epg_data': [
                    {
                        'start': 'HH:MM',  # 节目开始时间
                        'end': 'HH:MM',    # 节目结束时间
                        'title': '节目名称' # 节目标题
                    }
                ]
            }
        如果请求失败（网络错误、超时等）则返回 None

    Raises:
        requests.RequestException: 网络请求异常（连接错误、超时等）
        
    Note:
        - 请求超时设置为 3 秒
        - 使用模拟浏览器 User-Agent 避免被 API 拦截
        - 如果频道不存在或日期无效，API 可能返回空数据或错误
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


def get_data(date_str: str) -> Data:
    """获取所有频道的 EPG 数据并转换为标准 XMLTV 格式。

    该函数遍历 CHANNEL_NAMES 中定义的所有电视频道，为每个频道调用
    get_epg() 函数获取节目数据，然后将原始数据转换为符合 XMLTV 标准
    的 Data 对象。

    Args:
        date_str: 日期字符串，格式为 'YYYYMMDD'，如 '20240216'

    Returns:
        Data: 包含所有频道和节目数据的 Data 对象，结构包括：
            - data_from: 数据来源标识
            - channels: 频道列表（Channel 对象）
            - programmes: 节目列表（Programme 对象）

    Note:
        - 如果某个频道的 API 请求失败，会跳过该频道继续处理其他频道
        - 时间格式会转换为 XMLTV 标准格式：YYYYMMDDHHMMSS +0000
        - 时区固定为东八区（+0800）
        - 频道 ID 和显示名称使用相同的频道名称
    """
    data = Data(data_from='https://api.erw.cc/')

    # 遍历所有频道，获取每个频道的节目数据
    for channel_name in CHANNEL_NAMES:
        epg = get_epg(channel_name, date_str)
        if epg is None:
            continue

        # 添加频道信息
        data.channels.append(Channel(id=channel_name, display_name=channel_name))

        # 添加节目信息
        for item in epg["epg_data"]:
            data.programmes.append(Programme(
                channel=channel_name,
                start=f'{date_str}{item["start"].replace(":", "")}00 +0800',
                stop=f'{date_str}{item["end"].replace(":", "")}00 +0800',
                title=item["title"],
            ))
    return data


if __name__ == '__main__':
    """主程序入口：生成当天的 EPG 数据文件。
    
    执行流程：
    1. 获取当前日期
    2. 调用 get_data() 获取所有频道的 EPG 数据
    3. 将数据保存为 XML 文件（默认文件名：e.xml）
    
    输出文件：
        e.xml - 符合 XMLTV 标准的 EPG 数据文件
    """
    # 获取当前日期，格式化为 YYYYMMDD
    today = datetime.now()

    # 获取所有频道的 EPG 数据
    epg_data = get_data(today.strftime("%Y%m%d"))

    # 将数据保存为 XML 文件
    save_epg_file(epg_data)
