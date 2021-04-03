# -*- coding = utf-8 -*-
# @Time : 2021-03-25 14:26
# @Author : PZ
# @File : www_zhimahttp_com.py
# @Software : PyCharm
import json
import aiohttp
import asyncio
import ssl
from lxml import html


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
}


def parse_zhimahttp(page_text):
    proxys = []
    etree = html.etree
    parser = etree.HTMLParser(encoding="utf-8")
    # str = etree.parse('./page_text.html',parser=parser)
    str = etree.HTML(page_text, parser=parser)
    ips = str.xpath('//tr//td[1]/text()')
    ports = str.xpath('//tr//td[2]/text()')
    for i in range(0,len(ips)):
        # proxy = {'http':'http://' + ips[i] + ':' + ports[i]}
        proxy = 'http://' + ips[i] + ':' + ports[i]
        proxys.append(proxy)
    return proxys


async def fetch(session, url, headers=headers, ssl=ssl.SSLContext(), timeout=10):
    try:
        async with session.get(url, headers=headers, ssl=ssl, timeout=timeout) as response:
            if response.status != 200:
                response.raise_for_status()
            result = await response.read()
            page_text = json.loads(result.decode('utf-8'))['ret_data']['html']
            return parse_zhimahttp(page_text)
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
            task = asyncio.ensure_future(fetch(session, url))
            task.add_done_callback(callback)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)


async def check(session, url, proxy, headers=headers, timeout=20):
    try:
        async with session.get(url, proxy=proxy, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                response.raise_for_status()
            print('check:可以了')
            # return await response.read()
    except Exception as e:
        print('check:', repr(e))
        # raise e


async def check_all(url, loop, proxys):
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = []
        for proxy in proxys:
            task = asyncio.ensure_future(check(session, url, proxy))
            task.add_done_callback(callback)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    urls = ['http://wapi.http.linkudp.com/index/index/get_free_ip']
    loop = asyncio.get_event_loop()
    proxyss = loop.run_until_complete(fetch_all(urls, loop))
    proxys = []
    for proxys1 in proxyss:
        proxys += proxys1
    print('proxys:',proxys)
    url = 'http://httpbin.org/ip'
    result = loop.run_until_complete(check_all(url, loop, proxys))
    print('测试代理:',result)