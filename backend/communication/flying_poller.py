# coding: utf-8

import os
import sys
import time
import logging
from datetime import datetime
from threading import Thread, Lock, Event
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from backend.modbus_tcp_client import ModbusTCP
sys.path.append('/home/unitx/unitx_data/config')

from prod_api import ProdApiClient
from flying_communication import *

from backend.communication.grpc.part_handler import update_sn_remark, insert_data_to_db

logger = logging.getLogger("COMMUNICATION_POLLER")
log_to_dict = logging.getLogger("get_settings_time")


part_dict_lock = Lock()
part_result_dict_lock = Lock()
pause_event = Event()

wait_times = 60  # 超时物料最多等待时间，单位秒


def write_timeout_to_database(part_id):
    time.sleep(10)  # 等10秒再更新，让part_handler有时间更新数据库
    num = 0
    logger.debug(f"write_timeout_to_database, part_id: {part_id}")

    while num <= wait_times:
        num += 1
        if proxy.part_result_dict.get(part_id) is not None:
            update_sn_remark(sn=part_id, remark="超时物料")
            logger.warning(f"update db remark part_id:{part_id}, remark:超时物料, wait_times:{num}")
            with part_result_dict_lock:
                proxy.part_result_dict.pop(part_id, None)
            break
        time.sleep(1)
    else:
        logger.warning(f"part_id:{part_id} not in part_result_dict, update db remark failed, wait_times:{num}")
        update_sn_remark(sn=part_id, remark="超时物料")
        logger.warning(f"update_sn_remark_sn_no_cache_end, part_id: {part_id}")


class Proxy(Thread):
    def __init__(self):
        super(Proxy, self).__init__()
        self.part_id_dict = dict()
        self.part_result_dict = dict()

    def on_part_done(self, part_id, decision):
        logger.info(f"(Cache Proxy) on_part_done start. part_id:{part_id}, decision:{decision}")
        if isinstance(decision, int) and decision in (OK, NG1, NG2):
            result = decision
        elif len(decision) == 2 and decision == "OK":
            result = OK
        elif len(decision) == 3 and isinstance(decision, str) and decision.startswith("NG"):
            result = int(decision[2])
        else:
            result = NG2
        with part_result_dict_lock:
            self.part_result_dict[part_id] = result
        logger.info(f"(Cache Proxy) on_part_done over. part_result_dict:{self.part_result_dict}")

    def update_part_id(self, old_id, new_id):
        logger.info(f"(Cache Proxy) update_part_id start. old_id:{old_id}, new_id:{new_id}")
        if old_id.isdigit():
            old_id = int(old_id)
        with part_dict_lock:
            self.part_id_dict[old_id] = new_id
        logger.info(f"(Cache Proxy) update_part_id over. part_id_dict:{self.part_id_dict}")

    def run(self):
        logger.info("(Cache Proxy) register_function start.")
        try:
            with SimpleXMLRPCServer((CACHE_PROXY_HOST, CACHE_PROXY_PROT), allow_none=True) as server:
                server.register_function(self.on_part_done, "on_part_done")
                server.register_function(self.update_part_id, "update_part_id")

                server.serve_forever()
        except Exception as e:
            logger.error(f"(Cache Proxy) register_function error:{e}.")
            logger.logger.exception(e)
            os._exit(1)
        logger.info("(Cache Proxy) register_function over.")


