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
    address = 2638  # 初始化地址
    if ack:
        address = 2644
    ack_address = 2650
    part_id_address = 520
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
            part_id_address += 256  # part_id的address
            current_ack_address = ack_address
            ack_address += 1
            if ack:
                station_done = {
                    "signal": {
                        "request": {
                            "address": str(current_address),  # 使用当前的地址
                            "length": "1",
                            "default_signal": [0, 1, 2],
                        },
                        "ack": {
                            "address": str(current_ack_address),
                            "length": "1",
                            "default_signal": [
                                0,
                                1,
                                2
                            ]
                            }
                    },
                    "part_id": {
                        "request": {"address": str(part_id_address), "length": "254"}
                    },
                }                
            else:
                station_done = {
                    "signal": {
                        "request": {
                            "address": str(current_address),  # 使用当前的地址
                            "length": "1",
                            "default_signal": [0, 1, 2],
                        },
                    },
                    "part_id": {
                        "request": {"address": str(part_id_address), "length": "254"}
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
            plc_config = {}
            if self.config.get("communication_step")==2:
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
            result=self.snap_client.read(address="2578",  datatype='int')
            return result
        except Exception as e:
            logging.error(f"获取结果失败: {e}")
            return None 
    def run_server(self) -> bool:
        """启动"""
        return True
    def stop_server(self) -> bool:
        """停止"""
        self.snap_client.disconnect()
        return True
def gen_step2_config(config):
    return  {
                "plcs": [
                    {
                        "ip": "192.168.0.1",
                        "port": "48818",
                        "protocol": "s7_pro",
                        "name": "the_name_of_plc",
                        "addresses": {
                            "part_start": {
                                "signal": {
                                    "request": {
                                        "address": "2572",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_end": {
                                "signal": {
                                    "request": {
                                        "address": "2575",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_result": {
                                "signal": {
                                    "request": {
                                        "address": "2578",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "sys_reset": {
                                "signal": {
                                    "request": {
                                        "address": "2313",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_heartbeat": {
                                "signal": {
                                    "request": {
                                        "address": "2312",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_alarm": {
                                "signal": {
                                    "request": {
                                        "address": "2314",
                                        "length": "2",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "alarm_type": {
                                    "request": {
                                        "address": "2316",
                                        "length": "254"
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
                        "port": "48818",
                        "protocol": "s7_pro",
                        "name": "the_name_of_plc",
                        "addresses": {
                            "part_start": {
                                "signal": {
                                    "request": {
                                        "address": "2572",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    },
                                    "ack": {
                                        "address": "2574",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_end": {
                                "signal": {
                                    "request": {
                                        "address": "2575",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    },
                                    "ack": {
                                        "address": "2577",
                                        "length": "1",
                                        "default_signal": [
                                            0,
                                            1,
                                            2
                                        ],
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "part_result": {
                                "signal": {
                                    "request": {
                                        "address": "2578",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "part_id": {
                                    "request": {
                                        "address": "264",
                                        "length": "1"
                                    }
                                },
                                "part_type": {
                                    "request": {
                                        "address": "8",
                                        "length": "1"
                                    }
                                }
                            },
                            "sys_reset": {
                                "signal": {
                                    "request": {
                                        "address": "2313",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_heartbeat": {
                                "signal": {
                                    "request": {
                                        "address": "2312",
                                        "length": "1",
                                        "default_signal": [0, 1, 2]
                                    }
                                }
                            },
                            "sys_alarm": {
                                "signal": {
                                    "request": {
                                        "address": "2314",
                                        "length": "2",
                                        "default_signal": [0, 1, 2]
                                    }
                                },
                                "alarm_type": {
                                    "request": {
                                        "address": "2316",
                                        "length": "254"
                                    }
                                }
                            },
                            "station": transform_data(config,False)
                        }
                    }
                ]
            }