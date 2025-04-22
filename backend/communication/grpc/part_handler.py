import faulthandler
import io
import logging
import sys
import time
from datetime import datetime
from threading import Thread

import cv2
import numpy as np
import jpeg4py as jpeg

sys.path.append('/home/unitx/unitx_data/config')

from backend.communication.grpc.grpc_client import grpc_client
from backend.communication.grpc.proto import upper_service_pb2 as pb2

# 如果程序因为段错误而崩溃，faulthandler 会打印出崩溃的具体行号
faulthandler.enable()

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

GRPC_TIMEOUT = 2

SELECT_SN_QUERY = "SELECT * FROM sn WHERE sn = %s"
INSERT_SN_QUERY = "INSERT INTO sn (sn, feedstock_num, unitx_result, ng_type, result, DeviceID, remark, timestamp) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
UPDATE_SN_QUERY = "UPDATE sn SET remark = %s WHERE id = %s"

INSERT_NG_TYPE_QUERY = "INSERT INTO ng_type (sn, feedstock_num, result, ng_type) " \
                       "VALUES (%s, %s, %s, %s) "

# def get_first_sn_id(sn):
#     connection = connection_pool.get_connection()  # 从连接池获取连接
#     cursor = connection.cursor()  # 使用连接执行数据库操作
#     try:
#         cursor.execute(SELECT_SN_QUERY, (sn,))
#         result = cursor.fetchone()  # 获取第一条记录
#         if result:
#             sn_id = result[0]
#             return sn_id
#         else:
#             logger.error(f"select sn:{sn} from sn table, result is None.")
#             return None
#     except Exception as e:
#         logger.exception(e)
#     finally:
#         cursor.close()  # 关闭游标
#         connection.close()  # 关闭连接
#     logger.error(f"select sn:{sn} from sn table error.")
#     return None

def get_first_sn_id(sn):
    try:
        req = pb2.GetFirstSnIdRequest(sn=sn)
        resp = grpc_client.GetFirstSnId(req, timeout=GRPC_TIMEOUT)
        if resp:
            return resp.sn_id
        else:
            logger.error(f"select sn:{sn} from sn table by grpc, result is None.")
            return None
    except Exception as e:
        logger.exception(e)
    logger.error(f"select sn:{sn} from sn table by grpc error.")
    return None


# def update_sn_id_remark(sn_id, remark):
#     connection = connection_pool.get_connection()  # 从连接池获取连接
#     cursor = connection.cursor()  # 使用连接执行数据库操作
#     try:
#         cursor.execute(UPDATE_SN_QUERY, (remark, sn_id))
#         connection.commit()  # 提交事务，将更改保存到数据库
#         return True
#     except Exception as e:
#         connection.rollback()
#         logger.exception(e)
#         return False
#     finally:
#         cursor.close()  # 关闭游标
#         connection.close()  # 关闭连接


def update_sn_id_remark(id, remark):
    try:
        logger.info(f"UpdateSnIdRemark start, id:{id}, remark:{remark}")
        req = pb2.UpdateSnIdRemarkRequest(id=id, remark=remark)
        grpc_client.UpdateSnIdRemark(req, timeout=GRPC_TIMEOUT)
        logger.info(f"UpdateSnIdRemark success, id:{id}, remark:{remark}")
        return True
    except Exception as e:
        logger.exception(e)
        return False


def update_sn_remark(sn, remark):
    sn_id = get_first_sn_id(sn)
    update_sn_id_remark(sn_id, remark)
    logger.info(f"sn:{sn} update remark:{remark} ok, sn_id:{sn_id}")


