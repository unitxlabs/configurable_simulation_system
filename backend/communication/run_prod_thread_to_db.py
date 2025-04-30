# coding=utf-8

import json
import logging
import random
import signal
import sys
import threading
import time
import traceback
from datetime import datetime
from threading import Thread, Lock, Event
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from collections import OrderedDict
import mysql.connector.pooling

HOST, PORT = "localhost", 9090

# 连接池配置
config = {
    "user": "user",  # 数据库用户名
    "password": "123456",  # 数据库密码
    "host": "127.0.0.1",  # 数据库地址
    "port": 3306,  # 数据库端口
    "database": "mydatabase",  # 数据库名
    "pool_name": "my_connection_pool",  # 连接池名字
    "pool_size": 8,  # 最大连接数
}

# 创建连接池，用于后处理中的数据库操作
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**config)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename="/home/unitx/unitx_data/logs/thread_to_db.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

SELECT_SN_QUERY_1 = "SELECT id, timestamp, remark FROM sn WHERE sn = %s order by id asc"  # 从小到大排序
SELECT_SN_QUERY = "SELECT * FROM sn WHERE sn = %s"
INSERT_SN_QUERY = "INSERT INTO sn (sn, feedstock_num, unitx_result, ng_type, result, DeviceID, remark, timestamp) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
UPDATE_SN_QUERY = "UPDATE sn SET remark = %s WHERE id = %s"

INSERT_NG_TYPE_QUERY = "INSERT INTO ng_type (sn, feedstock_num, result, ng_type) " \
                       "VALUES (%s, %s, %s, %s) "
UPDATE_SN_ON_PART_DONE_QUERY = "UPDATE sn SET feedstock_num = %s, unitx_result = %s, ng_type = %s, result = %s, DeviceID = %s, timestamp = %s WHERE id = %s"

timeout_seconds = 3  # 数据表操作超时时间

insert_q = Queue()  # 插入数据队列
update_q = Queue()  # 更新超时物料队列
timeout_q = Queue()  # 记录超时 part_id
stop_event = Event() 

class Cache:
    """
    缓存：可以规定缓存大小，超出自动剔除旧数据
    """

    def __init__(self, max_size):
        self.max_size = max_size
        self.cache = OrderedDict()

    def add(self, key, value):
        if key in self.cache:
            self.cache.pop(key)  # 如果键已经存在于缓存中，先将其删除
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # 如果缓存已满，删除最旧的元素
        self.cache[key] = value

    def contains(self, key):
        return key in self.cache

    def get(self, key):
        return self.cache.get(key)

    def count(self):
        return len(self.cache)

    def pop_item(self, item):
        return self.cache.pop(item, None)


class RPCServer(Thread):
    def __init__(self):
        super(RPCServer, self).__init__()
        self.timeout_part_id_cache = Cache(max_size=100)  # 超时物料：先 超时物料后 on_part_done
        self.server=None

    def receiver(self, part_id, sn_data, ng_type_data_list):
        """
        1. 先 on_part_done，后超时物料：理论上无
        2. 先超时，后 on_part_done
        3. 只有 on_part_done，无超时
        """
        # 若超时物料缓存中无，则插入新纪录 on_part_done
        if not self.timeout_part_id_cache.contains(part_id):
            info = {"sn": part_id, "sn_data": sn_data, "ng_type_data_list": ng_type_data_list, 'flag': 'insert'}
            insert_q.put(info)
        else:
            # 超时物料先来，on_part_done 后进来，则更新 on_part_done
            info = {"sn": part_id, "sn_data": sn_data, "ng_type_data_list": ng_type_data_list, 'flag': 'update'}
            insert_q.put(info)

            # 清除缓存
            self.timeout_part_id_cache.pop_item(part_id)

        logger.info(f"receiver: {info}\tinsert_q qsize: {insert_q.qsize()}\tcache size: {self.timeout_part_id_cache.count()}")

    def receiver_sn_remark(self, sn, remark):
        """超时物料"""
        info = {"sn": sn, "remark": remark}

        logger.info(f"receiver_sn_remark: {info}\tupdate_q: {update_q.qsize()}")

        # 任务队列
        update_q.put(info)

        # 缓存队列
        self.timeout_part_id_cache.add(sn, "")

    def run(self):
        with SimpleXMLRPCServer((HOST, PORT), allow_none=True) as server:
            server.register_function(self.receiver, "receiver")
            server.register_function(self.receiver_sn_remark, "receiver_sn_remark")

            try:
                server.serve_forever()
                self.server=server
            except Exception as e:
                logger.error(f"RPCServer error:{traceback.format_exc()}.")


