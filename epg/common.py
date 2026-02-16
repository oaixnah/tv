"""EPG 数据保存模块。

该模块提供将 EPG 数据保存为 XML 文件的功能，遵循 XMLTV 格式标准。
"""

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

from epg.models import Data


def save_epg_file(epg_data: Data, mode: str = 'w') -> None:
    """将 EPG 数据保存为 XML 文件。

    该函数将 EPG 数据转换为符合 XMLTV 格式的 XML 文件，并进行格式化输出。

    Args:
        epg_data: EPG 数据对象，包含频道和节目信息
        mode: 文件打开模式，默认为 'w'（写入模式）

    Returns:
        None

    Example:
        >>> data = Data(data_from="test", channels=[...], programmes=[...])
        >>> save_epg_file(data)
    """
    # 创建根元素 tv
    tv = ET.Element("tv")

    # 添加 tv 元素的属性
    tv.set("info-name", epg_data.info_name)
    tv.set("info-url", epg_data.info_url)
    tv.set('data-from', epg_data.data_from)

    # 添加频道信息
    for channel in epg_data.channels:
        chan_elem = ET.SubElement(tv, "channel")
        chan_elem.set("id", channel.id)

        display = ET.SubElement(chan_elem, "display-name")
        display.set("lang", "zh")
        display.text = channel.display_name

    # 添加节目信息
    for prog in epg_data.programmes:
        prog_elem = ET.SubElement(tv, "programme")
        prog_elem.set("channel", prog.channel)
        prog_elem.set("start", prog.start)
        prog_elem.set("stop", prog.stop)

        title = ET.SubElement(prog_elem, "title")
        title.set("lang", "zh")
        title.text = prog.title

    # 将 XML 树转换为字符串
    xml_str = ET.tostring(tv, encoding='utf-8')

    # 使用 minidom 美化 XML 输出
    dom = parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="\t")

    # 将美化后的 XML 写入文件
    with open("e.xml", mode, encoding="UTF-8") as f:
        f.write(pretty_xml)
