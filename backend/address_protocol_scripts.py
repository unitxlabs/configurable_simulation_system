import struct
import time

"""
read holding registers
input:
    address: int, such as 0
    length: int, such as 10, max length is MAX_CONSECUTIVE_READ_WRITE_LENGTH, default is 1
    datatype: str, such as "int", "float", "str", "bool", "byte", "origin", "bytes", default is "int"
        if datatype is "int", support int range is [-32768, 65535].
            if you want to read int value from address 0, you can use:
                read(address=0, datatype="int")
            if you want to read int value from address 0 and 1, you can use:
                read(address=0, length=2, datatype="int")

        if datatype is "int32", support int range is [-2147483648, 2147483647].
        Every int32 value is 2 length, such as 1 is 2 length, 2147483647 is 2 length.
            if you want to read int value from address 0, you can use:
                read(address=0, datatype="int32", length=2)
            if you want to read int value from address 0 and 1, you can use:
                read(address=0, length=4, datatype="int32")

        (**Abandon) if datatype is "float", support float range is [-3.4028235E+38, 3.4028235E+38].
        Every float value is 2 length, such as 1.0 is 2 length, 44444.44 is 2 length.
        Float value can only be precise up to 7 digits. such as 1234567.0 or 1234.567 or 1.234567
            if you want to read float value from address 0, you can use:
                read(address=0, datatype="float", length=2)
            if you want to read float value from address 0 and 1, you can use:
                read(address=0, length=4, datatype="float")

        if datatype is "str", support str length is [1, MAX_CONSECUTIVE_READ_WRITE_LENGTH]. default decode is "default".
            if decode is "default", the str value will be decoded by gbk.
            You can use "reverse" to change the decode order.
            You can use "normal" = False to get the original str value.
            You can only read chinese characters by "normal" = False.
                Every str value is 0.5 length, such as "1" is 1 length, "abCD" is 2 length.
                Every Chinese character is 1 length, such as "中" is 1 length, "中文" is 2 length.
                    if you want to read str value from address 0, you can use:
                        read(address=0, datatype="str")
                    if you want to read str value from address 0 and 1, you can use:
                        read(address=0, length=2, datatype="str")
            if decode is "unicode", the str value will be decoded by unicode.
                Every str value is 1 length, such as "1" is 1 length, "abCD" is 4 length.
                Every Chinese character is 1 length, such as "中" is 1 length, "中文" is 2 length.
                    if you want to read str value from address 0, you can use:
                        read(address=0, datatype="str", decode="unicode")
                    if you want to read str value from address 0 and 1, you can use:
                        read(address=0, length=2, datatype="str", decode="unicode")
            if decode is "high" or "low", the str value will be decoded by unicode.
                Every str value is 1 length, such as "1" is 1 length, "abCD" is 4 length.
                Every Chinese character is 1 length, such as "中" is 1 length, "中文" is 2 length.
                When decode is "high" or "low", the Chinese char will decode to a Garbled.
                    if you want to read str value from address 0, you can use:
                        read(address=0, datatype="str", decode="low")
                    if you want to read str value from address 0 and 1, you can use:
                        read(address=0, length=2, datatype="str", decode="high")

        if datatype is "bool", every bool value must be a 16 elements list of bool.
            if you want to read bool value from address 0, you can use:
                read(address=0, datatype="bool")
            if you want to read bool value from address 0 and 1, you can use:
                read(address=0, length=2, datatype="bool")

        if datatype is "bytes" or "origin" or "byte", support bytes length is [1, MAX_CONSECUTIVE_READ_WRITE_LENGTH].
        Every byte value is 0.5 length, such as b'\x01\x00' is 2 length, b'\x01bcd' is 2 length.
            if you want to read bytes value from address 0, you can use:
                read(address=0, datatype="bytes")
            if you want to read bytes value from address 0 and 1, you can use:
                read(address=0, length=2, datatype="bytes")

return:
    list
    such as:
    if datatype is "int", return [int] or [int, int, ...]
    if datatype is "int32", return [int32] or [int32, int32, ...]
    if datatype is "float", return [float] or [float, float, ...]
    if datatype is "str", return [str]
    if datatype is "bool", return [bool, bool, ...] or [[bool, bool, ...], [bool, bool, ...], ...]
    if datatype is "bytes" or "origin" or "byte", return [bytes]
"""

