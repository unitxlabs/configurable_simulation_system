from typing import Dict, Optional
import logging
from backend.communication.base_communication import BaseCommunication
import json
import os


def transform_data(data,ack):
    # 获取workstation_config_ids和workstations_in_use
    c_name = data["communication_config"]["name"]
    workstations_in_use = data["communication_config"]["workstations_in_use"]
    workstation_configs = data["workstation_configs"]
    # 生成转换后的数据
    result = []
    address = 2636  # 初始化地址
    if ack:
        address = 2642
    ack_address = 2648
    part_id_address = 528
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
            address += 1  # signal的address使用current_address，然后address加2
            current_ack_address = ack_address
            ack_address += 1
            print(ack)
            if ack:
                station_done = {
                    "signal": {
                        "request": {
                            "address": f"1_{current_address}",  # 使用当前的地址
                            "length": "1",
                            "default_signal": [0, 1, 2],
                            "datatype": "int8"
                        },
                        "ack": {
                            "address": f"1_{current_ack_address}",
                            "length": "1",
                            "default_signal": [
                                0,
                                1,
                                2
                            ],
                            "datatype": "int8"
                            }
                    },
                    "part_id": {
                        "request": {"address": f"1_{part_id_address}", "length": "254"}
                    },
                }                
            else:
                station_done = {
                    "signal": {
                        "request": {
                            "address": f"1_{current_address}",  # 使用当前的地址
                            "length": "1",
                            "default_signal": [0, 1, 2],
                            "datatype": "int8"
                        },
                    },
                    "part_id": {
                        "request": {"address": f"1_{part_id_address}", "length": "254","datatype": "str"}
                    },
                }
            part_id_address += 256  # part_id的address

            result.append(
                {"name": name, "camera": camera, "station_done": station_done}
            )

    return result
class FixedCommunication(BaseCommunication):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.config_file_path = "/home/unitx/unitx_data/config/TecomX.json"

    def _generate_config_file(self) -> bool:
        """生成定拍配置文件"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            plc_config = {}
            if self.config.get("communication_config").get("communication_step")==2:
                plc_config = gen_step2_config(self.config)
            else:
                plc_config = gen_step4_config(self.config)
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
            result=self.snap_client.read(address="1_10",  datatype='int32')
            return result[0]
        except Exception as e:
            logging.error(f"获取结果失败: {e}")
            return None 
    def run_server(self) -> bool:
        """启动"""
        return True
    def stop_server(self) -> bool:
        """停止"""
        super().stop_server()
        self.snap_client.disconnect()
        return True
def gen_step2_config(config):
    return  {
                "plcs": [
                    {
                        "ip": "192.168.0.1",
                        "port": "44818",
                        "protocol": "Snap7",
                        "name": "the_name_of_plc",
                        "addresses": {
                            "part_start": {
                                "signal": {
                                    "request": {
                                        "address": "1_2576",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "1_272",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "1_16",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                }
                            },
                            "part_result": {
                                "signal": {
                                    "request": {
                                        "address": "1_2579",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "1_2064",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                },
                                "result": {
                                    "request": {
                                        "address": "1_5",
                                        "length": "1",
                                        "datatype": "int8"
                                    }
                                }
                            },
                            "sys_heartbeat": {
                                "signal": {
                                    "request": {
                                        "address": "1_3",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                }
                            },
                            "sys_alarm": {
                                "signal": {
                                    "request": {
                                        "address": "1_14",
                                        "length": "2",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int"
                                    }
                                },
                                "alarm_type": {
                                    "request": {
                                        "address": "1_2320",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                    
                                }
                            },
                            "station": transform_data(config,False)
                        }
                    }
                ]
            }
def gen_step4_config(config):
    return  {
                "plcs": [
                    {
                        "ip": "192.168.0.1",
                        "port": "44818",
                        "protocol": "Snap7",
                        "name": "the_name_of_plc",
                        "addresses": {
                            "part_start": {
                                "signal": {
                                    "request": {
                                        "address": "1_2577",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    },
                                    "ack": {
                                        "address": "1_2578",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "1_272",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "1_16",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                }
                            },
                            "part_result": {
                                "signal": {
                                    "request": {
                                        "address": "1_2580",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    },
                                    "ack": {
                                        "address": "1_2581",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "1_2064",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                },
                                "result": {
                                    "request": {
                                        "address": "1_5",
                                        "length": "1",
                                        "datatype": "int8"
                                    }
                                }
                            },
                            "sys_heartbeat": {
                                "signal": {
                                    "request": {
                                        "address": "1_3",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int8"
                                    }
                                }
                            },
                            "sys_alarm": {
                                "signal": {
                                    "request": {
                                        "address": "1_14",
                                        "length": "2",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                        "datatype": "int"
                                    }
                                },
                                "alarm_type": {
                                    "request": {
                                        "address": "1_2320",
                                        "length": "254",
                                        "datatype": "str"
                                    }
                                    
                                }
                            },
                            "station": transform_data(config,True)
                        }
                    }
                ]
            }