# def insert_data_to_db(sn_data, ng_type_data_list):
#     """
#     数据库操作
#     """
#     logger.info("[part_handler] insert_data_to_db() start insert data to db")
#     connection = connection_pool.get_connection()  # 从连接池获取连接
#     cursor = connection.cursor()  # 使用连接执行数据库操作
#     try:
#         cursor.execute(INSERT_SN_QUERY, sn_data)  # 插入sn表
#         connection.commit()
#
#         # cursor.executemany(INSERT_NG_TYPE_QUERY, ng_type_data_list)  # 批量插入ng_type表
#         # connection.commit()
#     except Exception as e:
#         logger.exception(e)
#         connection.rollback()
#     finally:
#         cursor.close()  # 关闭游标
#         connection.close()  # 关闭连接
#     logger.info("[part_handler] insert_data_to_db() insert data to db over.")


def insert_data_to_db(sn, feedstock_num, unitx_result, ng_type, result, DeviceID, remark, timestamp, is_timeout_sn):
    logger.info(
        f"[part_handler] InsertDataToDb start, sn: {sn}, feedstock_num: {feedstock_num}, unitx_result: {unitx_result}, ng_type: {ng_type}, result: {result}, DeviceID: {DeviceID}, remark: {remark}, timestamp: {timestamp}, is_timeout_sn: {is_timeout_sn}.")
    try:
        req = pb2.InsertDataToDbRequest(sn=sn, feedstock_num=feedstock_num, unitx_result=unitx_result, ng_type=ng_type,
                                        result=result, DeviceID=DeviceID, remark=remark, timestamp=timestamp, is_timeout_sn = is_timeout_sn)
        start_time = time.time()
        grpc_client.InsertDataToDb(req, timeout=GRPC_TIMEOUT)
        grpc_time = time.time() - start_time
        logger.info(f"[part_handler] InsertDataToDb success, sn: {sn}, took {grpc_time:.3f} seconds.")

    except Exception as e:
        logger.exception(e)


# def save_rgbbgr(file_path, image, image_ok, file_format='jpg'):
#     if image_ok:
#         image = cv2.resize(image,
#                            (int(image.shape[1] / 2.5), int(image.shape[0] / 2.5)))
#     if file_format == 'png':
#         cv2.imwrite(file_path[:-4], image)
#         os.replace(file_path[:-4], file_path)
#     elif file_format == 'jpg':
#         if image.dtype != np.uint8:
#             image = image.astype(np.uint8)
#         jpeg.JPEGEncoder(image).encode(file_path, quality=25)
#     else:
#         image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
#         cv2.imwrite(file_path, image)
#     logger.info(f"[part_handler] save jpg success. save path:{file_path}")


def save_rgbbgr(file_name, image, image_ok, part_id, timestamp):
    logger.info(f"[part_handler] save_rgbbgr start, file_name:{file_name}, part_id:{part_id}, timestamp: {timestamp}")
    start_time = time.time()

    if image_ok:
        image = cv2.resize(image, (int(image.shape[1] / 2.5), int(image.shape[0] / 2.5)))

    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    try:
        byte_arr = io.BytesIO()
        jpeg.JPEGEncoder(image).encode(byte_arr, quality=25)

        req = pb2.ImageRequest(file_name=file_name, part_id=part_id, timestamp=timestamp, image_data=byte_arr.getvalue())
        ready_time = time.time()

        logger.info(
            f"[part_handler] save_rgbbgr ready, call ImageHandler. file_name:{file_name}, part_id:{part_id}, timestamp: {timestamp}, took {ready_time - start_time:.3f} seconds to ready.")

        resp = grpc_client.ImageHandler(req)
        grpc_time = time.time() - ready_time

        if resp.code != 0:
            logger.error(
                f"[part_handler] save_rgbbgr finish, ImageHandler failed. file_name:{file_name}, part_id:{part_id}, timestamp: {timestamp}, err_msg:{resp.message}, took {grpc_time:.3f} seconds.")
        else:
            logger.info(
                f"[part_handler] save_rgbbgr finish, ImageHandler success. file_name:{file_name}, part_id:{part_id}, timestamp: {timestamp}, took {grpc_time:.3f} seconds.")
    except Exception as e:
        logger.exception(e)