"""
write holding registers
input:
    address: int, such as 0
    length: int, such as 10, max length is MAX_CONSECUTIVE_READ_WRITE_LENGTH, default is 1
    datatype: str, such as "int", "float", "str", "bool", "byte", "origin", "bytes", default is "int"
        if datatype is "int", support int range is [-32768, 65535].
            if you want to write int value -12 to address 0, you can use:
                write(address=0, value=-12, datatype="int")
            if you want to write int value 65535 to address 0 and -2222 to address 1, you can use:
                write(address=0, value=[65535, -2222], datatype="int")

        if datatype is "int32", support int range is [-2147483648, 2147483647].
        Every int32 value is 2 length, such as 1 is 2 length, 2147483647 is 2 length.
            if you want to write int value -122233222 to address 0,1, you can use:
                write(address=0, value=-122233222, datatype="int32")
            if you want to write int value 2147483647 to address 0,1 and -222332222 to address 2,3, you can use:
                write(address=0, value=[2147483647, -222332222], datatype="int32")
        You can use int32 to replace float, tell PLC to divide 10000 or 1000000 to get the float value.

        (**Abandon) if datatype is "float", support float range is [-3.4028235E+38, 3.4028235E+38].
        Every float value is 2 length, such as 1.0 is 2 length, 44444.44 is 2 length.
        Float value can only be precise up to 7 digits. such as 1234567.0 or 1234.567 or 1.234567
            if you want to write float value -12.3 to address 0, you can use:
                write(address=0, value=-12.3, datatype="float")
            if you want to write float value 65535.0 to address 0,1 and -2222.0 to address 2,3, you can use:
                write(address=0, value=[65535.0, -2222.0], datatype="float")

        if datatype is "str", support str length is [1, MAX_CONSECUTIVE_READ_WRITE_LENGTH]. default decode is "default".
            You can use "reverse" to change the decode order.
            if decode is "default", the str value will be encoded by gbk.
                Every str value is 0.5 length, such as "1" is 1 length, "abCD" is 2 length.
                Every Chinese character is 1 length, such as "中" is 1 length, "中文" is 2 length.
                if you input length, the str value will be filled with '\x00' to the length you input.
                also will cut the str value to the length you input.
                    If you want to write str value "1234567890" to address 0, you can use:
                        write(address=0, value="1234567890", datatype="str")
                    If you want to write str value "1234567890" to address 0, length=4, you can use:
                        write(address=0, value="1234567890", length=4, datatype="str")
                        But the value will be cut to "12345678"
                    If you want to write str value "1234567890" to address 0, length=6, you can use:
                        write(address=0, value="1234567890", length=12, datatype="str")
                        But the value will be filled with '\x00' to "1234567890\x00\x00"
            if decode is "unicode", the str value will be encoded by unicode.
                Every str value is 1 length, such as "1" is 1 length, "abCD" is 4 length.
                Every Chinese character is 1 length, such as "中" is 1 length, "中文" is 2 length.
                if you input length, the str value will be filled with '\x00' to the length you input.
                also will cut the str value to the length you input.
                    If you want to write str value "1234567890" to address 0, you can use:
                        write(address=0, value="1234567890", datatype="str", decode="unicode")
                    If you want to write str value "1234567890" to address 0, length=4, you can use:
                        write(address=0, value="1234567890", length=4, datatype="str", decode="unicode")
                        But the value will be cut to "1234"
                    If you want to write str value "1234567890" to address 0, length=12, you can use:
                        write(address=0, value="1234567890", length=12, datatype="str", decode="unicode")
                        But the value will be filled with '\x00' to "1234567890\x00\x00"
            if decode is "high" or "low", the str value will be encoded by unicode.
                Every str value is 1 length, such as "1" is 1 length, "abCD" is 4 length.
                !!! high or low decode can't support Chinese chars.
                if you input length, the str value will be filled with '\x00' to the length you input.
                also will cut the str value to the length you input.
                    If you want to write str value "1234567890" to address 0, you can use:
                        write(address=0, value="1234567890", datatype="str", decode="unicode")
                    If you want to write str value "1234567890" to address 0, length=4, you can use:
                        write(address=0, value="1234567890", length=4, datatype="str", decode="low")
                        But the value will be cut to "1234"
                    If you want to write str value "1234567890" to address 0, length=12, you can use:
                        write(address=0, value="1234567890", length=12, datatype="str", decode="high")
                        But the value will be filled with '\x00' to "1234567890\x00\x00"

        if datatype is "bool", every bool value must be a 16 elements list of bool.
            if you want to write bool value [True, False, True, False, True, False, True, False,
                                            True, False, True, False, True, False, True, False] to address 0,
                you can use:
                    write(address=0, value=[True, False, True, False, True, False, True, False,
                                            True, False, True, False, True, False, True, False],
                            datatype="bool")
            if you want to write bool value [True, False, True, False, True, False, True, False,
                                            True, False, True, False, True, False, True, False] to address 0,
                and [False, True, False, True, False, True, False, True, False, True, False, True,
                        False, True, False, True] to address 1, you can use:
                    write(address=0, value=[[True, False, True, False, True, False, True, False,
                                                True, False, True, False, True, False, True, False],
                                            [False, True, False, True, False, True, False, True,
                                                False, True, False, True, False, True, False, True]],
                            datatype="bool")

        if datatype is "bytes" or "origin" or "byte", support bytes length is [1, MAX_CONSECUTIVE_READ_WRITE_LENGTH].
        Every bytes value is 0.5 length, such as b'\x01\x00' is 1 length, b'\x01bcd' is 2 length.
        if you input length, the bytes value will be filled with '\x00' to the length you input.
        also will cut the str value to the length you input.
            If you want to write bytes value b'\x01\x02\x03\x04' to address 0,1, you can use:
                write(address=0, value=b'\x01\x02\x03\x04', datatype="bytes")
            If you want to write bytes value b'\x01\x02\x03\x04' to address 0,1, length=1, you can use:
                write(address=0, value=b'\x01\x02\x03\x04', length=1, datatype="bytes")
                But the value will be cut to b'\x01\x02'
            If you want to write bytes value b'\x01\x02\x03\x04' to address 0,1, length=3, you can use:
                write(address=0, value=b'\x01\x02\x03\x04', length=3, datatype="bytes")
                But the value will be filled with '\x00' to b'\x01\x02\x03\x04\x00\x00'
returns
    bytes
"""


