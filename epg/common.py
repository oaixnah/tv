import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

from epg.models import Data


def save_epg_file(epg_data: Data):
    tv = ET.Element("tv")

    # 添加 tv 元素的属性
    tv.set("info-name", epg_data.info_name)
    tv.set("info-url", epg_data.info_url)
    tv.set('data-from', epg_data.data_from)

    # 添加频道
    for channel in epg_data.channels:
        chan_elem = ET.SubElement(tv, "channel")
        chan_elem.set("id", channel.id)

        display = ET.SubElement(chan_elem, "display-name")
        display.set("lang", "zh")
        display.text = channel.display_name

    # 添加节目
    for prog in epg_data.programmes:
        prog_elem = ET.SubElement(tv, "programme")
        prog_elem.set("channel", prog.channel)
        prog_elem.set("start", prog.start)
        prog_elem.set("stop", prog.stop)

        title = ET.SubElement(prog_elem, "title")
        title.set("lang", "zh")
        title.text = prog.title

    # 转换为字符串并美化
    xml_str = ET.tostring(tv, encoding='utf-8')

    dom = parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="\t")
    with open("e.xml", "w", encoding="UTF-8") as f:
        f.write(pretty_xml)
