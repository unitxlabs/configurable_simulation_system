import snap7
import time
import struct
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
    SUPPORTED_DATATYPE = ["str", "int", "float", "bool"]

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
                    ret = snap7.util.get_bool(reading, 0, bit_offset)

                elif datatype == "byte":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_byte(reading, 0)

                elif datatype == "word":
                    reading = self.communication_fd.db_read(db_number, start_offset, 2)
                    ret = snap7.util.get_word(reading, 0)

                elif datatype == "dword":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_dword(reading, 0)

                elif datatype == "int":
                    reading = self.communication_fd.db_read(db_number, start_offset, 2)
                    ret = snap7.util.get_int(reading, 0)

                elif datatype == "dint":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_dint(reading, 0)

                elif datatype == "udint":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_dword(reading, 0)  # same as dword

                elif datatype == "sint":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_sint(reading, 0)

                elif datatype == "usint":
                    reading = self.communication_fd.db_read(db_number, start_offset, 1)
                    ret = snap7.util.get_byte(reading, 0)

                elif datatype == "float":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_real(reading, 0)

                elif datatype == "lreal":
                    reading = self.communication_fd.db_read(db_number, start_offset, 8)
                    ret = snap7.util.get_lreal(reading, 0)

                elif datatype == "time":
                    reading = self.communication_fd.db_read(db_number, start_offset, 4)
                    ret = snap7.util.get_dint(reading, 0)  # PLC 中 TIME 类型是 DINT，单位 ms

                elif datatype == "str":
                    reading = self.communication_fd.db_read(db_number, start_offset, 254)
                    ret = snap7.util.get_string(reading, 0)
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
                # if datatype not in str(type(value)):
                #     if datatype == "str":
                #         if isinstance(value, list):
                #             temp = ""
                #             for i in range(len(value)):
                #                 temp += str(value[i])
                #             value = temp
                #     elif datatype == "int":
                #         if isinstance(value, list):
                #             value = value[0]
                #         value = int(value)
                #     elif datatype == "float":
                #         if isinstance(value, list):
                #             value = value[0]
                #         value = float(value)
                #     elif datatype == "bool":
                #         if isinstance(value, list):
                #             value = value[0]
                #         value = bool(value)
                #     else:
                #         logger.error(
                #             f"Unsupported datatype {datatype} for value {value} of type {type(value)}"
                #         )
                if not self.is_connected:
                    raise Exception(
                        f"The conn not connected, can't send msg-{address}-{value}."
                    )
                if value is None:
                    raise Exception("Must set values of ethernet")
                if isinstance(value, list):
                    packed_data = struct.pack(f'>{len(value)}h', *value)
                    self.communication_fd.write_area(snap7.Area.DB,db_number=db_number,start=start_offset, data=packed_data)
                    if check:
                        result, ret = self.check_list(db=db_number,start=start_offset, value=value, datatype=datatype)
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
                    return value                
                else:
                    if datatype == "bool":
                        reading = self.communication_fd.db_read(db_number, start_offset, 1)
                        snap7.util.set_bool(reading, 0, bit_offset, value)

                    elif datatype == "byte":
                        reading = self.communication_fd.db_read(db_number, start_offset, 1)
                        snap7.util.set_byte(reading, 0, value)

                    elif datatype == "word":
                        reading = self.communication_fd.db_read(db_number, start_offset, 2)
                        snap7.util.set_word(reading, 0, value)

                    elif datatype == "dword":
                        reading = self.communication_fd.db_read(db_number, start_offset, 4)
                        snap7.util.set_dword(reading, 0, value)

                    elif datatype == "int":
                        reading = self.communication_fd.db_read(db_number, start_offset, 2)
                        snap7.util.set_int(reading, 0, value)

                    elif datatype == "dint":
                        reading = self.communication_fd.db_read(db_number, start_offset, 4)
                        snap7.util.set_dint(reading, 0, value)

                    elif datatype == "udint":
                        reading = self.communication_fd.db_read(db_number, start_offset, 4)
                        print(value)
                        snap7.util.set_dword(reading, 0, value)  # uint32

                    elif datatype == "sint":
                        reading = self.communication_fd.db_read(db_number, start_offset, 1)
                        snap7.util.set_sint(reading, 0, value)

                    elif datatype == "usint":
                        reading = self.communication_fd.db_read(db_number, start_offset, 1)
                        snap7.util.set_byte(reading, 0, value)

                    elif datatype == "float":
                        reading = self.communication_fd.db_read(db_number, start_offset, 4)
                        snap7.util.set_real(reading, 0, value)

                    elif datatype == "lreal":
                        reading = self.communication_fd.db_read(db_number, start_offset, 8)
                        snap7.util.set_lreal(reading, 0, value)

                    elif datatype == "time":
                        reading = self.communication_fd.db_read(db_number, start_offset, 4)
                        snap7.util.set_dint(reading, 0, value)  # TIME 类型通常是 DINT

                    elif datatype == "str":
                        reading = self.communication_fd.db_read(db_number, start_offset, 254)
                        snap7.util.set_string(reading, 0, value)

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
    def check_list(
        self, db: int,start:int, value: list, datatype: str, times: int = 3
    ) -> Tuple[bool, list]:
        try:
            with self.locker:
                # format_map = {
                #     "byte": ("B", 1),
                #     "word": ("H", 2),
                #     "dword": ("I", 4),
                #     "int": ("h", 2),
                #     "dint": ("i", 4),
                #     "udint": ("I", 4),
                #     "sint": ("b", 1),
                #     "usint": ("B", 1),
                #     "float": ("f", 4),
                #     "lreal": ("d", 8),
                #     "time": ("I", 4),
                #     "str": ("str", 256),
                # }
                size=2*len(value)
                if datatype == "bool":
                    size=1*len(value)
                elif datatype == "byte":
                    size=1*len(value)

                elif datatype == "word":
                    size=2*len(value)

                elif datatype == "dword":
                    size=4*len(value)

                elif datatype == "int":
                    size=2*len(value)

                elif datatype == "dint":
                    size=4*len(value)


                elif datatype == "udint":
                    size=4*len(value)


                elif datatype == "sint":
                    size=1*len(value)

                elif datatype == "usint":
                    size=1*len(value)

                elif datatype == "float":
                    size=4*len(value)
                elif datatype == "lreal":
                    size=8*len(value)
                elif datatype == "time":
                    size=4*len(value)
                elif datatype == "str":
                    size=254*len(value)
                for _ in range(times):
                    ret=list(struct.unpack(f'>{len(value)}h',self.communication_fd.read_area(snap7.Area.DB,db_number=db,start=start, size=size)))
                    if ret is None:
                        return False, []
                    if  ret== value:
                        return True, [ret]

                    self.write(
                        address=f'{db}_{start}', value=value, datatype=datatype, check=False
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
    # print(f'Address:1_0 read:{snap7_obj.read(address="1_0_0", datatype="bool")}')
    # print(
    #     f'Address:1_0 wrote:{snap7_obj.write(address="1_0_0", value=True, datatype="bool")}'
    # )
    print(f'Address:1_3062 wrote:{snap7_obj.write(address="1_2584_0",value=[True,False,False,True], datatype="bool")}')
    print(f'Address:1_3062 check:{snap7_obj.check_list(db=1,start=2584,value=[True,False,False,True], datatype="bool")}')

    print(f'Address:1_3062 wrote:{snap7_obj.write(address="1_3062_0",value=[100,200,300,500], datatype="int")}')
    print(f'Address:1_3062 check:{snap7_obj.check_list(db=1,start=3062,value=[100,200,300,500], datatype="int")}')
    # int_list = [100, 200, 300]
    # # '>3h' 表示大端序（S7 是 big endian），3 个 short（每个2字节）
    # packed_data = struct.pack('>3h', *int_list)
    # print(
    #     f'Address:1_3062_0 wrote:{snap7_obj.communication_fd.write_area(snap7.Area.DB,db_number=1,start=3062, data=packed_data)}'
    # )
    # print(
    #     f'Address:1_3062_0 wrote:{list(struct.unpack(">3h",snap7_obj.communication_fd.read_area(snap7.Area.DB,db_number=1,start=3062, size=6)))}'
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
    # print(f"Disconnect:{snap7_obj.disconnect()}")
