from abc import abstractmethod
from collections import deque
from functools import wraps
from threading import Event, RLock, Thread
from typing import Optional, Union, Any
import time
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

cls_locker = RLock()

DEFAULT_TOTAL_FAILED_MAX_COUNT_FOR_RECONNECT = 3
DEFAULT_READ_WRITE_FAILED_MAX_COUNT_FOR_RECONNECT = 3
MAX_RECONNECT_THREAD_COUNT = 3


def try_except_with_locker(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            with self.locker:
                result = func(self, *args, **kwargs)
                return result
        except Exception as ex:
            self.errors.append(ex)
            logger.error(f'PROTOCOL TYPE: [{self.__class__.__name__}] - '
                         f'FUNCTION NAME: [{func.__name__}] - INPUT: [{kwargs if kwargs else args}] - ERROR: [{ex}]',
                         exc_info=True)
            Thread(target=self.reconnect, args=[func, *args, kwargs], daemon=True).start()
            return None

    return wrapper


def cls_try_except_with_locker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with cls_locker:
                result = func(*args, **kwargs)
                return result
        except Exception as ex:
            logger.error(f'FUNCTION NAME: [{func.__name__}] - INPUT: [{kwargs if kwargs else args}] - ERROR: [{ex}]',
                         exc_info=True)
            return None

    return wrapper


class CommunicationBase:
    # limit of consecutive read/write
    MAX_CONSECUTIVE_READ_WRITE_LENGTH = None

    def __init__(self, host, port, callback=None) -> None:
        self.locker = RLock()
        self.communication_fd = None
        self.host = host
        self.port = port
        self.is_connected = False
        self.errors = deque()
        self.reconnect_thread_count = 0
        self.stop_event = Event()
        self.thread = Thread(target=self.auto_connect, args=[])
        self.callback = callback

    def __del__(self, signum=None, frame=None):
        self.stop_event.set()
        self._disconnect()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def auto_connect(self):
        """Used to wait for PLC to create a connection"""
        while not self.stop_event.is_set():
            self.connect()
            time.sleep(3)
        self.disconnect()

    @property
    def errors_times(self):
        return len(self.errors) >= DEFAULT_TOTAL_FAILED_MAX_COUNT_FOR_RECONNECT

    @try_except_with_locker
    def reconnect(self, func, *args, **kwargs):
        """Quickly reconnect when errors occurred 3 times"""
        self.reconnect_thread_count += 1
        if self.reconnect_thread_count > MAX_RECONNECT_THREAD_COUNT:
            return True
        if self.errors_times:
            logger.info(f'Reconnect [{self.__class__.__name__}] start!')
            try:
                self._disconnect()
                self._connect()
                self.errors.clear()
                logger.info(f'Reconnect [{self.__class__.__name__}] success!')
                self.reconnect_thread_count = 0
                return True
            except:
                self.reconnect_thread_count -= 1
        else:
            failed_count = 0
            while failed_count < DEFAULT_READ_WRITE_FAILED_MAX_COUNT_FOR_RECONNECT:
                try:
                    if args:
                        result = func(self, args)
                    elif kwargs:
                        result = func(self, kwargs)
                    else:
                        result = func(self)
                except:
                    result = None
                if result:
                    logger.info(f'No need to reconnect, errors: {self.errors}')
                    self.reconnect_thread_count = 0
                    return True
                failed_count += 1
                logger.error(f'[{self.__class__.__name__}] function: [{func.__name__}] failed. retry [{failed_count}]')
                time.sleep(0.01)
            self.reconnect_thread_count -= 1
            return False

    @try_except_with_locker
    def read(self, **kwargs):
        return self._read(**kwargs)

    @abstractmethod
    def _read(self, **kwargs) -> Optional[Union[list, dict, int, float, str, bool, bytes, None]]:
        pass

    @try_except_with_locker
    def write(self, **kwargs):
        return self._write(**kwargs)

    @abstractmethod
    def _write(self, **kwargs) -> Any:
        pass

    @try_except_with_locker
    def connect(self):
        return self._connect()

    @abstractmethod
    def _connect(self) -> bool:
        pass

    @try_except_with_locker
    def disconnect(self):
        return self._disconnect()

    @abstractmethod
    def _disconnect(self):
        pass

    @classmethod
    @cls_try_except_with_locker
    def encode_to_write(cls, **kwargs):
        return cls._encode_to_write(**kwargs)

    @classmethod
    def _encode_to_write(cls, **kwargs) -> Optional[Union[list, dict, int, float, str, bool, bytes, None]]:
        pass

    @classmethod
    @cls_try_except_with_locker
    def decode_from_read(cls, **kwargs):
        return cls._decode_from_read(**kwargs)

    @classmethod
    def _decode_from_read(cls, **kwargs) -> Optional[Union[list, dict, int, float, str, bool, bytes, None]]:
        pass

    @staticmethod
    def support_datatype() -> dict:
        return {}

    @staticmethod
    def additional_field() -> dict:
        return {}
