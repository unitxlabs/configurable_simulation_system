from typing import Dict,Optional
import logging
#from backend.modbus_tcp_client import ModbusTCP
from backend.snap_7 import Snap7
from backend.image_count_util import ImageCountUtil
# from backend.communication.run_prod_thread_to_db import run_proxy_server
# 配置日志
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class BaseCommunication:
    def __init__(self, config: Dict):
        self.config = config
        self.is_running = False
        self.snap_client = Snap7(
            host=config.get("plc_ip", "192.168.0.1"),
            port=config.get("plc_port", 44818),
            rack=config.get("rack", 0),
            slot=config.get("plc_port", 1),
            callback=config.get("plc_port", None)
        )
        self.result_id = 0

    async def start(self) -> bool:
        """启动通信"""
        try:
            # 连接 snap
            if not self.snap_client.connect():
                logging.error("无法连接到 snap 服务器")
                return False

            # 写入配置
            if not self._write_config():
                self.snap_client.disconnect()
                return False
            
            # 生成配置文件
            if not self._generate_config_file():
                self.snap_client.disconnect()
                return False

            self.is_running = True
            return True
        except Exception as e:
            logging.error(f"启动失败: {e}")
            return False

    def stop(self):
        """停止通信"""
        self.is_running = False
        self.snap_client.disconnect()

    def _write_config(self) -> bool:
        """写入配置到 snap"""
        try:
            communication_config = self.config.get("communication_config", {})
            workstation_in_use = communication_config.get("workstations_in_use", [False, False, False, False, False, False])
            workstation_config_ids = communication_config.get("workstation_config_ids", [])
            workstation_use_request = []
            workstation_use_ids = []
            
            # for i in range(6):
            #     if workstation_in_use[i]:
            #         workstation_use_request.append(1)
            #         workstation_use_ids.append(workstation_config_ids[i])
            #     else:
            #         workstation_use_request.append(0)
            for i in range(6):
                if workstation_in_use[i]:
                    workstation_use_request.append(1)
                    workstation_use_ids.append(workstation_config_ids[i])

            for i in range(6):
                if not workstation_in_use[i]:
                    workstation_use_request.append(0)
            workstation_configs = self.config.get("workstation_configs", [])
            workstation_use_configs = []
            for workstation_config in workstation_configs:
                wc = workstation_config.get("workstation_config", {})
                if wc.get("id", 0) in workstation_use_ids:
                    workstation_use_configs.append(workstation_config)

            communication_type = communication_config.get("communication_type", 0)
            communication_step = communication_config.get("communication_step", 0)
            communication_type_request = [communication_type, communication_step]

            part_type = communication_config.get("part_type", "物料")
            part_interval = int(communication_config.get("part_interval", 0))
            part_start_to_ws1_interval = int(communication_config.get("part_start_to_ws1_interval", 0))

            log.debug(f"📝_write_workstation_use: {workstation_use_request}")
            for index, value in enumerate(workstation_use_request):
                self.snap_client.write(address=f"1_2582_{index}", value=value, datatype='bool')
            log.debug(f"_write_communication: {communication_type_request}")
            self.snap_client.write(address=f"1_1", value=communication_type, datatype='int8')
            self.snap_client.write(address=f"1_2", value=communication_step, datatype='int8')

            log.debug(f"_write_part_start:{part_type} {part_interval}")
            self.snap_client.write(address="1_16",  value=part_type, datatype='str')
            self.snap_client.write(address="1_6",  value=part_interval, datatype='int32')

            ws_next_interval=[part_start_to_ws1_interval]
            camera_reset_time=[]
            ws_seq_count=[]
            start_offset_address=2700
            start_repeat_address=2660
            for workstation_config_data in workstation_use_configs:
                workstation_config = workstation_config_data.get("workstation_config", {})
                ws_next_interval.append(int(workstation_config.get("to_next_ws_offset", 0)))
                camera_reset_time.append(int(workstation_config.get("camera_reset_time", 0)))
                controller_id = workstation_config_data.get("controller_config").get("controller_id")
                repeat_list = ImageCountUtil.get_controller_pic_count_list(controller_id)
                ws_seq_count.append(workstation_config.get("sequence_count", 0))
                sequences_ids = workstation_config.get("sequences_id", [])
                if len(sequences_ids) < 10:
                    sequences_ids.extend([0] * (10 - len(sequences_ids)))
                sequences_intervals = workstation_config.get("sequences_interval", [])
                if len(sequences_intervals) < 10:
                    sequences_intervals.extend([0] * (10 - len(sequences_intervals)))

                # log.debug(f"_write_workstation:address 1_{start_address}_0 ,data {sequences_ids}")
                # for index, value in enumerate(sequences_ids):
                #     self.snap_client.write(f"1_{start_address}_0", value=value, datatype='int32')
                log.debug(f"_write_workstation_repeat:address 1_{start_repeat_address} ,data {repeat_list}")
                for value in repeat_list:
                    self.snap_client.write(address=f"1_{start_repeat_address}", value=value, datatype='int32')
                    start_repeat_address+=4
                # self.snap_client.write(address=f"1_{start_address}_0", value=sequences_intervals, datatype='udint',check=True)
                log.debug(f"_write_workstation_offset:address 1_{start_offset_address} ,data {sequences_intervals}")
                for value in sequences_intervals:
                    self.snap_client.write(address=f"1_{start_offset_address}", value=value, datatype='int32')
                    start_offset_address+=4

            log.debug(f"2654 ws_seq_count:{ws_seq_count}")
            seq_addr=2654
            for index, value in enumerate(ws_seq_count):
                self.snap_client.write(address=f"1_{seq_addr}", value=value, datatype='int8')
                seq_addr+=1
            log.debug(f"2584 ws_next_interval:{ws_next_interval}")
            seq_next_addr=2584
            for index, value in enumerate(ws_next_interval):
                self.snap_client.write(address=f"1_{seq_next_addr}", value=value, datatype='int32')
                seq_next_addr+=4

            log.debug(f"2612 camera_reset_time:{camera_reset_time}")
            camera_reset_addr=2612
            for index, value in enumerate(camera_reset_time):
                self.snap_client.write(address=f"1_{camera_reset_addr}", value=value, datatype='int32')
                camera_reset_addr+=4
            # self.snap_client.write(address="1_2614_0",  value=camera_reset_time, datatype='udint',check=True)
            if communication_type==1:
                value=[0,4,44,45,40,36,74,8,12,16,20,24,28,32,36,46,53,54,94]
                log.debug(f" write_fly config:address 100 ,data {value}")
                self.snap_client.write(slave_id=1, addr=100, value=value, datatype='int')

            # print("读取配置")
            # print(f'Address:2584 📝_write_workstation_use:{self.snap_client.read(address="2584",length=1,datatype="bool")}')
            # print(f'Address:1 _write_communication:{self.snap_client.read(address="1",length=1,datatype="int")}')
            # print(f'Address:8 part_type:{self.snap_client.read(address="8",datatype="str")}')
            # print(f'Address:4 _write_part_start:{self.snap_client.read(address="4",length=1,datatype="int")}')
            # print(f'Address:2662 _write_workstation1sequences_ids:{self.snap_client.read(address="2662",length=10,datatype="int")}')
            # print(f'Address:2702 _write_workstation1sequences_intervals:{self.snap_client.read(address="2702",length=10,datatype="int")}')
            # print(f'Address:2742 _write_workstation1repeat_list:{self.snap_client.read(address="2742",length=10,datatype="int")}')
            # print(f'Address:2656 ws_seq_count:{self.snap_client.read(address="2656",length=6,datatype="int")}')
            # print(f'Address:2586 ws_next_interval:{self.snap_client.read(address="2586",length=6,datatype="int")}')
            # print(f'Address:2614 camera_reset_time:{self.snap_client.read(address="2614",length=6,datatype="int")}')
            log.debug(f"_write_plc_reset: {1}")
            self.snap_client.write(address=f"1_4", value=1, datatype='int8')
            return True
        except Exception as e:
            logging.error(f"写入配置失败: {e}")
            return False

    def _generate_config_file(self) -> bool:
        """生成配置文件"""
        raise NotImplementedError("子类必须实现此方法")

    def get_result(self) -> Optional[Dict]:
        """获取结果"""
        raise NotImplementedError("子类必须实现此方法")
    def run_server(self) -> bool:
        """启动"""
        raise NotImplementedError("子类必须实现此方法")
    def stop_server(self) -> bool:
        """停止"""
        raise NotImplementedError("子类必须实现此方法")