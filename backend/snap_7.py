import snap7
import time
import snap7.util

from backend.communication_base import *
from typing import Any, Optional, Tuple, Union
import logging

# 日志配置
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Snap7(CommunicationBase):

    # limit of consecutive read/write
    MAX_CONSECUTIVE_READ_WRITE_LENGTH = 1
    SUPPORTED_DATATYPE = ["int8", "str", "int", "float", "bool"]

    def __init__(self, host: str, port: int, rack: int, slot: int, callback) -> None:
        super().__init__(host, port, callback=callback)
        self.write_times = 0
        self.rack = rack
        self.slot = slot

    def _read(self, **kwargs) -> Optional[list]:
        """
        read holding registers
        input:
            address, lenght
        returns
            resp
        """
        try:
            with self.locker:
                address = kwargs.get("address")
                if not address:
                    # temp use in tecomx
                    return None
                datatype = kwargs.get("datatype")
                if address is None:
                    raise Exception("Must set address of ethernet")
                temp = address.split("_")
                bit_offset = 0
                if len(temp) == 3:
                    db_number = int(temp[0])
                    start_offset = int(temp[1])
                    bit_offset = int(temp[2])
                elif len(temp) == 2:
                    db_number = int(temp[0])
                    start_offset = int(temp[1])
                else:
                    raise Exception("Address format is not correct")
                if datatype == "bool":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_bool(reading, 0, bit_offset)  # pyright: ignore
                elif datatype == "int8":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_sint(reading, 0)  # pyrig
                elif datatype == "uint8":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_usint(reading, 0)  # pyrig
                elif datatype == "int":
                    reading = self.communication_fd.db_read(db_number, start_offset, 2)
                    ret = snap7.util.get_int(reading, 0)  # pyright: ignore
                elif datatype == "int32":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_dword(reading, 0)  # pyright: ignore
                elif datatype == "float":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_real(reading, 0)  # pyright: ignore
                elif datatype == "str":
                    reading = self.communication_fd.db_read(
                        db_number, start_offset, 254
                    )
                    ret = snap7.util.get_string(reading, 0)  # pyright: ignore
                else:
                    raise Exception(f"Unsupported datatype {datatype}")
                if ret is None:
                    return None
                if isinstance(ret, list):
                    ret = ret[0]
                return [ret]
        except Exception as ex:
            self.handle_error(ex)
            self.disconnect()
            self.connect()
            return None

    def _write(self, **kwargs) -> Optional[list]:
        """
        write holding registers
        input:
            address, value
        returns
            resp
        """
        try:
            with self.locker:
                address = kwargs.get("address")
                if not address:
                    # temp use in tecomx
                    return None
                value: Any = kwargs.get("value")
                check = kwargs.get("check")
                datatype = kwargs.get("datatype")
                if address is None:
                    raise Exception("Must set address of ethernet")
                temp = address.split("_")
                bit_offset = 0
                if len(temp) == 3:
                    db_number = int(temp[0])
                    start_offset = int(temp[1])
                    bit_offset = int(temp[2])
                elif len(temp) == 2:
                    db_number = int(temp[0])
                    start_offset = int(temp[1])
                else:
                    raise Exception("Address format is not correct")
                if datatype is None:
                    datatype = "int"
                # Since datatype is a string, we need to do string comparison to figure out the type of value
                if datatype not in str(type(value)):
                    if datatype == "str":
                        if isinstance(value, list):
                            temp = ""
                            for i in range(len(value)):
                                temp += str(value[i])
                            value = temp
                    elif datatype == "int8":
                        if isinstance(value, list):
                            value = value[0]
                        value = int(value)
                    elif datatype == "int32":
                        if isinstance(value, list):
                            value = value[0]
                        value = int(value)
                    elif datatype == "uint8":
                        if isinstance(value, list):
                            value = value[0]
                        value = int(value)
                    elif datatype == "int":
                        if isinstance(value, list):
                            value = value[0]
                        value = int(value)
                    elif datatype == "float":
                        if isinstance(value, list):
                            value = value[0]
                        value = float(value)
                    elif datatype == "bool":
                        if isinstance(value, list):
                            value = value[0]
                        value = bool(value)
                    else:
                        logger.error(
                            f"Unsupported datatype {datatype} for value {value} of type {type(value)}"
                        )
                if not self.is_connected:
                    raise Exception(
                        f"The conn not connected, can't send msg-{address}-{value}."
                    )

                if value is None:
                    raise Exception("Must set values of ethernet")

                if datatype == "bool":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    snap7.util.set_bool(  # pyright: ignore
                        reading, 0, bit_offset, value
                    )
                elif datatype == "int8":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    snap7.util.set_sint(reading, 0, value)  # pyright: ignore
                elif datatype == "uint8":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    snap7.util.set_usint(reading, 0, value)  # pyright: ignore
                elif datatype == "int":
                    reading = self.communication_fd.db_read(db_number, start_offset, 2)
                    snap7.util.set_int(reading, 0, value)  # pyright: ignore
                elif datatype == "int32":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    snap7.util.set_dword(reading, 0, value)  # pyright: ignore
                elif datatype == "float":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    snap7.util.set_real(reading, 0, value)  # pyright: ignore
                elif datatype == "str":
                    reading = self.communication_fd.db_read(
                        db_number, start_offset, 254
                    )
                    snap7.util.set_string(reading, 0, value)  # pyright: ignore
                else:
                    raise Exception(f"Unsupported datatype {datatype}")
                ret = self.communication_fd.db_write(db_number, start_offset, reading)
                if check:
                    result, ret = self.check(address, value, datatype)
                    if result:
                        logger.info(
                            f"Check success! write to address[{address}], write value[{value}], "
                            f"read value[{ret}] "
                        )
                    else:
                        logger.error(
                            f"Check failed! write to address[{address}], write value[{value}], "
                            f"read value[{ret}] "
                        )
                if type(value) == list:
                    return value
                if value is not None:
                    return [value]

        except Exception as ex:
            self.handle_error(ex)
            self.disconnect()
            self.connect()
            return None

    def check(
        self, address: str, value: Any, datatype: str, times: int = 3
    ) -> Tuple[bool, list]:
        try:
            with self.locker:
                for _ in range(times):
                    ret = self.read(address=address)
                    if ret is None:
                        return False, []
                    if type(ret) is list and ret[0] == value:
                        return True, [ret]

                    self.write(
                        address=address, value=value, datatype=datatype, check=False
                    )

                return False, []

        except Exception as e:
            self.handle_error(e)
            return False, []

    def handle_error(self, ex) -> None:
        self.errors.append(ex)
        if ex:
            logger.error(f"{ex}")
            time.sleep(1)

    def _connect(self) -> bool:
        if self.is_connected:
            return True

        communication_fd = snap7.client.Client()
        self.communication_fd = communication_fd
        self.communication_fd.connect(
            address=self.host, rack=self.rack, slot=self.slot
        )
        self.is_connected = True
        if self.callback:
            self.callback(True)
        logger.info("Connect success")

        return self.is_connected

    def _disconnect(self) -> None:
        if not self.is_connected:
            return

        self.communication_fd.disconnect()
        logger.info("Disconnect success")
        self.is_connected = False

    @classmethod
    def _encode_to_write(cls, **kwargs) -> Optional[Union[int, str, float, bool, list]]:
        value: Any = kwargs.get("value", None)
        return value

    @staticmethod
    def support_datatype():
        return {"int": {}, "str": {}, "float": {}, "bool": {}}

    @classmethod
    def decode_from_read(cls, **kwargs) -> Optional[Union[int, str, float, bool, list]]:
        response: Any = kwargs.get("response", None)
        return response

    @staticmethod
    def additional_field() -> dict:
        return {"rack": 0, "slot": 1}