def update_sn_thread(cursor, connection, sn, remark):
    """
    INSERT_SN_QUERY = "INSERT INTO sn (sn, feedstock_num, unitx_result, ng_type, result, DeviceID, remark, timestamp) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
    """
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    # timestamp = datetime.now()

    cursor.execute(INSERT_SN_QUERY, (sn, 0, 'NG', '', 'NG', 'Unitx', remark, timestamp))

    # # 模拟写入超时
    # time.sleep(4)

    if connection._cnx:
        connection.commit()

    # # 方法二：
    # try:
    #     cursor.execute(INSERT_SN_QUERY, (sn, 0, 'NG', '', 'NG', 'Unitx', remark, timestamp))
    #
    #     # # 模拟写入超时
    #     # time.sleep(4)
    #
    #     if connection._cnx:
    #         connection.commit()
    # except:
    #     logger.error(f"update_sn_thread_error: {traceback.format_exc()}")


def update_sn_remark():
    while not stop_event.is_set():
        sn_result = update_q.get()
        if not sn_result:
            time.sleep(0.1)
            continue

        logger.info(
            f"start_update_sn_remark, sn_result: {sn_result}\tthread_name: {threading.currentThread().getName()}")
        sn = sn_result.get("sn", "")
        remark = sn_result.get("remark", "")

        connection = connection_pool.get_connection()  # 从连接池获取连接
        cursor = connection.cursor()  # 使用连接执行数据库操作
        st = time.perf_counter()

        try:
            # # 同步
            # update_sn_thread(cursor, connection, sn, remark)

            # 异步超时：多线程
            t = threading.Thread(target=update_sn_thread, args=(cursor, connection, sn, remark))
            t.start()
            t.join(timeout=timeout_seconds)

            # 超时，数据回滚，终止写入
            if t.is_alive():
                timeout_q.put(sn)
                logger.error(f"update_sn_remark timeout, sn: {sn}")

        except Exception as e:
            logger.exception(f"update_sn_remark, sn: {sn}\terror: {traceback.format_exc()}")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

        logger.info(f"end_update_sn:{sn} remark:{remark} ok\t\tcost_time: {round(time.perf_counter() - st, 2)}\n")


def write_to_db_thread(cursor, connection, result):
    """
    "INSERT INTO sn (sn, feedstock_num, unitx_result, ng_type, result, DeviceID, remark, timestamp) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
    result: {'sn': '1705889953',
     'sn_data': ['1705891175', 0, 'NG', 'all_ng_types', 'NG', 'Unitx', '', '2024_01_22_10_39_35_346688'], 'ng_type_data_list': [['1705889953', 0, 'NG', 'NG:划痕']]}
    """
    sn_data = result.get("sn_data", [])
    cursor.execute(INSERT_SN_QUERY, sn_data)  # 插入sn表

    # TODO：超时后，connection 已关闭，connection._cnx 为 None
    if connection._cnx:
        connection.commit()

    cursor.executemany(INSERT_NG_TYPE_QUERY, result.get("ng_type_data_list", []))
    if connection._cnx:
        connection.commit()

    # # 方法二：此处可以用 try 包裹，不做判断，超时后 connection 已归还 commit 也会报错，这样子线程自动结束
    # try:
    #     cursor.execute(INSERT_SN_QUERY, sn_data)  # 插入sn表
    #
    #     connection.commit()
    #
    #     cursor.executemany(INSERT_NG_TYPE_QUERY, result.get("ng_type_data_list", ""))
    #     connection.commit()
    # except:
    #     logger.error(f"write_to_db_thread_error: {traceback.format_exc()}")


