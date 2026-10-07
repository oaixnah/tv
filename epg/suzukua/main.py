"""EPG (Electronic Program Guide) 数据抓取模块

该模块通过下载 suzukua/epg 项目提供的 t.xml 文件，获取 XMLTV 格式的
电视节目指南数据，并筛选出所需的电视频道与日期范围，转换为标准
Data 对象后保存为 EPG XML 文件。

主要功能：
- 从 GitHub 下载 t.xml 获取电视节目指南数据
- 仅保留 epg.channel.NAMES 中定义的频道（支持别名映射）
- 仅保留今明两天的节目
- 自动处理时区信息（东八区）

使用示例：
    $ python -m epg.suzukua.main
    # 生成今明两天的 EPG 数据文件 e.xml

模块结构：
- get_epg(): 下载并解析 t.xml 数据
- get_data(): 筛选频道与日期并转换为标准格式
- 主程序：生成今明两天的 EPG 文件

Attributes:
    URL: t.xml 数据源地址
    ALIASES: 源文件频道 ID 与标准频道名称的别名映射
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from epg.channel import NAMES
from epg.common import save_epg_file
from epg.models import Data, Channel, Programme

logger = logging.getLogger(__name__)

# t.xml 数据源地址
URL = 'https://raw.githubusercontent.com/suzukua/epg/refs/heads/hidden/t.xml'

# 源文件频道 ID 与标准频道名称的别名映射
ALIASES = {
    'CCTV4K': 'CCTV4K超高清',
}


def get_epg() -> ET.Element | None:
    """下载并解析 t.xml 数据。

    通过 HTTP GET 请求下载 suzukua/epg 项目的 t.xml 文件，该文件为
    符合 XMLTV 标准的 XML，包含所有频道的节目信息。

    Returns:
        ET.Element | None: XML 根节点（tv 元素），
        如果请求或解析失败则返回 None

    Note:
        - 请求超时设置为 30 秒
        - 使用模拟浏览器 User-Agent 避免被拦截
    """
    try:
        req = requests.get(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            },
            timeout=30,
        )
        req.raise_for_status()
        return ET.fromstring(req.content)
    except (requests.RequestException, ET.ParseError) as e:
        logger.error(f"Request failed: {e}")
        return None


def get_data() -> Data:
    """获取今明两天的 EPG 数据并转换为标准 XMLTV 格式。

    下载 t.xml 后，筛选出 NAMES 中定义频道的节目数据，
    仅保留今天和明天（东八区）的节目，并转换为 Data 对象。

    Returns:
        Data: 包含频道和节目数据的 Data 对象，结构包括：
            - data_from: 数据来源标识
            - channels: 频道列表（Channel 对象）
            - programmes: 节目列表（Programme 对象）

    Note:
        - 源文件中存在重复的频道定义，输出时会去重
        - 频道 ID 和显示名称使用相同的频道名称
        - 时区固定为东八区（+0800）
    """
    data = Data(data_from=URL)

    root = get_epg()
    if root is None:
        return data

    # 计算今明两天的日期（东八区）
    today = datetime.now(ZoneInfo("Asia/Shanghai"))
    dates = {
        (today + timedelta(days=offset)).strftime('%Y%m%d')
        for offset in (0, 1)
    }

    names = set(NAMES)

    # 添加频道信息，源文件中存在重复定义，需要去重
    seen: set[str] = set()
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        channel_name = channel_id if channel_id in names else ALIASES.get(channel_id or '')
        if channel_name is None or channel_name in seen:
            continue
        seen.add(channel_name)
        data.channels.append(Channel(id=channel_name, display_name=channel_name))

    # 添加今明两天的节目信息
    for item in root.findall('programme'):
        channel_id = item.get('channel')
        channel_name = channel_id if channel_id in names else ALIASES.get(channel_id or '')
        if channel_name is None or channel_name not in seen:
            continue

        start = item.get('start', '')
        if start[:8] not in dates:
            continue

        title = item.find('title')
        data.programmes.append(Programme(
            channel=channel_name,
            start=start,
            stop=item.get('stop', ''),
            title=title.text or '',
        ))
    return data


if __name__ == '__main__':
    """主程序入口：生成今明两天的 EPG 数据文件。

    执行流程：
    1. 下载并解析 t.xml 数据
    2. 筛选 NAMES 频道及今明两天的节目
    3. 将数据保存为 XML 文件（默认文件名：e.xml）
    """
    save_epg_file(get_data())