class PartProcessor(object):
    def __init__(self, host_ip=MODBUS_HOST, host_port=MODBUS_PROT):
        self.host_ip = host_ip
        self.host_port = host_port
        self.client = None
        # sensor_last_timestamp_dict 传感器上一次的时间戳，用于校验传感器是否在正确的时间触发。
        self.sensor_last_timestamp_dict = {}
        # sensor_last_part_dict 表示每个传感器上次经过的物料，用于查询当前物料的ID
        self.sensor_last_part_dict = {}

        # sensor_cur_part_dict 表示每个传感器dang qian经过的物料，用于查询当前物料的ID
        self.sensor_cur_part_dict = {}

        # part_dict　表示物料的所有传感器时间的字典，元素如　
        # key(part_id): {"status": True,
        #               "pause_time": 0,
        #               "s0: time, R1: time, R2: time, ..., S1: time}
        self.part_dict = dict()

        # processing_part_list 表示正在生产线上处理的物料, like: [part1_sn, part2_sn, part3_sn, ...]
        self.processing_part_list = []
        # PLC暂停时的时间戳
        self.plc_pause_start_time = 0
        # PLC当前时间戳，每次轮询时更新
        self.plc_timestamp = 0
        # prod_status 表示 production 的状态，默认0表示 production 还未就绪
        self.prod_status = 0

        self.last_register_values = []
        self.warring_dict = {}
        self.is_sensor_error = False

        self.connect_host()
        self._init()
        self.write_plc_heartbeat()
        self.get_prod_heartbeat()

    def connect_host(self):
        self.client = ModbusTCP(host=self.host_ip, port=self.host_port)
        self.client.start()
        logger.info("start ModbusTcp client.")

    def write_plc_heartbeat(self):
        Thread(target=self.plc_heartbeat).start()

    def get_prod_heartbeat(self):
        Thread(target=self.prod_heartbeat).start()

    def plc_heartbeat(self):
        """心跳"""
        logger.debug("start plc heartbeat.")
        while True:
            time.sleep(PLC_HEARTBEAT_POLLER_TIME)
            with self.client.locker:
                heartbeat_val = self.client.read(addr=REGISTER_ADDR[PLC_HEARTBEAT]["addr"],
                                                 length=REGISTER_ADDR[PLC_HEARTBEAT]["length"])
            if heartbeat_val and not heartbeat_val[0]:
                time.sleep(PLC_HEARTBEAT_WAIT_TIME)
                with self.client.locker:
                    self.client.write(addr=REGISTER_ADDR[PLC_HEARTBEAT]["addr"], val=1, datatype="int")
                    self.client.write(addr=REGISTER_ADDR[PROD_HEARTBEAT]["addr"], val=self.prod_status, datatype="int")
                logger.debug("write plc heartbeat ok.")

    def prod_heartbeat(self):
        """prod 心跳"""
        logger.debug("start prod heartbeat.")
        while True:
            time.sleep(PROD_HEARTBEAT_POLLER_TIME)
            self.prod_status = ProdApiClient.get_prod_system_status()
            logger.debug(f"get prod heartbeat ok, prod status {self.prod_status}.")

    def run_process(self):
        while True:
            try:
                time.sleep(0.015)
                start_time = time.time()
                logger.debug(f"start read register. start_time:{start_time}")

                read_register_signal = self.client.read_multi_addr(addr=0, length=REGISTER_ADDR_LENGTH)
                logger.debug(f"read_register_signal:{read_register_signal}")

                if (
                        read_register_signal[8:] == self.last_register_values
                        and read_register_signal[44] == 0
                        and not self.part_dict
                ):
                    # 除了心跳、时间戳外的信号不变的情况, and part_dict is empty
                    logger.debug(f"end read register. all signal is 0. use time:{(time.time() - start_time)}")
                    continue
                elif read_register_signal[44] == 0 and self.is_sensor_error:
                    logger.warning(f"plc reset is 0, but there is sensor error existed!")
                    continue

                logger.debug(f"start decode, read_register_signal:{read_register_signal}")
                signal_dict = self.decode_signal(read_register_signal)
                logger.debug(f"==signal_dict:{signal_dict}")

                plc_reset_timestamp = signal_dict.get(PLC_RESET)
                if plc_reset_timestamp and isinstance(plc_reset_timestamp, list) and plc_reset_timestamp[0] == 1:
                    self._init()
                    logger.info(f"end read register. plc_reset. signal_dict:{signal_dict}. "
                                f"use time:{(time.time() - start_time)}")
                    continue
                else:
                    logger.debug(f"pass plc_reset, signal_dict:{signal_dict}")

                # 暂停后启动(区别开机启动)
                plc_start_timestamp = signal_dict.get(PLC_START)
                if plc_start_timestamp and self.plc_pause_start_time != 0:
                    self.plc_start(plc_start_timestamp)
                    pause_event.clear()
                # 暂停
                elif signal_dict.get(PLC_PAUSE):
                    if self.plc_pause_start_time != 0:
                        # PLC多次暂停不启动，只记录第一次暂停时间
                        logger.debug("plc_pause_start_time is not 0. pass record plc_pause timestamp.")
                        continue
                    else:
                        self.plc_pause_start_time = signal_dict.get(PLC_PAUSE)
                        logger.info("plc_pause. record plc_pause timestamp.")
                        pause_event.set()

                if signal_dict.get(SENSOR_PART_START) is not None:
                    self.run_part_start(signal_dict.get(SENSOR_PART_START), signal_dict.get(PART_START_SN))
                logger.debug("run_part_start over")

                for station in CAMERA_STATION_LIST:
                    # if signal_dict.get(station) is not None and self.processing_part_list:
                    if signal_dict.get(station) is not None:
                        self.camera_station(station, signal_dict.get(station))
                logger.debug("camera_station over")

                # if signal_dict.get(SENSOR_PART_END) is not None and self.processing_part_list:
                if signal_dict.get(SENSOR_PART_END) is not None:
                    self.part_end(signal_dict.get(SENSOR_PART_END))
                logger.debug("part_end over")

                for key in self.sensor_last_part_dict.keys():
                    self.sensor_last_part_dict[key] = self.sensor_cur_part_dict[key]
                logger.debug(f"run_process sensor_cur_part_dict {self.sensor_cur_part_dict}")

                self.last_register_values = read_register_signal[8:]

                if self.warring_dict:
                    logger.debug(f"run_process write warring_dict")
                    with self.client.locker:
                        for k, v in self.warring_dict.items():
                            self.client.write(addr=REGISTER_ADDR[PART_RESULT_MSG]['addr'], val=v, datatype="int")
                            self.client.write(addr=REGISTER_ADDR[PART_RESULT_SN]['addr'], val=str(k), datatype="str")
                        self.is_sensor_error = True
                self.warring_dict.clear()

                logger.debug(f"--end--cache: \n"
                            f"sensor_last_timestamp_dict:{self.sensor_last_timestamp_dict}, \n"
                            f"sensor_last_part_dict:{self.sensor_last_part_dict}, \n"
                            f"part_dict:{self.part_dict}, \n"
                            f"processing_part_list:{self.processing_part_list}\n")
                logger.debug(f"end read register. use time:{(time.time() - start_time)}")

            except Exception as e:
                logger.error(f"run_process failed! {e}", exc_info=True)

    def plc_start(self, plc_start_timestamp):
        logger.info("plc_start start")
        pause_time = self.get_pause_time(plc_start_timestamp)
        self.plc_pause_start_time = 0
        for item in self.part_dict.values():
            item["pause_time"][item["cur_sensor"]] += pause_time
        with self.client.locker:
            self.client.write(addr=REGISTER_ADDR[PLC_START]["addr"], val="", datatype='str', length=4)
            self.client.write(addr=REGISTER_ADDR[PLC_PAUSE]["addr"], val="", datatype='str', length=4)
        logger.info("plc_start over")

    def decode_signal(self, read_register_signal):
        """解析信号"""
        decode_dict = dict()
        for signal_name, signal_dict in REGISTER_ADDR.items():
            if not signal_dict.get("is_read"):
                continue
            signal_addr = signal_dict.get("addr")
            signal_length = signal_dict.get("length")
            signal_type = signal_dict.get("type")
            signal_value = read_register_signal[signal_addr: signal_addr + signal_length]
            if signal_type == "ulint":
                if signal_value:
                    signal_value = self.client.ulint_to_int(signal_value)
            elif signal_type == str:
                signal_value = self.client.str_decode(signal_value)
            elif signal_type == float:
                signal_value = self.client.float_decode(signal_value)
            elif isinstance(signal_type, (str, int, float)):
                signal_value = signal_value
            if not signal_value:
                signal_value = 0

            decode_dict[signal_name] = signal_value
            if signal_name == PLC_TIME_STAMP:
                self.plc_timestamp = signal_value
            # else:
            #     decode_dict[signal_name] = signal_value

        return decode_dict

    def _init(self):
        """初始化"""
        # 写给plc ack信号
        with self.client.locker:
            self.client.write(addr=REGISTER_ADDR[PLC_RESET]["addr"], val=0, datatype='int')  # 清零
            self.client.write(addr=REGISTER_ADDR[PLC_RESET_ACK]["addr"], val=1, datatype='int')
        
        time.sleep(0.02)  # 防止PLC没读到再写一次
        with self.client.locker:
            agent = self.client.read(addr=REGISTER_ADDR[PLC_RESET]["addr"])[0]
            if not agent:
                self.client.write(addr=REGISTER_ADDR[PLC_RESET]["addr"], val=0, datatype='int')  # 清零
                self.client.write(addr=REGISTER_ADDR[PLC_RESET_ACK]["addr"], val=1, datatype='int')
                logger.info(f"(write_signal) R0 agent addr:{REGISTER_ADDR[PLC_RESET_ACK]['addr']}, val:1")

        self.last_register_values.clear()
        self.sensor_last_timestamp_dict[SENSOR_PART_START] = 0
        for item in CAMERA_STATION_LIST:
            self.sensor_last_timestamp_dict[item] = 0
        self.sensor_last_timestamp_dict[SENSOR_PART_END] = 0
        
        self.sensor_last_part_dict.clear()
        self.sensor_last_part_dict[SENSOR_PART_START] = 0
        for item in CAMERA_STATION_LIST:
            self.sensor_last_part_dict[item] = 0
        self.sensor_last_part_dict[SENSOR_PART_END] = 0

        self.sensor_cur_part_dict.clear()
        self.sensor_cur_part_dict[SENSOR_PART_START] = 0
        for item in CAMERA_STATION_LIST:
            self.sensor_cur_part_dict[item] = 0
        self.sensor_cur_part_dict[SENSOR_PART_END] = 0

        self.part_dict = dict()
        self.processing_part_list = []
        self.warring_dict = {}
        self.plc_pause_start_time = 0
        self.is_sensor_error = False
        # 调用prod的物料重置接口
        ProdApiClient.reset_part()

    def get_pause_time(self, time_stamp):
        if self.plc_pause_start_time == 0:
            logger.error("Restarted without pausing!")
            return 0
        else:
            pause_time = time_stamp - self.plc_pause_start_time
            logger.debug(f"get pause_time:{pause_time}")
            if pause_time > 0:
                return pause_time
            else:
                logger.error(f"get pause_time:{pause_time} error, return 0.")
                return 0
            
    def run_part_start(self, time_stamp, sn=""):
        try:
            logger.debug(f"start call run_part_start")
            sensor_name = SENSOR_PART_START

            logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, run_part_start -- 1 --")
            part_start_sensor_last_value = self.sensor_last_timestamp_dict.get(sensor_name)
            logger.debug(f"sensor_last_value:{part_start_sensor_last_value}")

            if time_stamp == 0 or time_stamp == part_start_sensor_last_value:
                logger.debug(f"time_stamp {time_stamp}, last time_stamp {part_start_sensor_last_value} pass! "
                             f"run_part_start -- 2 --")
                return
            elif time_stamp == part_start_sensor_last_value:
                logger.debug(f"same time_stamp {time_stamp}, pass! run_part_start -- 3 --")
            elif time_stamp - part_start_sensor_last_value < MIN_SENSOR_TRIGGER_OFFSET:
                # 传感器在极短时间内重复触发的情况
                logger.debug(f"sensor_name {sensor_name} trigger repeat error! time_stamp:{time_stamp} - "
                             f"sensor_last_timestamp {part_start_sensor_last_value} < {MIN_SENSOR_TRIGGER_OFFSET} "
                             f"run_part_start -- 4 --")
                self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]["trigger_repeat_error"]
                logger.debug(f"warring_dict: {self.warring_dict}")
                raise Exception(f"sensor_name {sensor_name} trigger repeat error! time_stamp:{time_stamp} - "
                                f"sensor_last_timestamp {part_start_sensor_last_value} < {MIN_SENSOR_TRIGGER_OFFSET}")

            elif time_stamp - part_start_sensor_last_value < MIN_PART_TIME_INTERVAL:
                # 在极短时间wu触发的情况
                trigger_internal = time_stamp - self.sensor_last_timestamp_dict[sensor_name]
                logger.error(f"sensor_name{sensor_name} trigger internal: {trigger_internal} < min value: "
                             f"{MIN_PART_TIME_INTERVAL}! run_part_start -- 5 --")
                # 将传感器重复触发的警告写给PLC寄存器
                self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]["part_interval_error"]
                logger.debug(f"warring_dict: {self.warring_dict}")
                raise Exception(f"sensor_name{sensor_name} trigger internal: {trigger_internal} < min value: "
                                f"{MIN_PART_TIME_INTERVAL}!")

            else:
                logger.debug(f"sensor_name:{sensor_name} run_part_start -- 6 --")

                # 创建一个新物料
                part_id = "SN_" + str(time_stamp)
                sn = sn.strip()

                if IS_PLC_READ_SN:
                    with part_dict_lock:
                        if sn.upper() == PLC_DECODE_ERROR or not sn:
                            sn = part_id
                            proxy.part_id_dict[part_id] = part_id
                            logger.warning(f"plc read sn failed, part_id {part_id} ")
                        else:
                            proxy.part_id_dict[part_id] = sn

                self.processing_part_list.append(part_id)
                logger.debug(f"add {part_id} to processing_part_list")
                logger.debug(f"processing_part_list: {self.processing_part_list}")

                new_part = {
                    "status": True,
                    "pause_time": {SENSORS_MAP[sensor_name]["next_sensor"]: 0},
                    "cur_sensor": SENSORS_MAP[sensor_name]["next_sensor"],
                    sensor_name: time_stamp
                }
                self.part_dict[part_id] = new_part
                self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                self.sensor_cur_part_dict[sensor_name] = part_id
                # 调用prod的物料开始接口
                logger.debug(f"run_part_start -- 7 --")
                logger.info(f"sensor_name:{sensor_name} add new part {part_id}:{new_part}")
                logger.info(f"processing_part_list: {self.processing_part_list}")

                if IS_PLC_READ_SN and sn:
                    # ProdApiClient.start_part(PART_TYPE, sn)
                    Thread(target=ProdApiClient.start_part, args=(PART_TYPE, sn)).start()
                    Thread(target=PartProcessor.reset_station_camera, args=(sensor_name, sn,)).start()
                else:
                    # ProdApiClient.start_part(PART_TYPE, part_id)
                    Thread(target=ProdApiClient.start_part, args=(PART_TYPE, part_id)).start()
                    Thread(target=PartProcessor.reset_station_camera, args=(sensor_name, part_id,)).start()

                logger.debug(f"sensor_name:{sensor_name} run_part_start -- 8 --")
        except Exception as e:
            logger.error(f"sensor {sensor_name} last_timestamp: {self.sensor_last_timestamp_dict[sensor_name]}")
            logger.error(f"sensor_last_timestamp_dict: {self.sensor_last_timestamp_dict}")
            logger.error(f"sensor_last_part_dict: {self.sensor_last_part_dict}")
            logger.error(f"sensor_cur_part_dict: {self.sensor_cur_part_dict}")
            logger.error(f"processing_part_list: {self.processing_part_list}")
            logger.error(f"run_part_start failed, {e}", exc_info=True)

    def camera_station(self, sensor_name, time_stamp):
        try:
            logger.debug(f"start call camera_station")
            logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, camera_station -- 1 --")
            logger.debug(f"sensor_last_timestamp_dict: {self.sensor_last_timestamp_dict}")
            logger.debug(f"sensor {sensor_name} last_timestamp: {self.sensor_last_timestamp_dict[sensor_name]}")
            logger.debug(f"sensor_last_part_dict: {self.sensor_last_part_dict}")
            logger.debug(f"processing_part_list: {self.processing_part_list}")

            last_part_id = self.sensor_last_part_dict[sensor_name]
            pre_sensor = SENSORS_MAP[sensor_name]["last_sensor"]
            if not last_part_id:
                if self.processing_part_list and self.sensor_last_part_dict[pre_sensor] != 0:
                    cur_part_id = self.processing_part_list[0]
                else:
                    cur_part_id = None
            else:
                last_part_index = self.processing_part_list.index(last_part_id)

                if last_part_index + 1 >= len(self.processing_part_list):
                    # 如果上一次处理的part是列表中的最后一个，则当前的part id为None，即没有part
                    cur_part_id = None
                    logger.debug(f"sensor_name :{sensor_name}, last_part_id: {last_part_id}, "
                                 f"last_part_index: {last_part_index}; len(processing_part_list): "
                                 f"{len(self.processing_part_list)}")
                elif self.sensor_last_part_dict[sensor_name] == self.sensor_last_part_dict[pre_sensor]:
                    # for long time delay, pre sensor and cur sensor trigger time in the same signal dict
                    pre_sensor_cur_part = self.sensor_cur_part_dict[pre_sensor]
                    pre_sensor_last_part = self.sensor_last_part_dict[pre_sensor]
                    if pre_sensor_cur_part in self.part_dict.keys() and pre_sensor_cur_part != pre_sensor_last_part:
                        pre_sensor_cur_time = self.part_dict[pre_sensor_cur_part][pre_sensor]
                        sensor_offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                        if ((time_stamp - pre_sensor_cur_time) / sensor_offset_time) < MARGIN_OFF_OFFSET_TIME:
                            cur_part_id = pre_sensor_cur_part
                            logger.debug(f"sensor_name:{sensor_name} pre_sensor_time: {pre_sensor_cur_time} "
                                         f"cur_part_id: {cur_part_id}.")
                        else:
                            cur_part_id = None
                            logger.debug(f"pre_sensor:{pre_sensor} has not new part processed.")
                    else:
                        cur_part_id = None
                        logger.debug(f"pre_sensor:{pre_sensor} has not new part processed.")
                else:
                    cur_part_id = self.processing_part_list[last_part_index + 1]

            logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, cur_part_id:{cur_part_id} "
                         f"camera_station -- 2 --")

            sensor_last_timestamp = self.sensor_last_timestamp_dict[sensor_name]
            if time_stamp == 0 or time_stamp == sensor_last_timestamp:
                logger.debug(f"camera_station -- 3 --")
                if cur_part_id is None:
                    logger.debug(f"camera_station -- 4 --")
                    return
                else:
                    if self.part_dict.get(cur_part_id) is None:
                        raise Exception(f"cur_part_id {cur_part_id} not in part_dict {list(self.part_dict.keys())}")

                    part_last_sensor_stamp = self.part_dict[cur_part_id].get(pre_sensor)
                    logger.debug(f"part_last_sensor_stamp: {part_last_sensor_stamp}")
                    if part_last_sensor_stamp is None:
                        logger.debug(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                     f"{self.part_dict[cur_part_id]}, camera_station-- 5 --")
                        raise Exception(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                        f"{self.part_dict[cur_part_id]}")

                    pause_time = self.part_dict[cur_part_id]["pause_time"][self.part_dict[cur_part_id]["cur_sensor"]]
                    offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                    time_offset_max_limit = SENSORS_MAP[sensor_name]["offset_max_limit"]
                    part_trigger_max_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_max_limit
                    logger.debug(f"pause_time: {pause_time} offset_time: {offset_time}  camera_station -- 6 --")
                    if (
                            sensor_name not in self.part_dict[cur_part_id].keys() and
                            self.plc_timestamp > part_trigger_max_limit
                    ):
                        # 超过时间没触发传感器
                        self.part_dict[cur_part_id]["status"] = False
                        # 将该物料的ID和该物料应该经过的时间填写到当前传感器？
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        part_expect_time = part_last_sensor_stamp + pause_time + offset_time
                        self.sensor_last_timestamp_dict[sensor_name] = part_expect_time
                        self.part_dict[cur_part_id][sensor_name] = part_expect_time
                        next_sensor = SENSORS_MAP[sensor_name]["next_sensor"]
                        if next_sensor not in self.part_dict[cur_part_id]["pause_time"].keys():
                            self.part_dict[cur_part_id]["cur_sensor"] = next_sensor
                            self.part_dict[cur_part_id]["pause_time"][next_sensor] = 0

                        logger.debug(f"Part not triggered during expected time. camera_station -- 7 --")
                        logger.debug(f"sensor_name:{sensor_name}, cur_part_id: {cur_part_id}, part_last_sensor_stamp: "
                                     f"{part_last_sensor_stamp}; plc_timestamp:{self.plc_timestamp} > "
                                     f"part_trigger_max_limit: {part_trigger_max_limit}")
                        logger.debug(f"part_dict:{self.part_dict[cur_part_id]}")
                        logger.debug(f"processing_part_list: {self.processing_part_list}")

                        # TODO 如果漏相机复位补救措施没生效， 可无需作复位操作。
                        # camera reset
                        # Thread(target=PartProcessor.reset_station_camera, args=(sensor_name,)).start()
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]["no_trigger_error"]
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"Part not triggered during expected time. sensor_name:{sensor_name}, "
                                        f"cur_part_id: {cur_part_id}, part_last_sensor_stamp: {part_last_sensor_stamp}; "
                                        f"plc_timestamp:{self.plc_timestamp} > part_trigger_max_limit: "
                                        f"{part_trigger_max_limit}"
                                        )
                    else:
                        # 正常轮询的情况
                        logger.debug("camera_station pass -- 8 --")

                    return
            else:
                if cur_part_id is None:
                    if time_stamp - sensor_last_timestamp < MIN_SENSOR_TRIGGER_OFFSET:
                        # 在极短时间重复触发的情况
                        logger.error(f"sensor_name: {sensor_name} trigger repeat error!")
                        logger.error(f"time_stamp: {time_stamp} - sensor_last_timestamp: {sensor_last_timestamp} < "
                                     f"MIN_SENSOR_TRIGGER_OFFSET: {MIN_SENSOR_TRIGGER_OFFSET} camera_station -- 9 --")
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_repeat_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"sensor_name {sensor_name} trigger repeat error! time_stamp: {time_stamp} - "
                                        f"sensor_last_timestamp: {sensor_last_timestamp} < MIN_SENSOR_TRIGGER_OFFSET: "
                                        f"{MIN_SENSOR_TRIGGER_OFFSET}")
                    elif time_stamp - sensor_last_timestamp < MIN_PART_TIME_INTERVAL:
                        # 在极短时间wu触发的情况
                        logger.debug(f"sensor_name: {sensor_name} is triggered not in correct time!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                     f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL} camera_station -- 10 --")
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['part_interval_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"sensor_name {sensor_name} is triggered not in correct time!")
                    else:
                        # 当前传感器之前的传感器存在未触发的情况
                        self.warring_dict[pre_sensor] = SENSORS_MAP[pre_sensor]["no_trigger_error"]
                        logger.debug(f"warring_dict: {self.warring_dict}")

                        # TODO 需要初始化，防止下个物料多图错图
                        sensor_index = CAMERA_STATION_LIST.index(sensor_name)
                        logger.error(f"{SENSOR_PART_START} {CAMERA_STATION_LIST[:sensor_index]} miss trigger!")

                        new_part = {
                            "status": False,
                            "pause_time": {SENSORS_MAP[sensor_name]["next_sensor"]: 0},
                            "cur_sensor": SENSORS_MAP[sensor_name]["next_sensor"],
                        }
                        tmp_total_offset = 0
                        for item in CAMERA_STATION_LIST[:sensor_index + 1][::-1]:
                            new_part[item] = time_stamp - tmp_total_offset
                            tmp_total_offset += SENSORS_MAP[item]["offset_time"]

                        new_part[SENSOR_PART_START] = time_stamp - tmp_total_offset
                        part_start_timestamp = time_stamp - tmp_total_offset
                        part_id = "SN_" + str(part_start_timestamp)

                        for item in CAMERA_STATION_LIST[:sensor_index + 1][::-1]:
                            if new_part[item] > self.sensor_last_timestamp_dict[item]:
                                self.sensor_last_timestamp_dict[item] = new_part[item]
                                self.sensor_cur_part_dict[item] = part_id

                        if new_part[SENSOR_PART_START] > self.sensor_last_timestamp_dict[SENSOR_PART_START]:
                            self.sensor_last_timestamp_dict[SENSOR_PART_START] = new_part[SENSOR_PART_START]
                            self.sensor_cur_part_dict[SENSOR_PART_START] = part_id

                        if len(self.processing_part_list) == 0:
                            self.processing_part_list.append(part_id)
                        elif part_start_timestamp > int(self.processing_part_list[-1][3:]):
                            self.processing_part_list.append(part_id)
                        else:
                            for i, item in enumerate(self.processing_part_list):
                                if int(item[3:]) < part_start_timestamp:
                                    continue
                                else:
                                    self.processing_part_list.insert(i, part_id)
                                    break

                        logger.warning(f"add missing part: {part_id}: {new_part} to part_dict")
                        logger.debug(f"processing_part_list {self.processing_part_list}")
                        self.part_dict[part_id] = new_part
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.sensor_cur_part_dict[sensor_name] = part_id
                        logger.debug(f"sensor_name: {sensor_name}, time_stamp: {time_stamp}, camera_station -- 11 --")
                        raise Exception(f"cur_part {part_id} not triggered before sensor_name: {sensor_name} "
                                        f"time_stamp: {time_stamp}")
                else:
                    if self.part_dict.get(cur_part_id) is None:
                        raise Exception(f"cur_part_id {cur_part_id} not in part_dict {list(self.part_dict.keys())}")

                    part_last_sensor_stamp = self.part_dict[cur_part_id].get(pre_sensor)
                    logger.debug(f"part_last_sensor_stamp: {part_last_sensor_stamp}")
                    if part_last_sensor_stamp is None:
                        logger.debug(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                     f"{self.part_dict[cur_part_id]}, camera_station-- 12 --")
                        raise Exception(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                        f"{self.part_dict[cur_part_id]}")
                    
                    pause_time = self.part_dict[cur_part_id]["pause_time"][self.part_dict[cur_part_id]["cur_sensor"]]
                    offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                    time_offset_min_limit = SENSORS_MAP[sensor_name]["offset_min_limit"]
                    part_trigger_min_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_min_limit
                    time_offset_max_limit = SENSORS_MAP[sensor_name]["offset_max_limit"]
                    part_trigger_max_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_max_limit
                    logger.debug(f"pause_time: {pause_time} offset_time: {offset_time}  camera_station -- 13 --")

                    if time_stamp - sensor_last_timestamp < MIN_SENSOR_TRIGGER_OFFSET:
                        # 在极短时间重复触发的情况
                        self.part_dict[cur_part_id]["status"] = False
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_repeat_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")

                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} trigger repeat error!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp: {sensor_last_timestamp} < "
                                     f"MIN_SENSOR_TRIGGER_OFFSET: {MIN_SENSOR_TRIGGER_OFFSET} camera_station -- 14 --")
                        raise Exception(f"sensor_name {sensor_name} trigger repeat error! time_stamp: {time_stamp} - "
                                        f"sensor_last_timestamp: {sensor_last_timestamp} < MIN_SENSOR_TRIGGER_OFFSET: "
                                        f"{MIN_SENSOR_TRIGGER_OFFSET} ")
                    elif time_stamp - sensor_last_timestamp < MIN_PART_TIME_INTERVAL:
                        # 在极短时间wu触发的情况
                        self.part_dict[cur_part_id]["status"] = False
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.part_dict[cur_part_id][sensor_name] = time_stamp
                        self.part_dict[cur_part_id]["cur_sensor"] = SENSORS_MAP[sensor_name]["next_sensor"]
                        self.part_dict[cur_part_id]["pause_time"][SENSORS_MAP[sensor_name]["next_sensor"]] = 0

                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} "
                                     f"is triggered not in correct time!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                     f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL} camera_station -- 15 --")
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['part_interval_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"sensor_name: {sensor_name} is triggered not in correct time! time_stamp: "
                                        f"{time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                        f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL}")
                    elif time_stamp < part_trigger_min_limit or time_stamp > part_trigger_max_limit:
                        # 传感器触发时间不正确
                        self.part_dict[cur_part_id]["status"] = False
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.part_dict[cur_part_id][sensor_name] = time_stamp
                        self.part_dict[cur_part_id]["cur_sensor"] = SENSORS_MAP[sensor_name]["next_sensor"]
                        self.part_dict[cur_part_id]["pause_time"][SENSORS_MAP[sensor_name]["next_sensor"]] = 0

                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_out_range_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} trigger not in correct time!. "
                                     f"camera_station -- 16 --")
                        logger.debug(f"part_trigger_min_limit: {part_trigger_min_limit} < time_stamp:{time_stamp} < "
                                     f"part_trigger_max_limit:{part_trigger_max_limit}")
                        logger.debug(f"part_last_sensor_stamp:{part_last_sensor_stamp}, pause_time:{pause_time}, "
                                     f"offset_time:{offset_time}")
                        # TODO 若需修复错误， 可开启
                        # if time_stamp > part_trigger_max_limit:
                        #     Thread(target=PartProcessor.reset_station_camera, args=(sensor_name,)).start()

                        raise Exception(f"sensor_name {sensor_name} cur_part {cur_part_id} is triggered not in correct "
                                        f"time! time_stamp: {time_stamp} out of range: [{part_trigger_min_limit}, "
                                        f"{part_trigger_max_limit}]")
                    else:
                        logger.debug(f"sensor_name:{sensor_name} time_stamp:{time_stamp} cur_part: {cur_part_id}"
                                     f"camera_station -- 17 --")
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.part_dict[cur_part_id][sensor_name] = time_stamp
                        self.part_dict[cur_part_id]["cur_sensor"] = SENSORS_MAP[sensor_name]["next_sensor"]
                        self.part_dict[cur_part_id]["pause_time"][SENSORS_MAP[sensor_name]["next_sensor"]] = 0

                        if IS_PLC_READ_SN:
                            sn = proxy.part_id_dict.get(cur_part_id, cur_part_id)
                            Thread(target=PartProcessor.reset_station_camera, args=(sensor_name, sn,)).start()
                            if sn == cur_part_id:
                                raise Exception(f"sn {cur_part_id} is not from the PCL_READ_SN")
                        else:
                            Thread(target=PartProcessor.reset_station_camera, args=(sensor_name, cur_part_id,)).start()

                        logger.info(f"cur_part {cur_part_id}: {self.part_dict[cur_part_id]}")
                        logger.debug(f"camera_station -- 18 --")
            
            logger.debug(f"camera_station -- 19 --")
        except Exception as e:
            logger.error(f"sensor {sensor_name} last_timestamp: {self.sensor_last_timestamp_dict[sensor_name]}")
            logger.error(f"sensor_last_timestamp_dict: {self.sensor_last_timestamp_dict}")
            logger.error(f"sensor_last_part_dict: {self.sensor_last_part_dict}")
            logger.error(f"sensor_cur_part_dict: {self.sensor_cur_part_dict}")
            logger.error(f"processing_part_list: {self.processing_part_list}")
            logger.error(f"camera_station failed, {e}", exc_info=True)

    @staticmethod
    def reset_station_camera(sensor_name, part_id):
        logger.info(f"wait to reset camera at station {sensor_name}.")
        for i in range(int(SENSORS_MAP[sensor_name]["reset_camera_wait_time"]*200)):
            while pause_event.is_set():
                time.sleep(.005)
            time.sleep(.005)

        for camera_id in SENSORS_MAP[sensor_name]["sensor_to_camera"]:
            ProdApiClient.reset_camera(camera_id, part_id)  # 调用prod的相机重置接口
            time.sleep(0.01)
        logger.info(f"reset camera at {sensor_name} over.")

    def part_end(self, time_stamp):
        try:
            logger.debug(f"start call part_end")
            sensor_name = SENSOR_PART_END
            logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, part_end -- 1 --")
            logger.debug(f"sensor_last_timestamp_dict: {self.sensor_last_timestamp_dict}")
            logger.debug(f"sensor {sensor_name} last_timestamp: {self.sensor_last_timestamp_dict[sensor_name]}")
            logger.debug(f"sensor_last_part_dict: {self.sensor_last_part_dict}")
            logger.debug(f"processing_part_list: {self.processing_part_list}")

            last_part_id = self.sensor_last_part_dict[sensor_name]
            pre_sensor = SENSORS_MAP[sensor_name]["last_sensor"]
            if not last_part_id:
                if self.processing_part_list and self.sensor_last_part_dict[pre_sensor] != 0:
                    cur_part_id = self.processing_part_list[0]
                else:
                    cur_part_id = None
            else:
                last_part_index = self.processing_part_list.index(last_part_id)
                if last_part_index + 1 >= len(self.processing_part_list):
                    # 如果上一次处理的part是列表中的最后一个，则当前的part id为None，即没有part
                    cur_part_id = None
                    logger.debug(f"sensor_name :{sensor_name}, last_part_id: {last_part_id}, "
                                 f"last_part_index: {last_part_index}; len(processing_part_list): "
                                 f"{len(self.processing_part_list)}")

                elif self.sensor_last_part_dict[pre_sensor] == self.sensor_last_part_dict[sensor_name]:
                    # for long time delay, pre sensor and cur sensor trigger time in the same signal dict
                    pre_sensor_cur_part = self.sensor_cur_part_dict[pre_sensor]
                    pre_sensor_last_part = self.sensor_last_part_dict[pre_sensor]
                    if pre_sensor_cur_part in self.part_dict.keys() and pre_sensor_cur_part != pre_sensor_last_part:
                        pre_sensor_cur_time = self.part_dict[pre_sensor_cur_part][pre_sensor]
                        sensor_offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                        if ((time_stamp - pre_sensor_cur_time) / sensor_offset_time) < MARGIN_OFF_OFFSET_TIME:
                            cur_part_id = pre_sensor_cur_part
                            logger.debug(f"sensor_name:{sensor_name} pre_sensor_time: {pre_sensor_cur_time} "
                                         f"cur_part_id: {cur_part_id}.")
                        else:
                            cur_part_id = None
                            logger.debug(f"pre_sensor:{pre_sensor} has not new part processed.")
                    else:
                        cur_part_id = None
                        logger.debug(f"pre_sensor:{pre_sensor} has not new part processed.")
                else:
                    cur_part_id = self.processing_part_list[last_part_index + 1]

            logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, cur_part_id:{cur_part_id} "
                         f"part_end -- 2 --")

            sensor_last_timestamp = self.sensor_last_timestamp_dict[sensor_name]
            if time_stamp == 0 or time_stamp == sensor_last_timestamp:
                logger.debug(f"part_end -- 3 --")
                if cur_part_id is None:
                    logger.debug(f"part_end -- 4 --")
                    return
                else:
                    if self.part_dict.get(cur_part_id) is None:
                        raise Exception(f"cur_part_id {cur_part_id} not in part_dict {list(self.part_dict.keys())}")

                    part_last_sensor_stamp = self.part_dict[cur_part_id].get(pre_sensor)
                    logger.debug(f"part_last_sensor_stamp: {part_last_sensor_stamp}")

                    if part_last_sensor_stamp is None:
                        logger.debug(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                     f"{self.part_dict[cur_part_id]}, part_end-- 5 --")
                        raise Exception(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                        f"{self.part_dict[cur_part_id]}")

                    pause_time = self.part_dict[cur_part_id]["pause_time"][self.part_dict[cur_part_id]["cur_sensor"]]
                    offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                    time_offset_max_limit = SENSORS_MAP[sensor_name]["offset_max_limit"]
                    part_trigger_max_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_max_limit
                    logger.debug(f"pause_time: {pause_time} offset_time: {offset_time}  part_end -- 6 --")

                    if (
                            sensor_name not in self.part_dict[cur_part_id].keys() and
                            self.plc_timestamp > part_trigger_max_limit
                    ):
                        # 超过时间没触发传感器
                        self.part_dict[cur_part_id]["status"] = False
                        logger.debug(f"Part not triggered during expected time. part_end -- 7 --")
                        logger.debug(f"sensor_name:{sensor_name}, cur_part_id: {cur_part_id}, part_last_sensor_stamp: "
                                     f"{part_last_sensor_stamp}; plc_timestamp:{self.plc_timestamp} > "
                                     f"part_trigger_max_limit: {part_trigger_max_limit}")

                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['no_trigger_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")

                        # 传感器触发时间不正确
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        # ! 把料从队列中剔除出去
                        self.pop_false_part_from_queue(cur_part_id)

                        raise Exception(f"Part not triggered during expected time. sensor_name:{sensor_name}, "
                                        f"cur_part_id: {cur_part_id}, part_last_sensor_stamp: {part_last_sensor_stamp}; "
                                        f"plc_timestamp:{self.plc_timestamp} > part_trigger_max_limit: "
                                        f"{part_trigger_max_limit}"
                                        )
                    else:
                        # 正常轮询的情况
                        logger.debug("part_end pass -- 8 --")

                    return

            else:
                if cur_part_id is None:
                    if time_stamp - sensor_last_timestamp < MIN_SENSOR_TRIGGER_OFFSET:
                        # 在极短时间重复触发的情况
                        logger.error(f"sensor_name: {sensor_name} trigger repeat error!")
                        logger.error(f"time_stamp: {time_stamp} - sensor_last_timestamp: {sensor_last_timestamp} < "
                                     f"MIN_SENSOR_TRIGGER_OFFSET: {MIN_SENSOR_TRIGGER_OFFSET} part_end -- 9 --")

                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_repeat_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"sensor_name {sensor_name} trigger repeat error! time_stamp: {time_stamp} - "
                                        f"sensor_last_timestamp: {sensor_last_timestamp} < MIN_SENSOR_TRIGGER_OFFSET: "
                                        f"{MIN_SENSOR_TRIGGER_OFFSET}")
                    elif time_stamp - sensor_last_timestamp < MIN_PART_TIME_INTERVAL:
                        # 物料间距时间过短
                        logger.debug(f"sensor_name: {sensor_name} is triggered not in correct time!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                     f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL} camera_station -- 10 --")

                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['part_interval_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        
                        # self.client.write(addr=REGISTER_ADDR[PART_RESULT_MSG]["addr"], val=1, datatype="int")
                        raise Exception(f"sensor_name {sensor_name} is triggered not in correct time")
                    else:
                        # 当前传感器之前的传感器存在未触发的情况
                        self.warring_dict[pre_sensor] = SENSORS_MAP[pre_sensor]['no_trigger_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        # S0没触发的情况 TODO 需要初始化，防止下个物料多图错图
                        logger.error(f"{SENSOR_PART_START} {CAMERA_STATION_LIST} miss trigger!")
                        new_part = {
                            "status": False,
                            "pause_time": {},
                            "cur_sensor": None,
                        }
                        tmp_total_offset = 0
                        new_part[sensor_name] = time_stamp - tmp_total_offset
                        tmp_total_offset += SENSORS_MAP[sensor_name]["offset_time"]
                        
                        for item in CAMERA_STATION_LIST[::-1]:
                            new_part[item] = time_stamp - tmp_total_offset
                            tmp_total_offset += SENSORS_MAP[item]["offset_time"]

                        new_part[SENSOR_PART_START] = time_stamp - tmp_total_offset

                        part_start_timestamp = time_stamp - tmp_total_offset
                        part_id = "SN_" + str(part_start_timestamp)

                        if len(self.processing_part_list) == 0:
                            self.processing_part_list.append(part_id)
                        elif part_start_timestamp > int(self.processing_part_list[-1][3:]):
                            self.processing_part_list.append(part_id)
                        else:
                            for i, item in enumerate(self.processing_part_list):
                                if int(item[3:]) < part_start_timestamp:
                                    continue
                                else:
                                    self.processing_part_list.insert(i, part_id)
                                    break

                        self.part_dict[part_id] = new_part
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.sensor_cur_part_dict[sensor_name] = part_id
                        logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, part_end -- 11 --")
                        logger.debug(f"part_dict:{self.part_dict[part_id]}")
                        logger.debug(f"new processing_part_list {self.processing_part_list}")

                        # 把料从队列中剔除出去
                        self.pop_false_part_from_queue(part_id)

                        raise Exception(f"cur_part {part_id} not triggered before sensor_name: {sensor_name} "
                                        f"time_stamp: {time_stamp}")
                else:
                    if self.part_dict.get(cur_part_id) is None:
                        raise Exception(f"cur_part_id {cur_part_id} not in part_dict {list(self.part_dict.keys())}")

                    part_last_sensor_stamp = self.part_dict[cur_part_id].get(pre_sensor)
                    logger.debug(f"part_last_sensor_stamp: {part_last_sensor_stamp}")
                    if part_last_sensor_stamp is None:
                        logger.debug(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                     f"{self.part_dict[cur_part_id]}, part_end-- 12 --")
                        raise Exception(f"previous sensor:{pre_sensor} not in part {cur_part_id}: "
                                        f"{self.part_dict[cur_part_id]}")
                    
                    pause_time = self.part_dict[cur_part_id]["pause_time"][self.part_dict[cur_part_id]["cur_sensor"]]
                    offset_time = SENSORS_MAP[sensor_name]["offset_time"]
                    time_offset_min_limit = SENSORS_MAP[sensor_name]["offset_min_limit"]
                    part_trigger_min_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_min_limit
                    time_offset_max_limit = SENSORS_MAP[sensor_name]["offset_max_limit"]
                    part_trigger_max_limit = part_last_sensor_stamp + pause_time + offset_time * time_offset_max_limit
                    logger.debug(f"pause_time: {pause_time} offset_time: {offset_time}  part_end -- 13 --")

                    if time_stamp - sensor_last_timestamp < MIN_SENSOR_TRIGGER_OFFSET:
                        # 在极短时间重复触发的情况
                        self.part_dict[cur_part_id]["status"] = False
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_repeat_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")

                        # 把料从队列中剔除出去
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.pop_false_part_from_queue(cur_part_id)

                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} trigger repeat error!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp: {sensor_last_timestamp} < "
                                     f"MIN_SENSOR_TRIGGER_OFFSET: {MIN_SENSOR_TRIGGER_OFFSET} part_end -- 14 --")
                        raise Exception(f"sensor_name {sensor_name} trigger repeat error! time_stamp: {time_stamp} - "
                                        f"sensor_last_timestamp: {sensor_last_timestamp} < MIN_SENSOR_TRIGGER_OFFSET: "
                                        f"{MIN_SENSOR_TRIGGER_OFFSET} ")
                    elif time_stamp - sensor_last_timestamp < MIN_PART_TIME_INTERVAL:
                        # 在极短时间wu触发的情况
                        self.part_dict[cur_part_id]["status"] = False
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        # ! 把料从队列中剔除出去
                        # self.output_part_result(cur_part_id, time_stamp)
                        self.pop_false_part_from_queue(cur_part_id)

                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} "
                                     f"is triggered not in correct time!")
                        logger.debug(f"time_stamp: {time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                     f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL} part_end -- 15 --")
                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['part_interval_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        raise Exception(f"sensor_name: {sensor_name} is triggered not in correct time! time_stamp: "
                                        f"{time_stamp} - sensor_last_timestamp:{sensor_last_timestamp} < "
                                        f"MIN_PART_TIME_INTERVAL: {MIN_PART_TIME_INTERVAL}")
                    elif time_stamp < part_trigger_min_limit or time_stamp > part_trigger_max_limit:
                        # 传感器触发时间不正确
                        self.part_dict[cur_part_id]["status"] = False
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        # ! 把料从队列中剔除出去
                        # self.output_part_result(cur_part_id, time_stamp)
                        self.pop_false_part_from_queue(cur_part_id)

                        self.warring_dict[sensor_name] = SENSORS_MAP[sensor_name]['trigger_out_range_error']
                        logger.debug(f"warring_dict: {self.warring_dict}")
                        logger.debug(f"sensor_name: {sensor_name} cur_part: {cur_part_id} trigger not in correct time!. "
                                     f"part_end -- 16 --")
                        logger.debug(f"part_trigger_min_limit: {part_trigger_min_limit} < time_stamp:{time_stamp} < "
                                     f"part_trigger_max_limit:{part_trigger_max_limit}")
                        logger.debug(f"part_last_sensor_stamp:{part_last_sensor_stamp}, pause_time:{pause_time}, "
                                     f"offset_time:{offset_time}")

                        raise Exception(f"sensor_name {sensor_name} cur_part {cur_part_id} is triggered not in correct "
                                        f"time! time_stamp: {time_stamp} out of range: [{part_trigger_min_limit}, "
                                        f"{part_trigger_max_limit}]")
                    else:
                        logger.debug(f"part_end -- 17 --")
                        logger.debug(f"sensor_name: {sensor_name}, time_stamp: {time_stamp}, cur_part: {cur_part_id}")
                        self.sensor_last_timestamp_dict[sensor_name] = time_stamp
                        self.sensor_cur_part_dict[sensor_name] = cur_part_id
                        self.part_dict[cur_part_id][sensor_name] = time_stamp

                        self.output_part_result(cur_part_id, time_stamp)
                        logger.debug(f"part_end -- 18 --")

        except Exception as e:
            logger.error(f"sensor {sensor_name} last_timestamp: {self.sensor_last_timestamp_dict[sensor_name]}")
            logger.error(f"sensor_last_timestamp_dict: {self.sensor_last_timestamp_dict}")
            logger.error(f"sensor_last_part_dict: {self.sensor_last_part_dict}")
            logger.error(f"sensor_cur_part_dict: {self.sensor_cur_part_dict}")
            logger.error(f"processing_part_list: {self.processing_part_list}")
            logger.error(f"part_end failed, {e}", exc_info=True)

    def output_part_result(self, ipc_part_id, time_stamp):
        sensor_name = SENSOR_PART_END
        cur_part = self.part_dict.get(ipc_part_id)
        if cur_part is None:
            logger.debug(f"part {ipc_part_id} not in part_dict {list(self.part_dict.keys())}")
            return
        msg = ""
        logger.debug(f"cur_part {ipc_part_id}: {cur_part} output_part_result -- 1 --")

        if cur_part["status"] is False:
            part_result = NG2
            part_id = ipc_part_id
            logger.debug(f"output_part_result -- 2 --")
        else:
            logger.debug(f"output_part_result -- 3 --")
            part_id = proxy.part_id_dict.get(ipc_part_id, ipc_part_id)
            if part_id == ipc_part_id:
                logger.error("part_id not in cache!")
                part_result = NG1
                logger.debug(f"cur_part_id:{ipc_part_id}, part_id_dict {proxy.part_id_dict} "
                             f"output_part_result -- 4 --")
            else:
                logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, output_part_result -- 5 --")
                num = 0
                while num < 10:
                    # logger.info(f"try to get part_id:{part_id}, num:{num}")
                    prod_part_result = proxy.part_result_dict.get(part_id)
                    logger.debug(f"try to get part_id:{part_id}, num:{num}\tprod_part_result: {prod_part_result}")

                    if prod_part_result is not None:
                        part_result = prod_part_result
                        logger.debug(f"get part_id_data successful, "
                                     f"part_result_dict:{proxy.part_result_dict}, num:{num}")
                        break
                    num += 1
                    time.sleep(0.02)
                else:
                    logger.warning(f"part_id: {part_id} quit while get part_id_data [NG3]_before")
                    logger.warning(f"proxy.part_result_dict:{proxy.part_result_dict}, num:{num}")
                    # part_result = NG2
                    part_result = NG1

                    # Thread(target=server.receiver_sn_remark(part_id, "超时物料"), args=(part_id,)).start()

                    try:
                        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
                        insert_data_to_db(part_id, 0, 'NG', '', 'NG', 'Unitx', "超时物料", timestamp, True)
                        logger.warning(f"output_part_result, insert_data_to_db, sn:{part_id}, remark: 超时物料")
                    except Exception as e:
                        logger.error(f"insert_data_to_db failed! {e}", exc_info=True)

                    logger.debug(f"output_part_result -- 6 --")
                    logger.debug(f"part_id: {part_id} quit while get part_id_data [NG3], part_result: {part_result}")

        logger.debug(f"output_part_result -- 7 --")

        # 写给plc结果
        with self.client.locker:
            self.client.write(addr=REGISTER_ADDR[PART_RESULT]['addr'] + part_result, val=1, datatype="int")
            self.client.write(addr=REGISTER_ADDR[PART_RESULT_SN]['addr'], val=str(part_id), datatype="str")
            self.client.write(addr=REGISTER_ADDR[PART_RESULT_MSG]['addr'], val=msg, datatype="str")
        logger.info(f"(write_signal) S1 sn:{part_id}, result:{part_result}")

        # 删除缓存
        cur_part_id_dict = self.part_dict.pop(ipc_part_id, None)
        log_to_dict.info(f"cur_part_id_dict | {cur_part_id_dict}")

        if len(self.processing_part_list) >= MAX_PART_IN_PROCESS_NUM:
            self.processing_part_list.pop(0)

        logger.debug(f"sensor_name:{sensor_name}, time_stamp:{time_stamp}, part_end -- 25 --")

        if proxy.part_id_dict.get(ipc_part_id) is not None:
            with part_dict_lock:
                proxy.part_id_dict.pop(ipc_part_id, None)
        else:
            logger.error(f"pop ipc_part_id:{ipc_part_id} failed, part_id_dict:{proxy.part_id_dict}")
        if proxy.part_result_dict.get(part_id) is not None:
            with part_result_dict_lock:
                proxy.part_result_dict.pop(part_id, None)
        else:
            logger.error(f"pop part_id:{part_id} failed, part_result_dict:{proxy.part_result_dict}")

    def pop_false_part_from_queue(self, part_id):
        self.part_dict.pop(part_id, None)
        logger.warning(f"pop_false_part_from_queue {part_id}")

        if len(self.processing_part_list) >= MAX_PART_IN_PROCESS_NUM:
            self.processing_part_list.pop(0)
        if proxy.part_id_dict.get(part_id) is not None:
            with part_dict_lock:
                proxy.part_id_dict.pop(part_id, None)
        else:
            logger.error(f"pop_ ipc_part_id:{part_id} failed, part_id_dict:{proxy.part_id_dict}")

        if proxy.part_result_dict.get(part_id) is not None:
            with part_result_dict_lock:
                proxy.part_result_dict.pop(part_id, None)
        else:
            logger.error(f"pop_ part_id:{part_id} failed, part_result_dict:{proxy.part_result_dict}")


def main():
    part_run = PartProcessor()
    part_run.run_process()


# 设置缓存服务
proxy = Proxy()
proxy.start()

server = ServerProxy("http://localhost:9090/")

