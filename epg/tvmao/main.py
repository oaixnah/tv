"""TVMao EPG数据抓取模块。

该模块用于从TVMao网站抓取电视节目指南(EPG)数据，支持多个电视频道。
使用Playwright进行网页自动化，能够处理动态加载的内容。
"""

import asyncio
import logging
import re
from datetime import datetime

from playwright.async_api import async_playwright

from epg.common import save_epg_file
from epg.models import Data, Channel, Programme

logger = logging.getLogger(__name__)

# 频道配置字典，包含所有支持的频道及其对应的TVMao ID
# 格式：{'页面类型': (('频道显示名称', 'TVMao频道ID'), ...)}
CHANNELS = {
    # 普通节目页面类型
    'program': (
        # 中央电视台
        ('CCTV1', 'CCTV-CCTV1'),
        ('CCTV2', 'CCTV-CCTV2'),
        ('CCTV3', 'CCTV-CCTV3'),
        ('CCTV4', 'CCTV-CCTV4'),
        ('CCTV5', 'CCTV-CCTV5'),
        ('CCTV5+', 'CCTV-CCTV5-PLUS'),
        ('CCTV6', 'CCTV-CCTV6'),
        ('CCTV7', 'CCTV-CCTV7'),
        ('CCTV8', 'CCTV-CCTV8'),
        ('CCTV9', 'CCTV-CCTV9'),
        ('CCTV10', 'CCTV-CCTV10'),
        ('CCTV11', 'CCTV-CCTV11'),
        ('CCTV12', 'CCTV-CCTV12'),
        ('CCTV13', 'CCTV-CCTV13'),
        ('CCTV14', 'CCTV-CCTV15'),
        ('CCTV15', 'CCTV-CCTV16'),
        ('CCTV16', 'CCTV-CCTVOLY'),
        ('CCTV17', 'CCTV-CCTV17NY'),
        # 中数传媒付费频道
        ('风云音乐', 'CCTVPAYFEE-CCTVPAYFEE2'),
        ('第一剧场', 'CCTVPAYFEE-CCTVPAYFEE3'),
        ('风云剧场', 'CCTVPAYFEE-CCTVPAYFEE4'),
        ('风云足球', 'CCTVPAYFEE-CCTVPAYFEE1'),
        ('世界地理', 'CCTVPAYFEE-CCTVPAYFEE5'),
        ('电视指南', 'CCTVPAYFEE-CCTVPAYFEE6'),
        ('怀旧剧场', 'CCTVPAYFEE-CCTVPAYFEE7'),
        ('兵器科技', 'CCTVPAYFEE-CCTVPAYFEE8'),
        ('CCTV4K超高清', 'CCTVPAYFEE-CCTV4K'),
        # CHC华诚付费频道
        ('CHC动作电影', 'CHC-CHC1'),
        ('CHC家庭影院', 'CHC-CHC2'),
        ('CHC影迷电影', 'CHC-CHC3'),
        # 辽宁电视台
        ('辽宁公共', 'LNTV-LNTV7'),
        ('辽宁北方', 'LNTV-LNTV8'),
        ('辽宁生活', 'LNTV-LNTV6'),
        ('辽宁经济', 'LNTV-LNTV-FINANCE'),
        ('辽宁都市', 'LNTV-LNTV2'),
        ('辽宁影视剧', 'LNTV-LNTV3'),
        ('辽宁体育休闲', 'LNTV-LNTV-SPORT'),
    ),
    # 卫星节目页面类型
    'program_satellite': (
        # 各省级卫视
        ('深圳卫视', 'SZTV1'),
        ('重庆卫视', 'CCQTV1'),
        ('广东卫视', 'GDTV1'),
        ('北京卫视', 'BTV1'),
        ('湖南卫视', 'HUNANTV1'),
        ('东方卫视', 'DONGFANG1'),
        ('四川卫视', 'SCTV1'),
        ('天津卫视', 'TJTV1'),
        ('安徽卫视', 'AHTV1'),
        ('山东卫视', 'SDTV1'),
        ('广西卫视', 'GUANXI1'),
        ('江苏卫视', 'JSTV1'),
        ('江西卫视', 'JXTV1'),
        ('河北卫视', 'HEBEI1'),
        ('河南卫视', 'HNTV1'),
        ('浙江卫视', 'ZJTV1'),
        ('海南卫视', 'TCTC1'),
        ('湖北卫视', 'HUBEI1'),
        ('东南卫视', 'FJTV2'),
        ('贵州卫视', 'GUIZOUTV1'),
        ('云南卫视', 'YNTV1'),
        ('辽宁卫视', 'LNTV1'),
        ('黑龙江卫视', 'HLJTV1'),
        ('吉林卫视', 'JILIN1'),
        ('宁夏卫视', 'NXTV2'),
        ('新疆卫视', 'XJTV1'),
        ('兵团卫视', 'BINGTUAN'),
        ('甘肃卫视', 'GSTV1'),
        ('内蒙古卫视', 'NMGTV1'),
        # ('农林卫视', ''),  # 该频道暂无TVMao ID
        ('青海卫视', 'QHTV1'),
        ('三沙卫视', 'SANSHATV'),
        ('厦门卫视', 'XMTV5'),
        ('陕西卫视', 'SHXITV1'),
    )
}


