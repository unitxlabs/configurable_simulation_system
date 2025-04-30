from typing import Dict,Optional
import logging
from backend.modbus_tcp_client import ModbusTCP
from threading import Thread
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
        self.modbus_client = ModbusTCP(
            host=config.get("plc_ip", "localhost"),
            port=config.get("plc_port", 5020)
        )
        self.result_id = 0

    async def start(self) -> bool:
        """启动通信"""
        try:
            # 连接 Modbus TCP
            if not self.modbus_client.connect():
                logging.error("无法连接到 Modbus TCP 服务器")
                return False

            # 写入配置
            if not self._write_config():
                self.modbus_client.disconnect()
                return False

            # 生成配置文件
            if not self._generate_config_file():
                self.modbus_client.disconnect()
                return False

            self.is_running = True
            return True
        except Exception as e:
            logging.error(f"启动失败: {e}")
            return False

    def stop(self):
        """停止通信"""
        self.is_running = False
        self.modbus_client.disconnect()

    def _write_config(self) -> bool:
        """写入配置到 Modbus"""
        try:
            communication_config = self.config.get("communication_config", {})
            workstation_in_use = communication_config.get("workstations_in_use", [False, False, False, False, False, False])
            workstation_config_ids = communication_config.get("workstation_config_ids", [])
            workstation_use_request = []
            workstation_use_ids = []
            
            for i in range(6):
                if workstation_in_use[i]:
                    workstation_use_request.append(1)
                    workstation_use_ids.append(workstation_config_ids[i])
                else:
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
            part_start_request = [part_interval, part_start_to_ws1_interval]

            log.debug(f"📝_write_workstation_use: {workstation_use_request}")
            self.modbus_client.write(slave_id=1, addr=1000, val=workstation_use_request, datatype='int')

            log.debug(f"_write_communication: {communication_type_request}")
            self.modbus_client.write(slave_id=1, addr=1010, val=communication_type_request, datatype='int')

            log.debug(f"_write_part_start:{part_type} {part_start_request}")
            self.modbus_client.write(slave_id=1, addr=1020, val=part_type, datatype='str')
            self.modbus_client.write(slave_id=1, addr=1040, val=part_start_request, datatype='int')

            log.debug("🛠️ Writing system config")
            self.modbus_client.write(slave_id=1, addr=900, val=[7518, 7520, 7522, 7524], datatype='int')

            address = 1100
            for workstation_config in workstation_use_configs:
                controller_id = workstation_config.get("controller_config").get("controller_id")
                repeat_list = ImageCountUtil.get_controller_pic_count_list(controller_id)
                request = []
                sequence_count = workstation_config.get("sequence_count", 0)
                sequences_ids = workstation_config.get("sequences_id", [])
                # 如果sequences_ids长度小于10，补0到10个元素
                if len(sequences_ids) < 10:
                    sequences_ids.extend([0] * (10 - len(sequences_ids)))
                sequences_intervals = workstation_config.get("sequences_interval", [])
                # 如果sequences_intervals长度小于10，补0到10个元素
                if len(sequences_intervals) < 10:
                    sequences_intervals.extend([0] * (10 - len(sequences_intervals)))
                request.append(sequence_count)
                request.extend(sequences_ids)
                request.extend(sequences_intervals)
                request.extend(repeat_list)
                request.append(int(workstation_config.get("to_next_ws_offset", 0)))
                request.append(int(workstation_config.get("camera_reset_time", 0)))
                log.debug(f"_write_workstation:address {address} ,data {request}")
                self.modbus_client.write(slave_id=1, addr=address, val=request, datatype='int')
                address += 33
            if communication_type==1:
                # proxy_thread = Thread(
                #     target=run_proxy_server,
                #     args=(),
                #     daemon=True
                # )
                # proxy_thread.start()
                val=[0,4,44,45,40,36,74,8,12,16,20,24,28,32,36,46,53,54,94]
                log.debug(f" write_fly config:address 100 ,data {val}")
                self.modbus_client.write(slave_id=1, addr=100, val=val, datatype='int')
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