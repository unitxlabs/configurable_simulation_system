from typing import Dict, Optional
import logging
from backend.communication.base_communication import BaseCommunication
from backend.communication.run_prod_thread_to_db import HttpProxy
CAM1_ID = ""
CAM2_ID = ""
CAM3_ID = ""
CAM4_ID = ""
CAM5_ID = ""
CAM6_ID = ""

PART_TYPE = "测试物料"

MODBUS_HOST = "127.0.0.1"
MODBUS_PROT = 5020
SLAVE_ID = 1

CACHE_PROXY_HOST = "127.0.0.1"
CACHE_PROXY_PROT = 8048


PLC_HEARTBEAT_POLLER_TIME = 0.5  # 231028 PLC将心跳超时时间改为5s
PLC_HEARTBEAT_WAIT_TIME = 0.2  # PLC读到心跳信号过200ms再置1

PROD_HEARTBEAT_POLLER_TIME = 1  # Prod 心跳超时时间设为 1s


IS_PLC_READ_SN = False  # 是否由PLC读码

MAX_PART_IN_PROCESS_NUM = 10
PLC_DECODE_ERROR = "ERROR"


PLC_HEARTBEAT = "heartbeat"
PROD_HEARTBEAT = "prod_status"
PLC_TIME_STAMP = "plc_time_stamp"
PLC_RESET = "plc_reset"
PLC_RESET_ACK = "plc_reset_ack"
PLC_PAUSE = "plc_pause"
PLC_START = "plc_start"
PART_START_SN = "part_start_sn"
SENSOR_PART_START = "sensor_part_start"
SENSOR_STATION_1 = "sensor_station_1"
SENSOR_STATION_2 = "sensor_station_2"
SENSOR_STATION_3 = "sensor_station_3"
SENSOR_STATION_4 = "sensor_station_4"
SENSOR_STATION_5 = "sensor_station_5"
SENSOR_STATION_6 = "sensor_station_6"
SENSOR_PART_END = "sensor_part_end"
PART_RESULT = "part_result"
PART_RESULT_SN = "part_result_sn"
PART_RESULT_MSG = "part_result_msg"


