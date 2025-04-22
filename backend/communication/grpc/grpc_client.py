import grpc

from backend.communication.grpc.proto import upper_service_pb2_grpc

#HOST = '127.0.0.1'
HOST = '192.168.0.190'
PORT = 50051


# gRPC框架已经实现了自动重连，所以不需要自己实现重连逻辑
class GrpcClient:
    _instance = None  # 存储单例

    def __init__(self, host, port):
        # 构造器私有化，确保不能在其他模块中直接实例化
        if GrpcClient._instance is not None:
            raise Exception("GrpcClient is a singleton. Use get_instance() to get an instance.")
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = upper_service_pb2_grpc.UpperServiceStub(self.channel)

    @classmethod
    def get_instance(cls):
        # 如果还没有实例，则创建一个
        if cls._instance is None:
            cls._instance = cls(HOST, PORT)  # 在模块级别创建GrpcClient的单例
        return cls._instance


_grpc_client_singleton = GrpcClient.get_instance()
grpc_client = _grpc_client_singleton.stub

# 防止其他模块直接访问GrpcClient类
__all__ = ['grpc_client']