if __name__ == "__main__":
    snap7_obj = Snap7(host="192.168.0.1", port=44818, rack=0, slot=1, callback=None)
    print(f"Snap7 connected: {snap7_obj.connect()}")
    # repeat_list=[4, 3, 2, 1, 0, 0, 0, 0, 0, 0]
    # sequences_intervals=[5000, 3000, 2000, 2000, 0, 0, 0, 0, 0, 0]
    # start_offset_address=2700
    # start_repeat_address=2660
    # for value in repeat_list:
    #     snap7_obj.write(address=f"1_{start_repeat_address}", value=value, datatype='int32')
    #     start_repeat_address+=4
    # for value in sequences_intervals:
    #     snap7_obj.write(address=f"1_{start_offset_address}", value=value, datatype='int32')
    #     start_offset_address+=4
    # from src.data.data_monitor import DataMonitor,create_benchmark_config
    # data_monitor_config=create_benchmark_config(
    #     base_benchmark_config=None,
    #     camera_resolution='5mp',
    #     model_resolution='5mp',
    #     share_memory_interval_time=30,
    #     seq_interval_ms=235
    # )
    # bh = DataMonitor(data_monitor_config)
    # bh.create_workbook()
    # bh.get_system_data(start_time=time.time())
    # each_start_time = time.time()
    # benchmark_counter = 300
    # time_s = time.time() - each_start_time
    # fps = benchmark_counter * 30 / time_s
    # bh.create_report({
    #     "total_part_count": benchmark_counter,
    #     "total_use_time": time_s,
    #     "fps": fps
    # })
    # print(f'Address:52018_0 write:{snap7_obj.write(address="1_4", value=1, datatype="uint8")}')
    # print(f'Address:52018_0 write:{snap7_obj.write(address="1_3", value=1, datatype="uint8")}')
    # print(f'Address:52018_0 write:{snap7_obj.write(address="1_2576", value=2, datatype="uint8")}')
    # print(f'Address:52018_0 write:{snap7_obj.write(address="1_2636", value=2, datatype="uint8")}')
    # print(f'Address:52018_0 write:{snap7_obj.write(address="1_2579", value=2, datatype="uint8")}')
    # print(f'Address:52018_0 read:{snap7_obj.read(address="1_2582",datatype="bool")}')
    # print(f'Address:52018_0 read:{snap7_obj.write(address="1_2582_3",value=True,datatype="bool")}')
    # print(f'Address:52018_0 read:{snap7_obj.read(address="1_5", datatype="uint8")}')
    # print(f'Address:52018_0 read:{snap7_obj.read(address="1_16", datatype="str")}')
    # print(f'Address:52018_0 read:{snap7_obj.read(address="1_272", datatype="str")}')

    print(f'Address:52018_0 read:{snap7_obj.read(address="1_6", datatype="int32")}')
    # print(
    #     f'Address:52018_0 wrote:{snap7_obj.write(address="52018_0", value=3, datatype="int")}'
    # )
    # print(f'Address:52018_8 read:{snap7_obj.read(address="52018_8", datatype="str")}')
    # print(
    #     f'Address:52018_8 wrote:{snap7_obj.write(address="52018_8", value="13", datatype="str")}'
    # )
    # print(f'Address:52018_2 read:{snap7_obj.read(address="52018_2", datatype="float")}')
    # print(
    #     f'Address:52018_2 wrote:{snap7_obj.write( address="52018_2", value=102.2342299, datatype="float")}'
    # )
    # print(f'Address:52018_6 read:{snap7_obj.read(address="52018_6", datatype="bool")}')
    # print(
    #     f'Address:52018_6 wrote:{snap7_obj.write(address="52018_6", value=False, datatype="bool")}'
    # )
    # print(
    #     f'Address:52018_264 read:{snap7_obj.read(address="52018_264", datatype="bool")}'
    # )
    # print(
    #     f'Address:52018_264 wrote:{snap7_obj.write(address="52018_264", value=False, datatype="bool")}'
    # )
    # print(
    #     f'Address:52018_264_1 read:{snap7_obj.read(address="52018_264_1", datatype="bool")}'
    # )
    # print(
    #     f'Address:52018_264_1 wrote:{snap7_obj.write(address="52018_264_1", value=False, datatype="bool")}'
    # )
    print(f"Disconnect:{snap7_obj.disconnect()}")