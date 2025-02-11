import logging


class FormattedLogging(object):
    _instance = None

    def __new__(cls, logger=None):
        if cls._instance is None:
            cls._instance = super(FormattedLogging, cls).__new__(cls)
        return cls._instance

    def __init__(self, logger=None):
        """
        指定保存日志的文件路径，日志级别，以及调用文件
        将日志存入到指定的文件中
        """

        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True

        # 创建一个logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.INFO)
        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s %(filename)s [line:%(lineno)d]: %(message)s')
        ch.setFormatter(formatter)
        # 给logger添加handler
        self.logger.addHandler(ch)

    def getLog(self):
        return self.logger