# plc的地址除2, 才是MODBUS client抵达的地址。(plc系统是64位linux)
# 以下地址及长度全是plc的地址除2。like：plc 8000 --> AOI 4000
# PART_RESULT 地址46置1 OK，地址47置1 NG1 地址48置1 NG2
INT_LENGTH = 1
SN_LENGTH = 20
TIME_STAMP_LENGTH = 4
REGISTER_ADDR_LENGTH = 100  # 读取长度
REGISTER_ADDR = {
    PLC_HEARTBEAT:     {"addr": 0,   "length": INT_LENGTH,        "type": int,     "is_read": True},   # 心跳
    PLC_TIME_STAMP:    {"addr": 4,   "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # plc当前时间
    PLC_RESET:         {"addr": 44,  "length": INT_LENGTH,        "type": int,     "is_read": True},   # 初始化
    PLC_RESET_ACK:     {"addr": 45,  "length": INT_LENGTH,        "type": int,     "is_read": False},  # 初始化ack
    PLC_PAUSE:         {"addr": 40,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 暂停
    PLC_START:         {"addr": 36,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 暂停结束
    PART_START_SN:     {"addr": 74,  "length": SN_LENGTH,         "type": str,     "is_read": True},   # 物料开始SN
    SENSOR_PART_START: {"addr": 8,   "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 物料开始传感器
    SENSOR_STATION_1:  {"addr": 12,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位1传感器
    SENSOR_STATION_2:  {"addr": 16,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位2传感器
    SENSOR_STATION_3:  {"addr": 20,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位3传感器
    SENSOR_STATION_4:  {"addr": 24,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位4传感器
    SENSOR_STATION_5:  {"addr": 28,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位5传感器
    SENSOR_STATION_6:  {"addr": 32,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 工位6传感器
    SENSOR_PART_END:   {"addr": 36,  "length": TIME_STAMP_LENGTH, "type": "ulint", "is_read": True},   # 物料结束传感器
    PART_RESULT:       {"addr": 46,  "length": INT_LENGTH,        "type": int,     "is_read": False},  # 物料结果
    PART_RESULT_MSG:   {"addr": 53,  "length": INT_LENGTH,        "type": int,     "is_read": False},  # 物料结果信息
    PART_RESULT_SN:    {"addr": 54,  "length": SN_LENGTH,         "type": str,     "is_read": False},  # 物料结果SN
    PROD_HEARTBEAT:    {"addr": 94,  "length": INT_LENGTH,        "type": int,     "is_read": False},  # Prod状态
}


# 物料结果
OK = 0   # 物料ok, value=1, write to addr PART_RESULT + 0
NG1 = 1  # 排物料到黄色皮带, value=1, write to addr PART_RESULT + 1
NG2 = 2  # 排物料到红色皮带, value=1, write to addr PART_RESULT + 2

# 报警信息，有以下MSG的物料在数据库中都没有结果， 给PLC发NG2，排红色皮带
MSG_91 = 91  # 物料结果超时
MSG_92 = 92  # 物料丢图
MSG_93 = 93  # 物料未识别出二维码
MSG_94 = 94  # 物料间距过短
MSG_95 = 95  # 连续多个物料异常，需初始化

# MSG_<STATION><ERROR_TYPE>
# #1: 触发不在合适的时间
MSG_S1_E1 = 11 # 1号工位传感器触发时间不对
MSG_S2_E1 = 21 # 2号工位传感器触发时间不对
MSG_S3_E1 = 31 # 3号工位传感器触发时间不对
MSG_S4_E1 = 41 # 4号工位传感器触发时间不对
MSG_S5_E1 = 51 # 5号工位传感器触发时间不对
MSG_S6_E1 = 61 # 6号工位传感器触发时间不对
MSG_S7_E1 = 71 # 排料工位传感器触发时间不对
# #2： 超时没触发
MSG_S1_E2 = 12 # 1号工位传感器超时没触发
MSG_S2_E2 = 22 # 2号工位传感器超时没触发
MSG_S3_E2 = 32 # 3号工位传感器超时没触发
MSG_S4_E2 = 42 # 4号工位传感器超时没触发
MSG_S5_E2 = 52 # 5号工位传感器超时没触发
MSG_S6_E2 = 62 # 6号工位传感器超时没触发
MSG_S7_E2 = 72 # 排料工位传感器超时没触发
# #3: 重复触发
MSG_S1_E3 = 13  # 1号工位传感器重复触发
MSG_S2_E3 = 23 # 2号工位传感器重复触发
MSG_S3_E3 = 33 # 3号工位传感器重复触发
MSG_S4_E3 = 43 # 4号工位传感器重复触发
MSG_S5_E3 = 53 # 5号工位传感器重复触发
MSG_S6_E3 = 63 # 6号工位传感器重复触发
MSG_S7_E3 = 73 # 排料工位传感器重复触发
# #4:物料间距过短
MSG_S1_E4 = 14   # 1号工位传感器物料间距过短
MSG_S2_E4 = 24  # 2号工位传感器物料间距过短
MSG_S3_E4 = 34  # 3号工位传感器物料间距过短
MSG_S4_E4 = 44  # 4号工位传感器物料间距过短
MSG_S5_E4 = 54  # 5号工位传感器物料间距过短
MSG_S6_E4 = 64  # 6号工位传感器物料间距过短
MSG_S7_E4 = 74  # 排料工位传感器物料间距过短




MIN_SENSOR_TRIGGER_OFFSET = 500  # 传感器最小触发时间间隔 ms
MIN_PART_TIME_INTERVAL = 1000    # 同个传感器，感应到2个物料的最短间隔时间 ms

# SENSORS_TIME_OFFSET_DEVIATION_RANGE = 0.3  # 传感器时间偏差范围，百分比 %
SENSORS_TIME_OFFSET_MIN_LIMIT = 0.8  # 传感器时间偏差范围下限，百分比 %
SENSORS_TIME_OFFSET_MAX_LIMIT = 1.2  # 传感器时间偏差范围上限，百分比 %

MARGIN_OFF_OFFSET_TIME = 0.1

CAMERA_STATION_LIST = [
    SENSOR_STATION_1,
    SENSOR_STATION_2,
    SENSOR_STATION_3,
    SENSOR_STATION_4,
    SENSOR_STATION_5,
    SENSOR_STATION_6,
]

SENSORS_MAP = {
    SENSOR_PART_START: {
        "last_sensor": None,
        "next_sensor": None,  # 将在处理第一个工位时更新
        "sensor_to_camera": [],
        "offset_time": 0,
        "reset_camera_wait_time": 0,
        "log_name": "S0",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': None,
        'no_trigger_error': None,
        'trigger_repeat_error': None,
        'part_interval_error': None
    },
    SENSOR_STATION_1: {
        "last_sensor": SENSOR_PART_START,
        "next_sensor": SENSOR_STATION_2,
        "sensor_to_camera": [CAM1_ID],
        "offset_time": 1906,  # t_r1_r2 毫秒 ms
        "reset_camera_wait_time": 2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R2",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S2_E1,
        'no_trigger_error': MSG_S2_E2,
        'trigger_repeat_error': MSG_S2_E3,
        'part_interval_error': MSG_S2_E4
    },
    SENSOR_STATION_2: {
        "last_sensor": SENSOR_PART_START,
        "next_sensor": SENSOR_STATION_3,
        "sensor_to_camera": [CAM2_ID],
        "offset_time": 1906,  # t_r1_r2 毫秒 ms
        "reset_camera_wait_time": 2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R2",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S2_E1,
        'no_trigger_error': MSG_S2_E2,
        'trigger_repeat_error': MSG_S2_E3,
        'part_interval_error': MSG_S2_E4
    },
    SENSOR_STATION_3: {
        "last_sensor": SENSOR_STATION_2,
        "next_sensor": SENSOR_STATION_4,
        "sensor_to_camera": [CAM3_ID],
        "offset_time": 1906,  # t_r1_r2 毫秒 ms
        "reset_camera_wait_time": 2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R3",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S3_E1,
        'no_trigger_error': MSG_S3_E2,
        'trigger_repeat_error': MSG_S3_E3,
        'part_interval_error': MSG_S3_E4
    },
    SENSOR_STATION_4: {
        "last_sensor": SENSOR_STATION_3,
        "next_sensor": SENSOR_STATION_5,
        "sensor_to_camera": [CAM4_ID],
        "offset_time": 3223,  # t_r2_r4 毫秒 ms
        "reset_camera_wait_time": 2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R4",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S4_E1,
        'no_trigger_error': MSG_S4_E2,
        'trigger_repeat_error': MSG_S4_E3,
        'part_interval_error': MSG_S4_E4
    },
    SENSOR_STATION_5: {
        "last_sensor": SENSOR_STATION_4,
        "next_sensor": SENSOR_STATION_6,
        "sensor_to_camera": [CAM5_ID],
        "offset_time": 1774,  # t_r4_r5 毫秒 ms
        "reset_camera_wait_time": 2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R5",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S5_E1,
        'no_trigger_error': MSG_S5_E2,
        'trigger_repeat_error': MSG_S5_E3,
        'part_interval_error': MSG_S5_E4
    },
    SENSOR_STATION_6: {
        "last_sensor": SENSOR_STATION_5,
        "next_sensor": SENSOR_PART_END,
        "sensor_to_camera": [CAM6_ID],
        "offset_time": 2730,  # t_r5_r6 毫秒 ms
        "reset_camera_wait_time": 2.2,  # 触发传感器后过多久复位相机 秒 s
        "log_name": "R6",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S6_E1,
        'no_trigger_error': MSG_S6_E2,
        'trigger_repeat_error': MSG_S6_E3,
        'part_interval_error': MSG_S6_E4
    },
    SENSOR_PART_END: {
        "last_sensor": SENSOR_STATION_6,
        "next_sensor": None,
        "sensor_to_camera": [],
        "offset_time": 0,  # 将在处理最后一个工位时更新
        "reset_camera_wait_time": 0,
        "log_name": "S1",
        "offset_min_limit": 0.7,
        "offset_max_limit": 1.3,
        'trigger_out_range_error': MSG_S7_E1,
        'no_trigger_error': MSG_S7_E2,
        'trigger_repeat_error': MSG_S7_E3,
        'part_interval_error': MSG_S7_E4
    },
}

class FlyingCommunication(BaseCommunication):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.proxy=None
        self.part_process=None

    def _generate_config_file(self) -> bool:
        """生成飞拍配置文件"""
        global CAM1_ID, CAM2_ID, CAM3_ID, CAM4_ID, CAM5_ID, CAM6_ID,PART_TYPE,CAMERA_STATION_LIST,SENSORS_MAP
        # 获取workstation_config_ids和workstations_in_use
        PART_TYPE = self.config["communication_config"]["part_type"]
        # part_interval = int(self.config["communication_config"].get("part_interval", 0))
        # part_start_to_ws1_interval = int(self.config["communication_config"].get("part_start_to_ws1_interval", 0))
        workstations_in_use = self.config["communication_config"]["workstations_in_use"]
        workstation_configs = self.config["workstation_configs"]
        workstation_use_configs = []
        for i, ws_config in enumerate(workstation_configs):
            if workstations_in_use[i]:
                controller_config = ws_config["controller_config"]
                camera_id = controller_config["cameras_id"][0]
                offset_time = self.config["communication_config"]["part_start_to_ws1_interval"]
                if i == 0:
                    offset_time = SENSORS_MAP[SENSOR_PART_START]["offset_time"]
                workstation_use_configs.append({
                    "camera_id": camera_id,
                    "offset_time": offset_time,
                    "reset_camera_wait_time": ws_config["workstation_config"]["camera_reset_time"],
                })

        # 清空 CAMERA_STATION_LIST
        CAMERA_STATION_LIST.clear()
        
        # 重置 SENSORS_MAP
        SENSORS_MAP.clear()
        
        # 初始化 SENSOR_PART_START
        SENSORS_MAP[SENSOR_PART_START] = {
            "last_sensor": None,
            "next_sensor": None,  # 将在处理第一个工位时更新
            "sensor_to_camera": [],
            "offset_time": self.config["communication_config"]["part_start_to_ws1_interval"],
            "reset_camera_wait_time": 0,
            "log_name": "S0",
            "offset_min_limit": 0.7,
            "offset_max_limit": 1.3,
            'trigger_out_range_error': None,
            'no_trigger_error': None,
            'trigger_repeat_error': None,
            'part_interval_error': None
        }

        # 初始化 SENSOR_PART_END
        SENSORS_MAP[SENSOR_PART_END] = {
            "last_sensor": None,  # 将在处理最后一个工位时更新
            "next_sensor": None,
            "sensor_to_camera": [],
            "offset_time": 0,  # 将在处理最后一个工位时更新
            "reset_camera_wait_time": 0,
            "log_name": "S1",
            "offset_min_limit": 0.7,
            "offset_max_limit": 1.3,
            'trigger_out_range_error': MSG_S7_E1,
            'no_trigger_error': MSG_S7_E2,
            'trigger_repeat_error': MSG_S7_E3,
            'part_interval_error': MSG_S7_E4
        }
        
        # 定义工位与相机ID变量的映射关系
        station_map = {
            0: ("CAM1_ID", SENSOR_STATION_1),
            1: ("CAM2_ID", SENSOR_STATION_2), 
            2: ("CAM3_ID", SENSOR_STATION_3),
            3: ("CAM4_ID", SENSOR_STATION_4),
            4: ("CAM5_ID", SENSOR_STATION_5),
            5: ("CAM6_ID", SENSOR_STATION_6)
        }

        last_sensor = SENSOR_PART_START
        for i, wuc in enumerate(workstation_use_configs):
            # 只处理实际存在的工位
            if i < len(station_map):
                # 获取当前工位对应的相机ID和传感器变量
                cam_id_var, sensor = station_map[i]
                # 给全局变量赋值
                globals()[cam_id_var] = wuc["camera_id"]
                
                # 添加到相机站点列表
                CAMERA_STATION_LIST.append(sensor)

                # 计算下一个传感器
                next_sensor = SENSOR_PART_END
                if i < len(workstation_use_configs) - 1:
                    _, next_sensor = station_map[i + 1]
                
                # 更新 SENSORS_MAP
                SENSORS_MAP[sensor] = {
                    "last_sensor": last_sensor,
                    "next_sensor": next_sensor,
                    "sensor_to_camera": [globals()[cam_id_var]],
                    "offset_time": wuc["offset_time"],
                    "reset_camera_wait_time": wuc["reset_camera_wait_time"],
                    "log_name": f"R{i+1}",
                    "offset_min_limit": 0.7,
                    "offset_max_limit": 1.3,
                    'trigger_out_range_error': globals()[f"MSG_S{i+1}_E1"],
                    'no_trigger_error': globals()[f"MSG_S{i+1}_E2"],
                    'trigger_repeat_error': globals()[f"MSG_S{i+1}_E3"],
                    'part_interval_error': globals()[f"MSG_S{i+1}_E4"]
                }

                # 更新 SENSOR_PART_START 的 next_sensor（如果是第一个工位）
                if i == 0:
                    SENSORS_MAP[SENSOR_PART_START]["next_sensor"] = sensor

                # 如果是最后一个工位，更新 end 的相关配置
                if i == len(workstation_use_configs) - 1:
                    SENSORS_MAP[SENSOR_PART_END]["last_sensor"] = sensor
                    SENSORS_MAP[SENSOR_PART_END]["offset_time"] = wuc["offset_time"]

                # 更新 last_sensor 为当前传感器，用于下一次循环
                last_sensor = sensor
        print(SENSORS_MAP)
        print(CAMERA_STATION_LIST)
        print(CAM1_ID, CAM2_ID, CAM3_ID, CAM4_ID, CAM5_ID, CAM6_ID)
        print(PART_TYPE)
        return True

    def get_result(self) -> Optional[Dict]:
        """获取飞拍结果"""
        if not self.is_running:
            return None
            
        try:
            result=self.modbus_client.read(slave_id=1, addr=7516, length=1, datatype='int')[0]
            return result
        except Exception as e:
            logging.error(f"获取结果失败: {e}")
            return None 
    def set_part_processor(self, part_process):
        self.part_process = part_process
    def run_server(self) -> bool:
        """启动"""
        self.part_process.set_client(self.modbus_client)
        self.part_process.start_heartbeat()
        self.part_process.start_process()
        self.proxy=HttpProxy()
        self.proxy.start_proxy()
        return True
    def stop_server(self) -> bool:
        """停止"""
        if self.part_process:
            self.part_process.stop_heartbeat()
            self.part_process.stop_process()
        self.modbus_client.disconnect()
        if self.proxy:
            self.proxy.stop_proxy()
        return True