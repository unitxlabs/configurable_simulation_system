import importlib.util
import os
from pathlib import Path

home_dir = Path.home()

config_path = f"{home_dir}/unitx_data/config/production.py"


def load_config(config_path):
    """动态加载 Python 配置文件"""
    if not os.path.exists(config_path):
        return []

    spec = importlib.util.spec_from_file_location("config_module", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    return config_module.imaging_config


class ImageCountUtil:
    @staticmethod
    def get_controller_pic_all_count(controller_id: str):
        imaging_config = load_config(config_path)
        capture_images_count = 0
        networks_inference_count = 0
        for config in imaging_config:
            for part in config.get("part_config", []):
                if part.get("controller_port_id") == controller_id:
                    sequences = part.get("sequences", [])
                    for seq in sequences:
                        repeat = seq.get("repeat", 0)
                        cc_network_mapping = seq.get("cc_network_mapping", {})
                        capture_images_count += repeat * len(cc_network_mapping.keys())
                        networks_inference_count += repeat * sum(len(v) for v in cc_network_mapping.values())
        return capture_images_count, networks_inference_count

    @staticmethod
    def get_controller_pic_count_list(controller_id: str):
        imaging_config = load_config(config_path)
        repeat_list = []
        for config in imaging_config:
            for part in config.get("part_config", []):
                if part.get("controller_port_id") == controller_id:
                    sequences = part.get("sequences", [])
                    for seq in sequences:
                        repeat_list.append(seq.get("repeat", 0))
        if len(repeat_list) < 10:
            repeat_list.extend([0] * (10 - len(repeat_list)))
        return repeat_list
