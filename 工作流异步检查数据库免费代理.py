

import os
import sys
import ssl
import time
import aiohttp
import asyncio
import SqliteHelper
from lxml import html
from multiprocessing import Process,Queue,Lock
from threading import Thread, current_thread
import threading


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/89.0.4389.90 Safari/537.36'
}


async def get_page_text(loop, url, return_type, conn, sleep_time=0,
                        proxy=None, timeout=20, headers=headers):
    try:    # 访问网页，获取网页内容
        await asyncio.sleep(sleep_time)
        async with aiohttp.ClientSession(loop=loop,
                                         connector=conn,
                                         connector_owner=False,
                                         headers=headers) as session:
            async with session.get(url, proxy=proxy, timeout=timeout) as response:
                if response.status != 200:
                    response.raise_for_status()
                if return_type == 'read':
                    page_text = await response.read()
                if return_type == 'json':
                    page_text = await response.json()
                return page_text
    except Exception as e:
        if str(e) != '':
            print(f'get_page_text:{e} url={url} proxy={proxy}')


async def check(my_queue, loop, url, conn, item):
    start_time = time.time()    #验证代理信息是否可用，并将可用结果加入流水线
    page_text = await get_page_text(loop, url, 'json', conn, proxy=item['proxy'])
    time_delay = time.time() - start_time
    if page_text == None:
        # print(f'获取网页为空,id={item["id"]},proxy={item["proxy"]}')
        return None
    ips = page_text['origin'].split(',')
    if len(ips) == 1:
        anonymous_type = '高匿'
    elif ips[0] == 'unknown':
        anonymous_type = '普匿'
    else:
        anonymous_type = '透明'
    record = {'proxy': item['proxy'],
            'location': item['location'],
            'anonymous_type': anonymous_type,
            'time_delay': '%.2f'%time_delay}
    my_queue.put(record)  #可用代理写入流水线，供下一步工作使用
    log_print(sys._getframe().f_code.co_name,
              start_time, f'work2-check-item id={item["id"]},{record} ')
    return item


def work1(my_queue):
    url = 'http://httpbin.org/ip'
    put_loop = start_thread(name='work2_thread')
    conn = aiohttp.TCPConnector(loop=put_loop, limit=10, limit_per_host=10)
    futures = []
    DB_FILE_PATH = r'./proxy.db'
    DB = SqliteHelper.Connect(DB_FILE_PATH)
    results = DB.table('proxy').findAll()
    DB.close()
    for result in results:
        future = asyncio.run_coroutine_threadsafe(
                    check(my_queue, put_loop, url, conn, result), put_loop)
        futures.append(future)
    for future in futures:  # 阻塞线程，直到所有任务返回结果
        if future.result() != None:
            print(f'work1 返回值:{future.result()}')
    my_queue.put('EOF')
    conn.close()


def work2(my_queue):
    DB_FILE_PATH = r'./proxy.db'
    DB = SqliteHelper.Connect(DB_FILE_PATH)
    while True:
        item = my_queue.get()
        if item == 'EOF':
            break
        DB.table('proxy').add(item)  # 可用代理信息写入本地sqlite3数据库


def log_print(func_name=None, start_time=0.0, notes=None, threading_enumerate=False):
    str = f'{func_name} '\
          f'开始:{translate(start_time)}  '\
          f'结束:{translate(time.time())}  '\
          f'用时:{format(time.time() - start_time, ".2f")}  '\
          f'线程:{len(threading.enumerate())}  '
    if notes != None:
        str = str + f'备注:{notes}'
    if threading_enumerate:
        str = str + f'线程:{threading.enumerate()}'
    print(str)


def translate(time_stamp):
    # return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time_stamp)))
    return time.strftime("%M:%S", time.localtime(int(time_stamp)))


def start_thread(name=None, is_daemon=True):
    new_loop = asyncio.new_event_loop()
    new_thread = Thread(target=start_loop, args=(new_loop,))
    new_thread.name = name
    new_thread.daemon = is_daemon
    new_thread.start()
    return new_loop


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    q1 = Queue()
    p1 = Process(target=work1, args=(q1,))
    p2 = Process(target=work2, args=(q1,))
    p1.daemon = True
    p2.daemon = True
    p1.start()
    p2.start()
    p1.join()
    p2.join()


if __name__ == "__main__":
    main()