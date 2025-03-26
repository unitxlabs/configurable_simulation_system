import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

# 设置日志文件路径
log_file_path = "operate.log"

# 配置 RotatingFileHandler 进行日志切割
log_handler = RotatingFileHandler(
    log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3
)  # 文件最大5MB，最多保留3个备份
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)s # %(message)s"))
# 创建日志记录器
logger = logging.getLogger("backend_operate")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)


class Logger:
    @staticmethod
    def log_action(action: str):
        """
        记录操作日志
        :param action: 需要记录的操作
        """
        log_message = f"操作: {action}"
        logger.info(log_message)

    @staticmethod
    def get_last_logs(count: int = 20):
        """
        获取最新的日志
        :param count: 获取的日志条数
        :return: 日志内容列表
        """
        log_lines = []
        try:
            with open(log_file_path, "r") as log_file:
                log_lines = log_file.readlines()[-20:]  # 获取最后20条日志
        except Exception as e:
            return log_lines

        # 格式化日志数据
        formatted_logs = []
        for line in reversed(log_lines):
            # 提取时间和日志消息
            timestamp = line.split("#")[0]
            message = line.split("#")[1]
            formatted_logs.append({"date": timestamp, "desc": message.strip()})

        return formatted_logs
