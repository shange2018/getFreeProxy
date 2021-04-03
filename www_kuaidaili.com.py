# -*- coding = utf-8 -*-
# @Time : 2021-03-25 22:32
# @Author : PZ
# @File : www_kuaidaili.com.py
# @Software : PyCharm
import aiohttp
import asyncio
import ssl
from lxml import html

# https://www.fanqieip.com/free
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
}


def parse_kuaidaili(page_text):
    proxys = []
    etree = html.etree
    parser = etree.HTMLParser(encoding="utf-8")
    # str = etree.parse('./page_text.html',parser=parser)
    str = etree.HTML(page_text, parser=parser)
    ips = str.xpath('//td[@data-title="IP"]/text()')
    ports = str.xpath('//td[@data-title="PORT"]/text()')
    for i in range(0,len(ips)):
        proxy = 'http://' + ips[i] + ':' + ports[i]
        proxys.append(proxy)
    return proxys


async def fetch(session, url, sleeptime, headers=headers, ssl=ssl.SSLContext(), timeout=10):
    try:
        await asyncio.sleep(sleeptime)
        async with session.get(url, headers=headers, ssl=ssl, timeout=timeout) as response:
            if response.status != 200:
                response.raise_for_status()
            result = await response.read()
            return parse_kuaidaili(result)
            # return await response.read()
    except Exception as e:
        raise e


def callback(future):
    pass
    # print('callback',json.loads(future.result())['ret_data']['html'])
    # return None


async def fetch_all(urls, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(fetch(session, url, urls.index(url)*2))
            task.add_done_callback(callback)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)


async def check(session, url, proxy, headers=headers, timeout=20):
    try:
        await asyncio.sleep(1)
        async with session.get(url, proxy=proxy, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                response.raise_for_status()
            print('可用代理:',proxy)
            return proxy
            # return await response.read()
    except Exception as e:
        if str(e) != '':
            print('check:', e)
        raise e


async def check_all(url, loop, proxys):
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = []
        for proxy in proxys:
            task = asyncio.ensure_future(check(session, url, proxy))
            task.add_done_callback(callback)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    urls = [f'https://www.kuaidaili.com/free/intr/{page}' for page in range(5,7)]
    loop = asyncio.get_event_loop()
    proxyss = loop.run_until_complete(fetch_all(urls, loop))
    proxys = []
    for proxys1 in proxyss:
        proxys += proxys1
    print('proxyss:',proxyss)
    # url = 'http://httpbin.org/ip'
    url = 'http://httpbin.org/get'
    result = loop.run_until_complete(check_all(url, loop, proxys))
    print('测试代理:',result)