def byte_to_bool(byte, return_bin=False, reverse=False):
    if isinstance(byte, int):
        byte = bytearray([byte])
    return_value = []
    for index in range(len(byte)):
        temp_value = [bool(byte[index] & (1 << i)) for i in range(8)]
        if return_bin:
            temp_value = [1 if value else 0 for value in temp_value]
        return_value += temp_value[::-1] if reverse else temp_value
    return return_value

def bytes_to_int8(byte_string, byteorder="big"):
    byte_pairs = [
        byte_string[i: i + 1] for i in range(0, len(byte_string), 1)
    ]
    int_value = [
        int.from_bytes(pair, byteorder=byteorder) for pair in byte_pairs  # pyright: ignore [reportArgumentType]
    ]
    return int_value

def bytes_to_int(byte_string, byteorder="big"):
    byte_pairs = [
        byte_string[i: i + 2] for i in range(0, len(byte_string), 2)
    ]
    int_value = [
        int.from_bytes(pair, byteorder=byteorder) for pair in byte_pairs  # pyright: ignore [reportArgumentType]
    ]
    return int_value


def bytes_to_int32(byte_string):
    byte_pairs = [
        byte_string[i + 2: i + 4] + byte_string[i: i + 2] for i in range(0, len(byte_string), 4)
    ]
    int32_value = []
    for byte_pair in byte_pairs:
        int32_value.append(struct.unpack(">i", byte_pair)[0])
    return int32_value


