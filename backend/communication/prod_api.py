import socket
import time
import uuid
import json
import sys
import enum
sys.path.append('/home/unitx/unitx_data/config')
import logging
from flying_communication import  PROD_PORT
class ProdStatus(enum.Enum):
    PROD_STATUS_NOT_READY = 0
    PROD_STATUS_OK = 1
    PROD_STATUS_NOT_OK = 2
logger = logging.getLogger("prod_api")


def milliseconds():
    return round(time.time() * 1000)


class ProdApiClient(object):
    @staticmethod
    def _send_to_prod(message:str):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('', PROD_PORT))
            sock.sendall(message)
            logger.info(f'sent {message}')

            response = b''
            while not response.endswith(b'\n'):
                response += sock.recv(1024)
            response = response.strip()
            received = str(response, "utf-8")
            logger.info(f'received {received}')

    @staticmethod
    def reset_part():
        ProdApiClient._send_to_prod(b'run/part/reset\n')

    @staticmethod
    def end_part(part_type:str, part_id:str):
        ProdApiClient._send_to_prod(str.encode(f'run/part/end/{part_type}/{part_id}\n'))
    
    @staticmethod
    def start_part(part_type:str, part_id:str=None, timestamp:int=None):
        if timestamp is None:
            timestamp = milliseconds()

        if part_id is None or part_id == '':
            part_id = uuid.uuid4()

        ProdApiClient._send_to_prod(str.encode(f'run/part/start/{part_type}/{part_id}/?ts={timestamp}\n'))

    @staticmethod
    def reset_camera(camera_id: str, part_id: str):
        ProdApiClient._send_to_prod(str.encode(f'run/camera/reset/{camera_id}/{part_id}\n'))

    @staticmethod
    def camera_sequence_select(camera_id: str, sequence_id: int=0):
        ProdApiClient._send_to_prod(str.encode(f'run/camera/sequence_select/{camera_id}/{sequence_id}\n'))

    @staticmethod
    def camera_trigger(camera_id: str):
        ProdApiClient._send_to_prod(str.encode(f'run/camera/trigger/{camera_id}\n'))

    @staticmethod
    def update_part_id(part_type, part_id: str, new_part_id: str):
        # ProdApiClient._send_to_prod(str.encode(f'run/part/replace_part_id/{part_type}/{part_id}/{new_part_id}\n'))
        ProdApiClient._send_to_prod(str.encode(f'run/part/update_part_id/{part_type}/{part_id}/{new_part_id}\n'))

    @staticmethod
    def get_prod_system_status():
        try:
            message = b'system/status\n'
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(('', PROD_PORT))
                sock.sendall(message)
                logger.info(f'sent {message}')

                response = b''
                while not response.endswith(b'\n'):
                    response += sock.recv(1024)
                response = response.strip()
                received = str(response, "utf-8").strip()
                logger.debug(f"ProdApiClient prod received {received}")
                dict_received = json.loads(received)
                logger.debug(f"ProdApiClient prod status {dict_received}")
                prod_status = int(dict_received["message"])
                return prod_status
        except ConnectionRefusedError:
            return ProdStatus.PROD_STATUS_NOT_OK.value
        except json.decoder.JSONDecodeError:
            return ProdStatus.PROD_STATUS_NOT_OK.value
        except ValueError:
            return ProdStatus.PROD_STATUS_NOT_OK.value
        except KeyError:
            return ProdStatus.PROD_STATUS_NOT_OK.value

    @staticmethod
    def send_human_result(result):
        ProdApiClient._send_to_prod(str.encode(f'run/part/human_classification/{result}\n'))
