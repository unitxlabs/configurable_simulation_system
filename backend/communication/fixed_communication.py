from typing import Dict, Optional
import logging
from backend.communication.base_communication import BaseCommunication
import json
import os


def transform_data(data):
    # 获取workstation_config_ids和workstations_in_use
    c_name = data["communication_config"]["name"]
    workstations_in_use = data["communication_config"]["workstations_in_use"]
    workstation_configs = data["workstation_configs"]
    # 生成转换后的数据
    result = []
    address = 7526  # 初始化地址
    for i, ws_config in enumerate(workstation_configs):
        if workstations_in_use[i]:
            workstation_id = ws_config["workstation_config"]["workstation_id"]
            controller_config = ws_config["controller_config"]

            # 生成name字段
            name = f"{c_name}_{workstation_id}"

            # 生成camera字段
            camera = []
            for camera_id in controller_config["cameras_id"]:
                controller_port_id = controller_config["controller_id"]
                camera.append(
                    {"camera_id": camera_id, "controller_port_id": controller_port_id}
                )
            current_address = address
            address += 2  # signal的address使用current_address，然后address加2
            part_id_address = address
            address += 2  # part_id的address

            # 生成station_done字段
            station_done = {
                "signal": {
                    "request": {
                        "address": str(current_address),  # 使用当前的地址
                        "length": "1",
                        "default_signal": [0, 1, 2],
                    }
                },
                "part_id": {
                    "request": {"address": str(part_id_address), "length": "1"}
                },
            }

            result.append(
                {"name": name, "camera": camera, "station_done": station_done}
            )

    return result

class FixedCommunication(BaseCommunication):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.config_file_path = "config/fixed_communication.json"

    def _generate_config_file(self) -> bool:
        """生成定拍配置文件"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            
            # 生成配置文件内容
            plc_config = {
                "plcs": [
                    {
                        "ip": "127.0.0.1",
                        "port": "5020",
                        "protocol": "Modbus TCP",
                        "name": "the_name_of_plc",
                        "addresses": {
                            "part_start": {
                                "signal": {
                                    "request": {
                                        "address": "7500",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "7502",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "7504",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_end": {
                                "signal": {
                                    "request": {
                                        "address": "7506",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "7508",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "7510",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_result": {
                                "signal": {
                                    "request": {
                                        "address": "7512",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "7514",
                                        "length": "1"
                                    }
                                },
                                "result": {
                                    "request": {
                                        "address": "7516",
                                        "length": "1"
                                    }
                                }
                            },
                            "sys_reset": {
                                "signal": {
                                    "request": {
                                        "address": "7518",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_heartbeat": {
                                "signal": {
                                    "request": {
                                        "address": "7520",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_alarm": {
                                "signal": {
                                    "request": {
                                        "address": "7522",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "alarm_type": {
                                    "request": {
                                        "address": "7524",
                                        "length": "1"
                                    }
                                }
                            },
                            "station": transform_data(self.config)
                        }
                    }
                ]
            }
            
            # 写入配置文件
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(plc_config, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            logging.error(f"生成配置文件失败: {e}")
            return False

    def get_result(self) -> Optional[Dict]:
        """获取定拍结果"""
        if not self.is_running:
            return None
            
        try:
            result=self.modbus_client.read(slave_id=1, addr=7516, length=1, datatype='int')[0]
            return result
        except Exception as e:
            logging.error(f"获取结果失败: {e}")
            return None 
    def run_server(self) -> bool:
        """启动"""
        return True
    def stop_server(self) -> bool:
        """停止"""
        self.modbus_client.disconnect()
        return True