def bytes_to_float(byte_string):
    byte_pairs = [
        byte_string[i + 2: i + 4] + byte_string[i: i + 2] for i in range(0, len(byte_string), 4)
    ]
    float_value = []
    for byte_pair in byte_pairs:
        float_value.append(struct.unpack(">f", byte_pair)[0])
    return float_value


def bytes_to_bool(byte_string, reverse=False, byteorder="big", return_bin=False):
    byte_pairs = [
        byte_string[i: i + 2] for i in range(0, len(byte_string), 2)
    ]
    int_value = [
        int.from_bytes(pair, byteorder=byteorder) for pair in byte_pairs  # pyright: ignore [reportArgumentType]
    ]
    bool_value = []
    for i in range(len(int_value)):
        bin_value = bin(int_value[i])[2:].zfill(16)
        bin_value = bin_value[::-1] if not reverse else bin_value
        bin_int_value = [bool(int(value)) for value in bin_value] if not return_bin else [int(_bin) for _bin in
                                                                                          bin_value]
        bool_value.append(bin_int_value)
    return bool_value


def bytes_to_str_default(byte_string, reverse=False):
    if reverse:
        if len(byte_string) % 2 == 1:
            byte_string += b'\x00'
        byte_string = bytearray(byte_string)
        for i in range(0, len(byte_string), 2):
            byte_string[i], byte_string[i + 1] = byte_string[i + 1], byte_string[i]
    str_value = byte_string.decode("gbk", errors='ignore')
    return [str_value]


def bytes_to_str_unicode(byte_string, byteorder="little"):
    str_value = ''
    char_groups = [byte_string[i: i + 2] for i in range(0, len(byte_string), 2)]
    for char_group in char_groups:
        int_value = int.from_bytes(char_group[::-1], byteorder=byteorder)  # pyright: ignore [reportArgumentType]
        str_value += chr(int_value)
    return [str_value]


def bytes_to_str_low(byte_string):
    str_value = ''
    char_groups = [byte_string[i + 1] for i in range(0, len(byte_string), 2)]
    for char_group in char_groups:
        str_value += chr(char_group)
    return [str_value]


def bytes_to_str_high(byte_string):
    str_value = ''
    char_groups = [byte_string[i] for i in range(0, len(byte_string), 2)]
    for char_group in char_groups:
        str_value += chr(char_group)
    return [str_value]


def get_normal_char(char_groups):
    return_chars = ''
    for char in char_groups[0]:
        if 32 <= ord(char) <= 126:
            return_chars += char
    return [return_chars]

def int8_to_bytes(values, byteorder="big"):
    bytes_write_value = b''
    if not isinstance(values, list):
        values = [values]
    for value in values:
        value = int(value)
        if value > 255 or value < -127:
            raise Exception("The int value is out of range!")
        if value < 0:
            value += 255
        write_value = int(value)
        bytes_write_value += write_value.to_bytes(1, byteorder=byteorder)  # pyright: ignore [reportArgumentType]

    return bytes_write_value

def int_to_bytes(values, byteorder="big"):
    bytes_write_value = b''
    if not isinstance(values, list):
        values = [values]
    for value in values:
        value = int(value)
        if value > 65535 or value < -32768:
            raise Exception("The int value is out of range!")
        if value < 0:
            value += 65536
        write_value = int(value)
        bytes_write_value += write_value.to_bytes(2, byteorder=byteorder)  # pyright: ignore [reportArgumentType]

    return bytes_write_value


