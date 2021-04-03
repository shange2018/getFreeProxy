# -*- coding = utf-8 -*-
# @Time : 2021-03-29 13:35
# @Author : PZ
# @File : 工作流异步模板.py
# @Software : PyCharm


import os
import sys
import ssl
import time
import aiohttp
import asyncio
from lxml import html
from multiprocessing import Process,Queue,Lock
from threading import Thread, current_thread
import threading


async def put(my_queue, item):  #写入队列数据
    start_time = time.time()
    await asyncio.sleep(3)
    ... #执行异步任务，建议是下载任务，下载完后将信息写入队列
    my_queue.put(item)
    log_print(sys._getframe().f_code.co_name, start_time, f'work1 put item = {item}')
    return item


def work1(my_queue_1):  #第一个任务，建议是下载数据
    put_loop = start_thread(name='put_thread')
    items = [11,22,'',None,33,44]
    futures = []
    start_time = time.time()
    for item in items:  #异步执行写入队列任务
        future = asyncio.run_coroutine_threadsafe(put(my_queue_1, item), put_loop)
        futures.append(future)
    for i in range(len(futures)):   #确保每个异步任务结束
        assert futures[i].result() == items[i]
    log_print(sys._getframe().f_code.co_name, start_time)
    my_queue_1.put('EOF')   #写入队列任务结束标志


def work2(my_queue_1, my_queue_2):  #第二个任务，建议是分析数据
    put_loop = start_thread(name='put_thread')
    futures = []
    items = []
    start_time = time.time()
    while True:
        start_time1 = time.time()
        item = my_queue_1.get() #获取第一个任务传递的信息
        log_print(sys._getframe().f_code.co_name, start_time1, f'work2 get item = {item}')
        if item == 'EOF':   #判断任务是否结束
            break
        items.append(item)  #异步执行写入队列任务
        future = asyncio.run_coroutine_threadsafe(put(my_queue_2, item), put_loop)
        futures.append(future)
    for i in range(len(futures)):   #确保每个异步任务结束
        assert futures[i].result() == items[i]
    log_print(sys._getframe().f_code.co_name, start_time)
    my_queue_2.put('EOF')


def work3(my_queue_2):  #第三个任务，建议是持久化存储数据
    while True:
        start_time = time.time()
        item = my_queue_2.get()
        log_print(sys._getframe().f_code.co_name, start_time, f'work3 get item = {item}')
        if item == 'EOF':
            break
        ...


def log_print(func_name=None, start_time=0.0, notes=None, threading_enumerate=False):
    str = f'{func_name} '\
          f'开始时间:{translate(start_time)}  '\
          f'结束时间:{translate(time.time())}  '\
          f'用时:{format(time.time() - start_time, ".2f")}  '\
          f'线程数:{len(threading.enumerate())}  '
    if notes != None:
        str = str + f'备注:{notes}'
    if threading_enumerate:
        str = str + f'线程:{threading.enumerate()}'
    print(str)


def translate(time_stamp):  #时间格式转换
    # return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time_stamp)))
    return time.strftime("%M:%S", time.localtime(int(time_stamp)))


def start_thread(name=None, is_daemon=True):    #在新建线程中运行新建事件循环
    new_loop = asyncio.new_event_loop()
    new_thread = Thread(target=start_loop, args=(new_loop,))
    new_thread.name = name
    new_thread.daemon = is_daemon
    new_thread.start()
    return new_loop


def start_loop(loop):   #设置事件循环为当前事件循环，并永久运行
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    q1 = Queue()    # 开启两个队列，三个进程，每两个队列之间用队列传递信息
    q2 = Queue()
    p1 = Process(target=work1, args=(q1,))
    p2 = Process(target=work2, args=(q1,q2))
    p3 = Process(target=work3, args=(q2,))
    p1.daemon = True    # 子进程跟随主进程结束
    p2.daemon = True
    p3.daemon = True
    p1.start()
    p2.start()
    p3.start()
    p1.join()   # 等待子进程结束
    p2.join()
    p3.join()


if __name__ == "__main__":
    main()