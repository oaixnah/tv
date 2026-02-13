from datetime import datetime

import requests

from epg.common import save_epg_file
from epg.models import Data, Channel, Programme

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


def get_epg(channel_name: str, date: str):
    try:
        req = requests.get(
            f"https://api.erw.cc/?ch={channel_name}&date={date}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            }
        )
        return req.json()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def get_data(date: str):
    data = Data(data_from='https://api.erw.cc/')
    for channel_name in CHANNEL_NAMES:
        epg = get_epg(channel_name, date)
        if epg is None:
            continue
        data.channels.append(Channel(id=channel_name, display_name=channel_name))
        for item in epg["epg_data"]:
            data.programmes.append(Programme(
                channel=channel_name,
                start=f'{date}{item["start"].replace(":", "")}00 +0800',
                stop=f'{date}{item["end"].replace(":", "")}00 +0800',
                title=item["title"],
            ))
    return data


if __name__ == '__main__':
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")  # 20260312
    epg_data = get_data(date_str)
    save_epg_file(epg_data)