def update_sn_on_part_done_thread(cursor, connection, result, part_id):
    """
    先超时后 on_part_done，更新操作
    UPDATE_SN_ON_PART_DONE_QUERY = "UPDATE sn SET feedstock_num = %s, unitx_result = %s, ng_type = %s, result = %s, DeviceID = %s, timestamp = %s WHERE id = %s"
    sn_data: [part_id, feedstock_num, result, "" if decision else ";".join(all_ng_types), result, "Unitx", remark, timestamp]
    """
    sn_data = result.get("sn_data", [])

    # 查询 id #  [(1849, '2024_01_22_13_33_01_238682', '超时物料'), (1850, '2024_01_30_15_26_31_238682', '超时物料')]
    cursor.execute(SELECT_SN_QUERY_1, (part_id,))
    rows = cursor.fetchall()
    if not rows:
        logger.error(f"update_sn_on_part_done_thread_error, no sn: {part_id}")
        return

    # sn_id = rows[0]
    sn_id = rows[-1][0]

    # 更新 sn 表
    values = [sn_data[1], sn_data[2], sn_data[3], sn_data[4], sn_data[5], sn_data[7], sn_id]
    logger.info(f"update_sn_on_part_done_thread, values: {values}")

    cursor.execute(UPDATE_SN_ON_PART_DONE_QUERY, values)
    if connection._cnx:
        connection.commit()

    # 更新 ng_type 表
    cursor.executemany(INSERT_NG_TYPE_QUERY, result.get("ng_type_data_list", []))  # 批量插入ng_type表
    if connection._cnx:
        connection.commit()


def insert_to_db():
    """
    插入数据
    """
    while not stop_event.is_set():
        result = insert_q.get()
        if not result:
            time.sleep(0.01)
            continue

        part_id = result.get("sn", "")
        logger.info(
            f"start_insert_data_to_db, part_id: {part_id}\tresult: {result}\t{threading.currentThread().getName()}\n")

        connection = connection_pool.get_connection()  # 从连接池获取连接
        cursor = connection.cursor()  # 使用连接执行数据库操作
        st = time.perf_counter()

        try:
            # # 同步
            # write_to_db_thread(cursor, connection, result)
            flag = result.get("flag", 'insert')

            # 异步超时：多线程
            # 插入
            if flag == "insert":
                t = threading.Thread(target=write_to_db_thread, args=(cursor, connection, result))
                t.start()
                t.join(timeout=timeout_seconds)
            else:
                # 更新
                t = threading.Thread(target=update_sn_on_part_done_thread, args=(cursor, connection, result, part_id))
                t.start()
                t.join(timeout=timeout_seconds)

            # 超时，数据回滚，终止写入
            if t.is_alive():
                logger.error(f"insert_to_db timeout, part_id: {part_id}\n")
                # 存入本地文件
                timeout_q.put(part_id)

        except Exception as e:
            logger.exception(f"insert_to_db_error, part_id: {part_id}\terror: {traceback.format_exc()}")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

        logger.info(f"end_insert_data_to db, part_id: {part_id}\t\tcost_time: {round(time.perf_counter() - st, 2)}")


def get_timeout_thread():
    """
    获取超时物料相关信息，并写入文件中
    """
    with open("timeout.txt", "a", encoding="utf-8") as f:
        while not stop_event.is_set():
            value = timeout_q.get()
            if not value:
                time.sleep(0.1)
                continue

            logger.error(f"timeout error: {value}")
            f.write(str(value) + "\n")
            f.flush()


def get_active_thread_count():
    """获取主线程中有多少个存活的子线程"""
    while not stop_event.is_set():
        count = threading.active_count()
        logger.info(f"active_count: {count}\n")
        time.sleep(5)




class HttpProxy:
    def __init__(self):
        self.lp=None
        self.sub_thread=None
        self.rpc_server=None
        self.pool=None

    def start_proxy(self):
        self.lp=threading.Thread(target=get_timeout_thread)
        self.lp.start()
        self.sub_thread = threading.Thread(target=get_active_thread_count)
        self.sub_thread.start()
        self.rpc_server = RPCServer()
        self.rpc_server.start()
        self.pool=ThreadPoolExecutor(max_workers=6)
        for _ in range(3):
            self.pool.submit(insert_to_db)
        for _ in range(3):
            self.pool.submit(update_sn_remark)

    def stop_proxy(self):
        stop_event.set()
        self.lp.join()
        self.sub_thread.join()
        self.rpc_server.server.shutdown()
        self.pool.shutdown(wait=True)

