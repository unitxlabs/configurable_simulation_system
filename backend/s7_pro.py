import snap7
import time
import snap7.util
from backend.communication_base import *
from backend.address_protocol_scripts import *

class S7Pro(CommunicationBase):
    """
        Snap7 is a protocol used by Siemens PLCs to communicate with external devices.
        input:
            host: ip address of PLC, str, such as "192.168.0.1"
            port: port of PLC, int, default is 44818, Snap7 don't need port
            callback: callback function, such as self.connect_callback, default is None
            rack: int, default is 0, if don't set, please ask PLC engineer.
            slot: int, default is 1, if don't set, please ask PLC engineer.
            db_number: int, default is 1, please ask PLC engineer which db number to use.
    """

    # limit of consecutive read/write 64KB
    MAX_CONSECUTIVE_READ_WRITE_LENGTH = 32768
    SUPPORTED_DATATYPE = ["str", "int", "float", "bool", 'bytes', 'origin', 'byte']

    def __init__(self, host: str, port: int = 44818, callback=None, rack: int = 0, slot: int = 1,
                 db_number: int = 1) -> None:
        super().__init__(host, port, callback=callback)
        self.port = int(port)
        self.db_number = int(db_number)
        self.rack = int(rack)
        self.slot = int(slot)

    @staticmethod
    def datatype_to_size(datatype, length, is_read=True, value=None):
        if length:
            if isinstance(length, str):
                length = int(length)
            if datatype =="int8":
                return 1* length
            elif datatype in ["int", "bool"]:
                return length * 2
            elif datatype in ["float", "int32"]:
                return length // 2 * 4
            elif datatype == "str":
                return (length + 127) // 128 * 256 if is_read else (length + 127) // 128 * 254
            return length * 2
        else:
            if isinstance(value, list):
                length = len(value)
            elif datatype in ["bytes", "origin", "byte"]:
                return len(value)  # pyright: ignore [reportArgumentType]
            else:
                length = 1
            if datatype =="int8":
                return 1* length
            elif datatype == ["int", "bool"]:
                return 2 * length
            elif datatype in ["float", "int32"]:
                return 4 * length
            elif datatype == "str":
                return 254 * length if is_read else 254 * length
            else:
                return 2 * length

    @staticmethod
    def write_bytes_to_bytes_str(bytes_str):
        return_bytes = b''
        total_len_bytes = len(bytes_str)
        split_bytes_list = []
        for i in range(0, total_len_bytes, 254):
            split_bytes_list.append(bytes_str[i:i + 254])

        for split_bytes in split_bytes_list:
            _len_bytes = 0
            for index, b in enumerate(split_bytes):
                if b != 0:
                    _len_bytes = index + 1
            return_bytes += b'\xfe' + _len_bytes.to_bytes(1, byteorder='big') + split_bytes

        return return_bytes

    @staticmethod
    def read_bytes_to_bytes_str(bytes_str):
        return_bytes = b''
        total_len_bytes = len(bytes_str)
        split_bytes_list = []
        for i in range(0, total_len_bytes, 254):
            split_bytes_list.append(bytes_str[i:i + 254])

        for split_bytes in split_bytes_list:
            return_bytes += split_bytes[0:]

        return return_bytes

    @staticmethod
    def bool_get_bit(bool_list, bit):
        if bit is None:
            return bool_list

        depth = max_bool_list_depth(bool_list)
        if depth == 1:
            return bool_list[bit]
        else:
            return [sub_list[bit] for sub_list in bool_list]

    @staticmethod
    def bool_set_bit(bool_bytes, bit, value):
        split_bytes = [bool_bytes[i:i + 2] for i in range(0, len(bool_bytes), 2)]
        for index, b in enumerate(split_bytes):
            snap7.util.set_bool(b, 0, bit, value)  # pyright: ignore [reportAttributeAccessIssue]
            split_bytes[index] = b
        return b''.join(split_bytes)

    def _read(self, **kwargs):
        address = kwargs.get("address")
        if address is None:
            raise Exception("Must set address of Snap 7")
        if isinstance(address, str):
            address = int(address)
        bool_bit = kwargs.get("bool_bit")

        datatype = kwargs.get("datatype", "int")
        size = self.datatype_to_size(datatype, kwargs.get("length", None))

        decode = kwargs.get("decode", "default")
        reverse = kwargs.get("reverse", False)
        normal = kwargs.get("normal", True)
        response = self.communication_fd.db_read(self.db_number, address, size)
        return self._decode_from_read(response=response, datatype=datatype, decode=decode, reverse=reverse,
                                      normal=normal, bool_bit=bool_bit)

    def _write(self, **kwargs):
        address = kwargs.get("address")
        if address is None:
            raise Exception("Must set address of Snap 7")
        if isinstance(address, str):
            address = int(address)

        value: Any = kwargs.get("value")
        if value is None:
            raise Exception("Must set values of Snap 7")

        datatype = kwargs.get("datatype", "int")
        size = self.datatype_to_size(datatype, kwargs.get("length", None), is_read=False, value=value)
        length = size // 2
        decode = kwargs.get("decode", "default")
        reverse = kwargs.get("reverse", False)
        bool_bit = kwargs.get("bool_bit")

        if bool_bit is not None:
            read_data = self.communication_fd.db_read(self.db_number, address, size)
        else:
            read_data = None

        bytes_write_value = self._encode_to_write(
            value=value, datatype=datatype, length=length, decode=decode, reverse=reverse, bool_bit=bool_bit,
            address=address, read_data=read_data)

        self.communication_fd.db_write(self.db_number, address, bytes_write_value)

        # db_Write can't return write bytes. so return True
        return True

    def _connect(self) -> bool:
        if self.is_connected:
            return True

        communication_fd = snap7.client.Client()
        self.communication_fd = communication_fd
        self.communication_fd.connect(address=self.host, rack=self.rack, slot=self.slot)
        if self.communication_fd.get_connected():
            self.is_connected = True
        if self.callback:
            self.callback(True)
        logger.info(f"PROTOCOL TYPE: [{self.__class__.__name__}] - Connect success")

        return self.is_connected

    def _disconnect(self) -> None:
        if not self.is_connected:
            return

        self.communication_fd.disconnect()
        self.is_connected = False

    @classmethod
    def _encode_to_write(cls, **kwargs):
        """
            encode value to bytes
            input:
                value: int, float, str, bool, bytes, list, such as 1, 1.0, "1", True, b'\x01\x02\x03\x04', [1, 2, 3, 4]
                length: int, such as 10, max length is 997
                datatype: str, such as "int", "float", "str", "bool", "byte", "origin", "bytes", default is "int"
                decode: only for str datatype, such as "default", "unicode", "high", "low", default is "default"
                reverse: only for str datatype, such as True, False, default is False
            return:
                bytes
        """
        value = kwargs.get("value")
        datatype = kwargs.get("datatype", "int")
        length = kwargs.get("length")
        decode = kwargs.get("decode", "default")
        reverse = kwargs.get("reverse", False)
        bool_bit = kwargs.get("bool_bit", None)
        if datatype == "int8":
            bytes_write_value = int8_to_bytes(value)
        elif datatype == "int":
            bytes_write_value = int_to_bytes(value)
        elif datatype == "int32":
            bytes_write_value = int32_to_bytes(value)
            bytes_write_value = four_bytes_reverse(bytes_write_value)
        elif datatype == "float":
            bytes_write_value = float_to_bytes(value)
            bytes_write_value = four_bytes_reverse(bytes_write_value)
        elif datatype == "str":
            if decode == "default":
                bytes_write_value = str_to_bytes_default(value, length, reverse)
            elif decode == "unicode":
                bytes_write_value = str_to_bytes_unicode(value, length)
            elif decode == "low":
                bytes_write_value = str_to_bytes_low(value, length)
            elif decode == "high":
                bytes_write_value = str_to_bytes_high(value, length)
            else:
                raise Exception(f'Write Error: Unsupported str decode: {decode}')
            bytes_write_value = cls.write_bytes_to_bytes_str(bytes_write_value)
        elif datatype == "bool":
            if bool_bit is None:
                bytes_write_value = bool_to_bytes(value, reverse)
                bytes_write_value = two_bytes_reverse(bytes_write_value)
            else:
                read_data = kwargs.get("read_data")
                bytes_write_value = cls.bool_set_bit(read_data, bool_bit, value)
        elif datatype in ["bytes", "origin", "byte"]:
            bytes_write_value = bytes_to_bytes(value, length)
        else:
            raise Exception(f'Write Error: Unsupported datatype: {datatype}')

        return bytes_write_value

    @classmethod
    def _decode_from_read(cls, **kwargs):
        """
        decode bytes to value
        input:
            response: bytes
            datatype: str, such as "int", "float", "str", "bool", "byte", "origin", "bytes", default is "int"
            decode: only for str datatype, such as "default", "unicode", "high", "low", default is "default"
            reverse: only for str datatype, such as True, False, default is True
            normal: only for str datatype, such as True, False, default is True
        return:
            value: int, float, str, bool, bytes, list, such as 1, 1.0, "1", True, b'\x01\x02\x03\x04', [1, 2, 3, 4]
        """
        response = kwargs.get("response")
        datatype = kwargs.get("datatype", "int")
        decode = kwargs.get("decode", "default")
        reverse = kwargs.get("reverse", False)
        normal = kwargs.get("normal", True)
        bool_bit = kwargs.get("bool_bit", None)
        if datatype == "int8":
            response = bytes_to_int8(response)
        elif datatype == 'int':
            response = bytes_to_int(response)
        elif datatype == 'str':
            ret = snap7.util.get_string(response, 0)
            if ret == "":
                response= [ret]
            else:
                response = cls.read_bytes_to_bytes_str(response)
                if decode == "default":
                    response = bytes_to_str_default(response, reverse)
                elif decode == "unicode":
                    response = bytes_to_str_unicode(response)
                elif decode == "high":
                    response = bytes_to_str_high(response)
                elif decode == "low":
                    response = bytes_to_str_low(response)
                else:
                    raise Exception(f"Read Error: Unsupported str decode: {decode}")
                if normal:
                    response = get_normal_char(response)
        elif datatype == 'float':
            response = four_bytes_reverse(response)
            response = bytes_to_float(response)
        elif datatype == 'int32':
            response = four_bytes_reverse(response)
            response = bytes_to_int32(response)
        elif datatype == 'bool':
            response = two_bytes_reverse(response)
            response = bytes_to_bool(response, reverse)
            response = cls.bool_get_bit(response, bool_bit)
        elif datatype in ["byte", "bytes", "origin"]:
            response = response
        else:
            raise Exception(f"Read Error: Unsupported datatype: {datatype}")

        return response

    @staticmethod
    def support_datatype() -> dict:
        return {
            "int8": {},
            "int": {},
            "int32": {},
            "str": {"decode": ["default", "unicode", "low", "high"],
                    "reverse": [True, False],
                    "normal": [True, False]
                    },
            "bool": {"reverse": [True, False]},
            "float": {},
            "bytes": {}
        }

    @staticmethod
    def additional_field() -> dict:
        return {"rack": 0, "slot": 1, "db_number": 1}


