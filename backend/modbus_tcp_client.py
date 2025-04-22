import time
import socket
import struct

from umodbus.client import tcp
from threading import RLock, Thread, Event
import logging

# 日志配置
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#logger = log("communication", prefix="communication")


class ModbusTCP:
    def __init__(self, host, port) -> None:
        self.locker = RLock()
        self.communication_fd = None
        self.host = host
        self.port = port
        self.is_connected = False
        self.stop_event = Event()
        self.thread = Thread(target=self.auto_reconnect, args=[])

    def __del__(self):
        self.stop_event.set()
        if self.is_connected:
            self.disconnect()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def auto_reconnect(self):
        while not self.stop_event.is_set():
            self.connect()
            time.sleep(3)
        self.disconnect()

    def str_decode(self, response):
        # converting from signed two's complement to unsigned
        # processing hex string by removing 0x prefix and extending to length 4
        # changing endianness, removing null bytes, and decoding to gb2312
        return_value = ''
        for res in response:
            if res < 0:
                res += 65536
            res = hex(res)[2:].zfill(4)
            res = bytes.fromhex(res[2:] + res[:2]).replace(b'\x00', b'').decode('gb2312', errors='ignore')
            return_value += res
        return return_value

    def float_decode(self, response):
        # every two adjacent list elements are a float
        # converting from signed two's complement to unsigned
        # processing hex string by removing 0x prefix and extending to length 4
        # changing endianness, and unpacking as float
        return_value = []
        for i in range(0, len(response), 2):
            two_int = response[i:i + 2]
            list_hex = []
            for temp_int in two_int:
                if temp_int < 0:
                    temp_int += 65536
                temp_hex = hex(temp_int)[2:].zfill(4)
                list_hex.append(temp_hex)
            hex_str = list_hex[1] + list_hex[0]
            return_value.append(struct.unpack('!f', bytes.fromhex(hex_str))[0])
        return return_value

    def ulint_to_int(self, hex_list):
        """
        将16进制的list转换为10进制的int
        震裕plc用ulint格式写入寄存器，读取时需要转换为int
        """
        def dec_to_hex(n):
            return hex(n)[2:].zfill(4)

        hex_list = hex_list[::-1]
        num = int("".join([dec_to_hex(x) for x in hex_list]), 16)
        return num

    def read(self, **kwargs):
        """
        read holding registers
        input:
            slave_id, address, length
        returns
            resp
        """
        try:
            slave_id = kwargs.get("slave_id", 1)
            address = kwargs.get("addr")
            datatype = kwargs.get("datatype")
            if address is None:
                raise Exception("Must set address of modbus")
            length = kwargs.get("length", 1)
            address = int(address)
            msg = tcp.read_holding_registers(slave_id, address, length)
            response = tcp.send_message(msg, self.communication_fd)
            logger.info(f"(modbus_read) msg:{msg}, response:{response}\n, address:{address}")
            if datatype == 'str':
                response = self.str_decode(response)
            elif datatype == 'float':
                response = self.float_decode(response)
            if isinstance(response, (str, int, float)):
                response = [response]
            return response
        except Exception as ex:
            logger.exception(ex)
            self.handle_error(f'Read {kwargs.get("address")} error {ex}')
            return None

    def read_multi_addr(self, **kwargs):
        """
        """
        try:
            with self.locker:
                slave_id = kwargs.get("slave_id", 1)
                address = kwargs.get("addr")
                if address is None:
                    raise Exception("Must set address of modbus")
                length = kwargs.get("length", 1)
                address = int(address)
                msg = tcp.read_holding_registers(slave_id, address, length)
                response = tcp.send_message(msg, self.communication_fd)
                # logger.info(f"(modbus_read_multi_addr) msg:{msg}, response:{response}, address:{address}")
                return response
        except Exception as ex:
            logger.exception(ex)
            self.handle_error(f'Read {kwargs.get("address")} error {ex}')
            return None

    def str_convert_to_int(self, string):
        # converting string to list of ints
        # encoding to gb2312, each two splitting into a group, reversing each group
        # processing hex string by removing 0x prefix and extending to length 2
        # then converting to int
        # converting from unsigned to signed
        string = string.encode('gb2312')
        char_groups = [string[i:i + 2] for i in range(0, len(string), 2)]
        list_int = []
        for two_char in char_groups:
            two_char = two_char[::-1]
            temp_hex = ''
            for char in two_char:
                if isinstance(char, int):
                    temp_hex += hex(char)[2:].zfill(2)
                else:
                    temp_hex += hex(ord(char))[2:].zfill(2)
            list_int.append(int(temp_hex, 16))
        return list_int

    def float_convert_to_int(self, float_value):
        # converting float to list of ints
        # converting input parameters to a list of float type
        # converting every float to hex, every hex_string is 8 characters long
        # reversing the first and last four characters of hex_string
        # converting from unsigned to signed then converting to int
        list_int = []
        if not isinstance(float_value, (list, tuple)):
            float_value = [float_value]
        for index, temp_float in enumerate(float_value):
            if not isinstance(temp_float, float):
                float_value[index] = float(temp_float)
            hex_string = struct.pack('!f', float_value[index]).hex()
            for i in range(len(hex_string), 0, -4):
                list_int.append(int(hex_string[i - 4:i], 16))
        return list_int

    def write(self, **kwargs):
        """
        write holding registers
        input:
            slave_id, address, value
        returns
            resp
        """
        try:
            slave_id = kwargs.get("slave_id", 1)
            address = kwargs.get("addr")
            datatype = kwargs.get("datatype")
            value = kwargs.get("val")
            check = kwargs.get("check")
            heartbeat = kwargs.get("heartbeat")

            if not self.is_connected:
                raise Exception(f"The conn not connected, can't send msg-{address}-{value}.")

            if address is None:
                raise Exception("Must set address of modbus")
            if value is None:
                raise Exception("Must set value of modbus")
            address = int(address)

            if datatype == 'str':
                if value == '':
                    length = kwargs.get("length", 1)
                    processed_value = [0 for _ in range(length)]
                elif str(value).isdigit():
                    processed_value = self.str_convert_to_int(str(value))
                else:
                    processed_value = self.str_convert_to_int(value)
            elif datatype == 'int':
                processed_value = value
            elif datatype == 'float':
                processed_value = self.float_convert_to_int(value)
            else:
                processed_value = value

            if not isinstance(processed_value, (list, tuple, bytes)):
                processed_value = [processed_value]
            logger.info(f"(modbus_write) msg, address:{address}, processed_value:{processed_value}")
            msg = tcp.write_multiple_registers(slave_id, address, processed_value)
            response = tcp.send_message(msg, self.communication_fd)
            #logger.info(f"(modbus_write) msg:{msg}, response:{response}, address:{address}, processed_value:{processed_value}")
            if check:
                success, read_value = self.check(slave_id, address, processed_value, length=response)
                if success:
                    logger.info(
                        f"Check success! write to address[{address}], write value[{value}], "
                        f"read value[{read_value}] "
                    )
                else:
                    logger.error(
                        f"Check failed! write to address[{address}], write value[{value}], "
                        f"read value[{read_value}] "
                    )

            if not heartbeat:
                logger.info(f"write value: [{value}] | address = [{address}]")

            return response

        except Exception as ex:
            self.handle_error(f'Write {kwargs.get("address")} error {ex}')
            return None

    def check(self, slave_id, address, value, length=1, times=3):
        try:
            with self.locker:
                for _ in range(times):
                    msg = tcp.read_holding_registers(slave_id, address, length)
                    response = tcp.send_message(msg, self.communication_fd)

                    if response == value:
                        return True, response
                    else:
                        msg = tcp.write_multiple_registers(slave_id, address, value)
                        response = tcp.send_message(msg, self.communication_fd)

                return False, response

        except Exception as ex:
            self.handle_error(ex)
            return None, None

    def handle_error(self, ex):
        if ex:
            logger.error(ex)

    def connect(self):
        if self.is_connected:
            return True

        with self.locker:
            try:
                communication_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                communication_fd.settimeout(3)
                communication_fd.connect((self.host, self.port))
                self.communication_fd = communication_fd
                self.is_connected = True
                logger.info("Connect success")
            except Exception as ex:
                self.handle_error(f"Connect error: {ex}")

            return self.is_connected

    def disconnect(self):
        if not self.is_connected:
            return

        try:
            self.communication_fd.close()
        except Exception as ex:
            self.handle_error(f"Disconnect error: {ex}")
        self.is_connected = False