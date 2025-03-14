from fastapi import APIRouter, Depends, HTTPException
from backend.api.v1.schemas import SystemInfoResponse, CommonResponse
import subprocess
from backend.logger import Logger

systemInfoRouter = APIRouter()


# 获取系统版本信息
def get_system_version():
    result = subprocess.run(["cat", "/etc/os-release"], capture_output=True, text=True)

    # 查找包含 PRETTY_NAME 的行并提取版本信息
    for line in result.stdout.splitlines():
        if "PRETTY_NAME" in line:
            version = line.split("=")[1].strip('"\n')
            return version


# 获取CPU信息（简化输出）
def get_cpu_info():
    result = subprocess.run(["cat", "/proc/cpuinfo"], stdout=subprocess.PIPE, text=True)
    for line in result.stdout.splitlines():
        if "model name" in line:
            return line.split(": ")[1]


# 获取GPU信息（适用于NVIDIA GPU，需安装nvidia-smi工具）
def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "没有检测到NVIDIA GPU"
    except FileNotFoundError:
        return "未安装nvidia-smi工具，无法获取GPU信息"


# 获取内存信息
def get_memory_info():
    # 执行 dmidecode 命令获取内存信息
    password = "your_password_here"

    # 使用 echo 和管道传递密码给 sudo
    result = subprocess.run(
        f"echo {password} | sudo -S dmidecode -t memory",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    memory_info = []

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return " ".join(memory_info)

    # 处理命令输出并提取 Type 和 Speed
    lines = result.stdout.splitlines()

    type_value = None
    speed_value = None

    for line in lines:
        line = line.strip()

        # 提取 Type 和 Speed
        if line.startswith("Type:"):
            type_value = line
        elif line.startswith("Speed:"):
            speed_value = line

        # 当遇到一个内存条的完整信息时，进行过滤
        if type_value and speed_value:
            # 过滤掉包含 'Unknown' 或 'None' 的行
            if (
                "Unknown" not in type_value
                and "None" not in type_value
                and "Unknown" not in speed_value
            ):
                memory_info.append(f"{type_value}, {speed_value}")

            # 重置 type_value 和 speed_value，准备处理下一条内存条
            type_value = None
            speed_value = None

    return " ".join(memory_info)


# 获取磁盘信息
def get_disk_info():
    result = subprocess.run(
        ["lsblk", "-d", "-o", "name,model"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode == 0:
        # 解析命令输出
        output = result.stdout.decode("utf-8").strip().split("\n")
        # 跳过标题行，遍历每一行，找到磁盘型号
        for line in output[1:]:
            columns = line.split()
            if len(columns) > 1:  # 确保至少有两列
                return " ".join(columns[1:])  # 返回磁盘型号
    else:
        print(f"Error: {result.stderr.decode('utf-8')}")
        return None  # 如果发生错误，返回 None


@systemInfoRouter.get("/info", response_model=CommonResponse)
def get_system_info():
    system_version = get_system_version()
    cpu_info = get_cpu_info()
    gpu_info = get_gpu_info()
    memory_info = get_memory_info()
    disk_info = get_disk_info()
    system_info_model = SystemInfoResponse(
        name=system_version,
        cpu=cpu_info,
        ram=memory_info,
        ssds=disk_info,
        gpu=gpu_info,  # 将最终的gpu信息传递给模型
    )
    return CommonResponse(msg="", data=[system_info_model.dict()])


@systemInfoRouter.get("/log", response_model=CommonResponse)
def get_system_log():
    logs = Logger.get_last_logs(20)
    return CommonResponse(msg="", data=logs)