def int32_to_bytes(values, byteorder="big", reverse=False):
    bytes_write_value = b''
    if not isinstance(values, list):
        values = [values]
    for value in values:
        value = int(value)
        if value > 2147483647 or value < -2147483648:
            raise Exception("The int value is out of range!")
        if value < 0:
            value += 4294967296
        write_value = int(value)
        temp_write_value = write_value.to_bytes(4, byteorder=byteorder)  # pyright: ignore [reportArgumentType]
        bytes_write_value += temp_write_value if reverse else temp_write_value[2:] + temp_write_value[:2]

    return bytes_write_value


def float_to_bytes(values, reverse=False):
    bytes_write_value = b''
    if not isinstance(values, list):
        values = [values]
    for value in values:
        # if len(str(value)) > 8:
        #     raise Exception("The float value is out of range!")
        write_value = float(value)
        temp_bytes = struct.pack('>f', write_value)
        bytes_write_value += temp_bytes if reverse else temp_bytes[2:] + temp_bytes[:2]

    return bytes_write_value


def str_to_bytes_default(values, length=None, reverse=False):
    if length is None and not values:
        raise Exception("The str length and values can't be None at the same time!")
    values = str_get_ascii_char(values)
    bytes_write_value = values.encode('gbk')
    if length is not None:
        bytes_write_value = bytes_write_value[:length * 2].ljust(length * 2, b'\x00')
    if bytes_write_value is None:
        raise Exception(f'The str is None!')
    if len(bytes_write_value) % 2 == 1:
        bytes_write_value += b'\x00'
    if reverse:
        bytes_write_value = bytearray(bytes_write_value)
        for i in range(0, len(bytes_write_value), 2):
            bytes_write_value[i], bytes_write_value[i + 1] = bytes_write_value[i + 1], bytes_write_value[i]
        bytes_write_value = bytes(bytes_write_value)

    return bytes_write_value


def str_get_ascii_char(chars):
    ascii_chars = []
    non_sequence = []
    for index, char in enumerate(chars):
        if 32 <= ord(char) <= 126:
            ascii_chars.append(index)
    if len(ascii_chars) == 0:
        return chars
    if len(ascii_chars) == 1:
        return chars[:ascii_chars[0] + 1] + '\x00' + chars[ascii_chars[0] + 1:]
    for i in range(len(ascii_chars) - 1):
        if ascii_chars[i + 1] - ascii_chars[i] != 1:
            non_sequence.append(i)
    for j in range(len(non_sequence)):
        chars = chars[:non_sequence[j] + j + 1] + '\x00' + chars[non_sequence[j] + j + 1:]
    return chars


def str_to_bytes_unicode(values, length=None, byteorder="big"):
    if length is None and not values:
        raise Exception("The str length and values can't be None at the same time!")
    if length is not None:
        values = str(values)[:length].ljust(length, '\x00')
    else:
        values = str(values)
    int_values = [ord(char) for char in values]
    bytes_write_value = b''
    for temp_int in int_values:
        bytes_write_value += temp_int.to_bytes(2, byteorder=byteorder)  # pyright: ignore [reportArgumentType]
    return bytes_write_value


def str_to_bytes_low(values, length=None):
    if length is None and not values:
        raise Exception("The str length and values can't be None at the same time!")
    if not is_ascii_char(values):
        raise Exception("The high decode str value must be ascii char!")
    if length is not None:
        values = str(values)[:length].ljust(length, '\x00')
    else:
        values = str(values)
    int_values = [ord(char) for char in values]
    bytes_write_value = b''
    for temp_int in int_values:
        bytes_write_value += temp_int.to_bytes(2, byteorder="big")
    return bytes_write_value


def str_to_bytes_high(values, length=None):
    if length is None and not values:
        raise Exception("The str length and values can't be None at the same time!")
    if not is_ascii_char(values):
        raise Exception("The low decode str value must be ascii char!")
    if length is not None:
        values = str(values)[:length].ljust(length, '\x00')
    else:
        values = str(values)
    int_values = [ord(char) for char in values]
    bytes_write_value = b''
    for temp_int in int_values:
        bytes_write_value += temp_int.to_bytes(2, byteorder="little")
    return bytes_write_value


def is_ascii_char(chars):
    for char in chars:
        if ord(char) > 126 or ord(char) < 32:
            return False
    return True