# def check_file_path(shared_folder_path, file_path):
#     if not os.path.exists(shared_folder_path):
#         logger.error(f"[part_handler] warning: the path {shared_folder_path} not online!")
#         return
#     if not os.path.exists(file_path):
#         os.makedirs(file_path, exist_ok=True)
#         logger.debug(f"mkdir success, file_path:{file_path}")


def on_part_done(**kwargs):
    decision = kwargs["ok"]
    part_id = kwargs['part_id']
    part_results = kwargs["part_results"]
    not_enough_image_results = kwargs["not_enough_image_results"]

    # SHARED_FOLDER_PATH = "/home/unitx/shared_images/images"  # 挂载盘
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    # file_path = os.path.join(SHARED_FOLDER_PATH, part_id, timestamp)
    # check_file_path(SHARED_FOLDER_PATH, file_path)

    all_ng_types = list()
    # threads = []

    # mark图另存到上位机
    logger.info(f"[part_handler] start save mask to upper server, part_id:{part_id}")
    start_time = time.time()
    for key, image_results in part_results.items():
        for i, image in image_results.items():
            image_ok = image.ok
            image_timestamp = image.image_timestamp
            mask_overlaid = image.mask_overlaid
            network_detail_results = image.network_detail_results

            image_datetime = datetime.fromtimestamp(image_timestamp / 1000)
            image_result = 'OK' if image_ok else 'NG'
            img_name = f"{image_result}_{part_id}_{str(image_datetime).replace(' ', '_').replace(':', '-')}"
            # img_path = f'{file_path}/{img_name}.jpg'

            try:
                # save_rgbbgr(img_path, mask_overlaid, image_ok, 'jpg')
                save_rgbbgr(f'{img_name}.jpg', mask_overlaid, image_ok, part_id, timestamp)

                # t = Thread(
                #     target=save_rgbbgr,
                #     args=(f'{img_name}.jpg', mask_overlaid, image_ok, part_id, timestamp)
                # )
                #
                # t.start()
                # threads.append(t)

            except Exception as e:
                logger.error(f"save jpg failed. part_id:{part_id}")
                logger.exception(e)

            for network, network_result in network_detail_results.items():
                if not network_result.get("ng_stats"):
                    continue
                for ng_type in network_result["ng_stats"]:
                    if ng_type["decision"] == "NG":
                        all_ng_types.append(ng_type["name"])

    # 等待所有传图线程完成
    # for t in threads:
    #     t.join()

    execution_time = time.time() - start_time
    logger.info(
        f'[part_handler] finished save mask to upper server, part_id:{part_id}, took {execution_time:.3f} seconds.')

    try:
        logger.info(f"[part_handler] start insert data to db, part_id:{part_id}")
        result = "OK" if decision else "NG"
        all_ng_types = set(all_ng_types)
        feedstock_num = 0
        # sn, feedstock_num, unitx_result, ng_type, result, DeviceID
        remark = "丢图物料" if not_enough_image_results else ""
        # sn_data = [part_id, feedstock_num, result, "" if decision else ";".join(all_ng_types),
        #            result, "Unitx", remark, timestamp]

        ng_type_data_list = []
        for ng_type in all_ng_types:
            # sn, feedstock_num, result, ng_type
            ng_type_data_list.append([part_id, feedstock_num, result, ng_type])

        # insert_data_to_db(sn_data, ng_type_data_list)

        insert_data_to_db(part_id, feedstock_num, result, "" if decision else ";".join(all_ng_types),
                            result, "Unitx", remark, timestamp, False)

        # server = ServerProxy("http://localhost:9090/")
        # server.receiver(part_id, sn_data, ng_type_data_list)

        logger.info(f"[part_handler] insert data to db by grpc over, part_id:{part_id}")
    except Exception as e:
        logger.error(f"[part_handler] insert data to db by grpc failed. part_id:{part_id}")
        logger.exception(e)

    logger.info(f"[part_handler] part_handler over, part_id:{part_id}")