if __name__ == "__main__":
    snap7_obj = S7Pro(host="192.168.0.1", port=44818, rack=0, slot=1, callback=None)
    print(f"Snap7 connected: {snap7_obj.connect()}")
    # print(f'Address:1_2662 wrote:{snap7_obj.write(address="3",value=1, datatype="int8")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="3",length=1,datatype="int8")}')
    print(f'Address:1_2662 wrote:{snap7_obj.write(address="272",value="db_number22222", datatype="str")}')
    # print(f'Address:1_2662 wrote:{snap7_obj.write(address="2576",value=1, datatype="int8")}')
    print(f'Address:1_2662 read:{snap7_obj.write(address="4",value=1,datatype="int8")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="4",length=1,datatype="int8")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="272", datatype="str")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="2576",length=1,datatype="int8")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="4",length=1,datatype="int8")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="16",datatype="str")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="272",datatype="str")}')
    # print(f'Address:1_2662 read:{snap7_obj.read(address="528",datatype="str")}')
    # print(
    #     f'Address:1_0 wrote:{snap7_obj.write(address="0", value=[True], datatype="bool")}'
    # )
    # print(f'Address:1_0 read:{snap7_obj.read(address="0",datatype="bool")}')

    # print(f'Address:1_2584 wrote:{snap7_obj.write(address="2584",value=[True,False,False,True], datatype="bool")}')
    # print(f'Address:1_0 read:{snap7_obj.read(address="2584",datatype="bool")}')



    # print(f'STR read:{snap7_obj.read(address="0", length=384, datatype="str")}')
    # print(f'STR write:{snap7_obj.write(address="0", value="Abcd1234" * 96, length=384, datatype="str")}')
    # print(f'Address:1_2656 wrote:{snap7_obj.write(address="8",value="asd", datatype="str")}')
    # print(f'Address:1_2656 wrote:{snap7_obj.read(address="8",datatype="str")}')
    # print(f'Address:1_2662 wrote:{snap7_obj.write(address="2662",value=[6,0,0,0,0,0,0,0,0,6], datatype="int8")}')
    # print(f'Address:1_2662 wrote:{snap7_obj.read(address="2662",length=10,datatype="int8")}')
    # print(f'BOOL_BIT read:{snap7_obj.read(address="768", bool_bit=0, length=2, datatype="bool")}')
    # print(f'BOOL_BIT write:{snap7_obj.write(address="768", bool_bit=0, length=2, value=False, datatype="bool")}')

    # print(f'FLOAT read:{snap7_obj.read(address="772", length=6, datatype="float")}')
    # print(f'FLOAT write:{snap7_obj.write(address="772", value=[111.11, 222.22, 333.33], datatype="float")}')

    # print(f'INT read:{snap7_obj.read(address="784", length=3, datatype="int")}')
    # print(f'INT write:{snap7_obj.write(address="784", value=[111, 222, 333], datatype="int")}')

    # print(f'INT32 read:{snap7_obj.read(address="790", length=6, datatype="int32")}')
    # print(
    #     f'INT32 write:{snap7_obj.write(address="790", value=[1113123123, 2021231231, 33555454], datatype="int32")}')

    # print(f'BYTES read:{snap7_obj.read(address="802", length=2, datatype="bytes")}')
    # bytes_value = b"\x01\x02\x03\x04"
    # print(f'BYTES write:{snap7_obj.write(address="802", value=bytes_value, datatype="bytes")}')

    print(f"Disconnect:{snap7_obj.disconnect()}")