def bool_to_bytes(values, reverse=False, byteorder="big"):
    bytes_write_value = b''

    if not isinstance(values, list):
        raise Exception("The bool value must be a list!")
    if max_bool_list_depth(values) > 2:
        raise Exception("The bool value depth must be equal to 1 or 2!")
    if max_bool_list_depth(values) == 2:
        for value in values:
            if len(value) != 16:
                raise Exception("The bool value length must be equal to 16!")
            value = value[::-1] if not reverse else value
            binary_string = ''.join(map(lambda x: '1' if x else '0', value))
            bytes_write_value += int(binary_string, 2).to_bytes(2, byteorder=byteorder)  # pyright: ignore
    else:
        values = values[::-1] if not reverse else values
        binary_string = ''.join(map(lambda x: '1' if x else '0', values))
        bytes_write_value += int(binary_string, 2).to_bytes(2,  byteorder=byteorder)  # pyright: ignore

    return bytes_write_value


def bool_to_byte(value, reverse=False):
    return_byte_value = b""
    if not isinstance(value, list):
        raise Exception("The bool value must be a list!")
    value = [int(item) for item in value]
    remainder = len(value) % 8
    if remainder != 0:
        value += [0 for _ in range(8 - remainder)]
    for times in range(len(value) // 8):
        binary_str = "".join(map(str, value[times * 8: (times + 1) * 8]))
        return_byte_value += int(binary_str if reverse else binary_str[::-1], 2).to_bytes(1)
    return return_byte_value


def is_subset(array1, array2):
    if isinstance(array1, list):
        return set(array1).issubset(set(array2))
    else:
        return array1 in array2


def max_bool_list_depth(bool_list):
    if not isinstance(bool_list, list):
        return 0
    if not bool_list:
        return 1
    nested_depths = [max_bool_list_depth(item) for item in bool_list]
    return 1 + max(nested_depths)


def bytes_to_bytes(values, length=None):
    if length is None and not values:
        raise Exception("The bytes length and values can't be None at the same time!")
    if length is not None:
        bytes_write_value = values[:length * 2].ljust(length * 2, b'\x00')
    else:
        bytes_write_value = values
    if len(bytes_write_value) % 2 == 1:
        bytes_write_value += b'\x00'
    if bytes_write_value is None:
        raise Exception(f'The bytes is None!')
    return bytes_write_value


def calculate_longer_than_max_length_read(address: int, length: int, max_length: int):
    if length > max_length:
        address_list = [address + i * max_length for i in range(length // max_length)]
        if length % max_length != 0:
            address_list.append(address + length // max_length * max_length)
        length_list = [max_length for _ in range(length // max_length)]
        if length % max_length != 0:
            length_list.append(length % max_length)
        return {address_list[i]: length_list[i] for i in range(len(address_list))}
    else:
        return {address: length}


def calculate_longer_than_max_length_write(address: int, length: int, max_length: int, value: bytes):
    if length > max_length:
        address_list = [address + i * max_length for i in range(length // max_length)]
        if length % max_length != 0:
            address_list.append(address + length // max_length * max_length)
        length_list = [max_length for _ in range(length // max_length)]
        if length % max_length != 0:
            length_list.append(length % max_length)
        value_list = [value[i * max_length * 2: (i + 1) * max_length * 2] for i in range(length // max_length)]
        if length % max_length != 0:
            value_list.append(value[length // max_length * max_length * 2:])
        return {address_list[i]: (length_list[i], value_list[i]) for i in range(len(address_list))}

    else:
        return {address: (length, value)}


def four_bytes_reverse(bytes_str):
    byte_pairs = [
        bytes_str[i + 2: i + 4] + bytes_str[i: i + 2] for i in range(0, len(bytes_str), 4)
    ]
    return b''.join(byte_pairs)


def two_bytes_reverse(bytes_str):
    byte_pairs = [
        bytes_str[i + 1: i + 2] + bytes_str[i: i + 1] for i in range(0, len(bytes_str), 2)
    ]
    return b''.join(byte_pairs)

def one_bytes_reverse(bytes_str):
    byte_pairs = [
        bytes_str[i : i + 1] + bytes_str[i: i + 1] for i in range(0, len(bytes_str), 1)
    ]
    return b''.join(byte_pairs)
def address_test_script(Comm):
    Comm.connect()
    max_length = Comm.MAX_CONSECUTIVE_READ_WRITE_LENGTH
    print('MAX_LENGTH:', max_length)

    t0 = time.time()
    times = 0
    while time.time() - t0 < 1:
        Comm.read(address=0, length=max_length, datatype="int")
        times += 1
    print('1s Read Max Length times: ', times)

    t0 = time.time()
    times = 0
    while time.time() - t0 < 1:
        Comm.write(address=0, length=max_length, datatype="str", value="")
        times += 1
    print('1s Write Max Length times: ', times)

    t0 = time.time()
    times = 0
    while time.time() - t0 < 1:
        Comm.read(address=0, length=max_length, datatype="int")
        Comm.write(address=0, length=max_length, datatype="str", value="")
        times += 1
    print('1s Read/Write Max Length times: ', times)

    test_int = [9534, 2]
    Comm.write(address=0, value=test_int, datatype="int")
    print('INT:', Comm.read(address=0, length=2, datatype="int"))

    test_int32 = [95342222, -21312313]
    Comm.write(address=2, value=test_int32, datatype="int32")
    print('INT32:', Comm.read(address=2, length=4, datatype="int32"))

    test_float = [-321.210, 232.670]
    Comm.write(address=6, value=test_float, datatype="float")
    print('FLOAT:', Comm.read(address=6, length=4, datatype="float"))

    test_str_default = "你C2"
    Comm.write(address=10, value=test_str_default, datatype="str")
    print('STR_DEFAULT:', Comm.read(address=10, length=2, datatype="str"))
    Comm.write(address=12, value=test_str_default, datatype="str", reverse=True)
    print('STR_DEFAULT_R:', Comm.read(address=12, length=2, datatype="str", reverse=True))
    Comm.write(address=14, value=test_str_default, datatype="str", normal=False)
    print('STR_DEFAULT_n:', Comm.read(address=14, length=2, datatype="str", normal=False))
    Comm.write(address=16, value=test_str_default, datatype="str", normal=False, reverse=True)
    print('STR_DEFAULT_R_n:', Comm.read(address=16, length=2, datatype="str", normal=False, reverse=True))

    test_str_unicode = "你C2X"
    Comm.write(address=18, value=test_str_unicode, datatype="str", decode="unicode")
    print('STR_UNICODE:', Comm.read(address=18, length=4, datatype="str", decode="unicode"))

    test_str_high_low = "A-C1"
    Comm.write(address=22, value=test_str_high_low, datatype="str", decode="high")
    print('STR_HIGH:', Comm.read(address=22, length=4, datatype="str", decode="high"))
    Comm.write(address=26, value=test_str_high_low, datatype="str", decode="low")
    print('STR_LOW:', Comm.read(address=26, length=4, datatype="str", decode="low"))

    test_bool = [[True, False, True, True, False, False, True, True,
                  True, True, False, False, False, False, True, False],
                 [True for i in range(8)] + [False for i in range(8)]]
    Comm.write(address=30, value=test_bool, datatype="bool", reverse=False)
    print('BOOL:', Comm.read(address=30, length=2, datatype="bool", reverse=False))
    Comm.write(address=32, value=test_bool, datatype="bool", reverse=True)
    print('BOOL_R:', Comm.read(address=32, length=2, datatype="bool", reverse=True))

    test_bytes = b'\x01\x02\x03\x04'
    Comm.write(address=34, value=test_bytes, datatype="bytes")
    print('BYTES:', Comm.read(address=34, length=2, datatype="bytes"))

    print('SUPPORT_DATATYPE:', Comm.support_datatype())
    Comm.disconnect()