async def scrape(channel_url: str):
    """抓取指定TVMao节目页面的EPG数据。
    
    该函数使用Playwright自动化浏览器，能够处理动态加载的内容，自动点击"查看更多"
    按钮以获取完整的节目列表，然后解析页面中的节目信息。
    
    Args:
        channel_url: TVMao频道节目页面的URL
        
    Returns:
        包含节目时间与标题的字典列表，格式为[{"time": "HH:MM", "title": "..."}]
        
    Raises:
        Exception: 当浏览器操作或页面解析出现错误时抛出
    """
    async with async_playwright() as p:
        # 启动Chromium浏览器（无头模式）
        browser = await p.chromium.launch(headless=True)
        # 设置用户代理和语言环境，提升兼容性并避免反爬虫检测
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        page = await context.new_page()
        # 打开目标页面并等待主体元素渲染完成
        await page.goto(channel_url, timeout=60000)
        await page.wait_for_selector("body")
        # 尝试点击最多10次"查看更多"按钮，直到按钮不再出现
        for _ in range(10):
            locator = page.get_by_text("查看更多")
            count = await locator.count()
            if count == 0:
                break
            elt = locator.first
            try:
                # 确保按钮在视口内后再点击，避免点击失败
                await elt.scroll_into_view_if_needed()
                await elt.click()
                # 等待网络空闲状态，配合短暂休眠确保内容加载完成
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3.0)
            except Exception as e:
                logger.error(f"点击'查看更多'按钮时出错: {e}")
                break
        items = []
        # 遍历页面中的所有li元素，提取时间与标题信息
        lis = await page.locator("li").all()
        for li in lis:
            # 获取li元素的文本内容并进行规范化处理
            t = await li.inner_text()
            s = re.sub(r"\s+", " ", t).strip()

            # 使用正则表达式匹配时间格式（HH:MM）和节目标题
            m = re.match(r"^(\d{1,2}:\d{2})\s*(.*)$", s)
            if not m:
                continue

            time_str = m.group(1)
            rest = m.group(2).strip()

            # 当li文本不含标题时，尝试从子元素收集文本并拼接
            if not rest:
                texts = await li.locator("a, span, em").all_text_contents()
                texts = [x.strip() for x in texts]
                texts = [x for x in texts if not re.fullmatch(r"\d{1,2}:\d{2}", x)]
                rest = re.sub(r"\s+", " ", " ".join(texts)).strip()

            # 去除"正在播出"等常见标记词，保留纯节目标题
            title = re.sub(r"(正在播出)", "", rest).strip()
            if not title:
                continue

            # 将解析出的节目信息添加到结果列表
            items.append({"time": time_str, "title": title})

        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()
        return items


def get_epg_data():
    """获取所有频道的EPG数据。
    
    该函数遍历所有配置的频道，为每个频道生成对应的TVMao URL，调用scrape函数抓取数据，
    并将抓取到的节目信息转换为标准的EPG格式。
    
    Returns:
        Data: 包含所有频道和节目信息的EPG数据对象
    """
    result = Data()
    # 获取当前日期和星期几信息
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    weekday = today.weekday() + 1  # TVMao使用1-7表示周一到周日

    # 遍历所有频道配置
    for _type, channels in CHANNELS.items():
        for channel_name, channel_id in channels:
            # 构建TVMao节目页面URL，格式：https://www.tvmao.com/program/CCTV-CCTV1-w4.html
            url = f"https://www.tvmao.com/{_type}/{channel_id}-w{weekday}.html"
            logger.info(f"正在抓取频道 {channel_name} 的EPG数据: {url}")

            # 调用scrape函数抓取该频道的节目数据
            if epg_data := asyncio.run(scrape(url)):
                logger.info(f"频道 {channel_name} 抓取到 {len(epg_data)} 个节目")

                # 添加频道信息到结果中
                result.channels.append(Channel(
                    id=channel_name,
                    display_name=channel_name
                ))

                # 处理每个节目的时间信息
                for index, epg_item in enumerate(epg_data):
                    # 节目开始时间：日期 + 时间 + 时区
                    start_str = f"{date_str}{epg_item['time'].replace(':', '')}00 +0800"

                    # 节目结束时间：如果是最后一个节目，则结束时间为当天23:59:59
                    # 否则为下一个节目的开始时间
                    if index + 1 == len(epg_data):
                        stop_str = f"{date_str}235959 +0800"
                    else:
                        stop_str = f"{date_str}{epg_data[index + 1]['time'].replace(':', '')}00 +0800"

                    # 添加节目信息到结果中
                    result.programmes.append(Programme(
                        channel=channel_name,
                        start=start_str,
                        stop=stop_str,
                        title=epg_item['title']
                    ))
    return result


if __name__ == '__main__':
    """主函数：执行EPG数据抓取并保存到文件。"""
    # 获取所有频道的EPG数据
    data = get_epg_data()
    # 将数据保存为EPG文件
    save_epg_file(data)
