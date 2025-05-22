from fastapi import APIRouter, HTTPException
from threading import Thread, Event
import backend.api.v1.endpoints.communication as c
import time
import copy
from backend.database import db_instance
from backend.communication.fixed_communication import FixedCommunication
from backend.communication.base_communication import BaseCommunication
from backend.communication.flying_communication import FlyingCommunication
from backend.communication.flying_poller import PartProcessor
import asyncio
import ast
runRouter = APIRouter()
# Task management
task_thread = None
task_running = False
task_status_code = 0  # 0: Not started, 1: Running, 2: Paused, 3: Stopped
task_hand_paused = False
task_result_id = 0
pause_event = Event()
stop_event = Event()
lock = asyncio.Lock()  # 使用asyncio.Lock替代threading.Lock

def safe_list(value, default=None):
    try:
        result = ast.literal_eval(value) if isinstance(value, str) else value
        return result if isinstance(result, list) else (default or [])
    except Exception:
        return default or []
def background_task(c: BaseCommunication):
    communication_config = c.config.get("communication_config")
    print(communication_config)
    global task_running, task_status_code, task_result_id,task_hand_paused
    result=0
    c.run_server()
    while not stop_event.is_set():
        if not pause_event.is_set():
            if task_hand_paused:
                c.resume_server()
            print("Task is running...")
            #if result>=c.part_num or task_status_code ==3:  # After 30 seconds
            if result>=300:  # After 30 seconds
                print("Task is end...")
                from src.data.data_monitor import DataMonitor,create_benchmark_config
                data_monitor_config=create_benchmark_config(
                    base_benchmark_config={"id":c.start_time},
                    camera_resolution='5mp',
                    model_resolution='5mp',
                    share_memory_interval_time=30,
                    seq_interval_ms=235
                )
                bh = DataMonitor(data_monitor_config)
                bh.create_workbook()
                start_time=c.start_time+60
                bh.get_system_data(start_time=start_time)
                each_start_time = start_time
                benchmark_counter = result
                time_s = time.time() - each_start_time
                fps = benchmark_counter * 30 / time_s
                data=bh.create_report({
                    "total_part_count": benchmark_counter,
                    "total_use_time": time_s,
                    "fps": fps
                })
                cpu=data.get("CPU","i7-13000K")
                gpu=safe_list(data.get("GPU",["RTX-4070"]))
                ram=data.get("RAM","")
                ssd=safe_list(data.get("SSD",[]))
                print(isinstance(gpu, list),isinstance(ssd, list),isinstance(ram, list))
                soft_version=data.get("Software Version","4.9.6")
                ipc_config_data_dict={
                    "name": "us_enterprise",
                    "cpu": cpu,
                    "gpus": gpu,
                    "ram": ram,
                    "ssds": ssd,
                    "software_version": soft_version,
                }
                ipc_config = db_instance.query_data(
                    table_name="ipc_config", data_dict=ipc_config_data_dict
                ) 
                ipc_config_id=0
                if not ipc_config:
                    ipc_config_id = db_instance.add_data(
                        table_name="ipc_config", data_dict=ipc_config_data_dict
                    )
                    ipc_config_data_dict.update({"id": ipc_config_id})
                else:
                    ipc_config_id = ipc_config[0]["id"] if isinstance(ipc_config, list) else ipc_config.get("id")
                data_dict = {
                    # part information
                    "detection_dimension": data.get("detection_dimension",0),
                    "part_type": communication_config.get("part_type","test"),
                    "part_interval": 2.5,
                    "total_image_count": 30,
                    "total_inference_count": 40,
                    "ng_type_count": data.get("NG Type Number",0),
                    "each_ng_type_defect_count": data.get("Each NG Type Defect Number",0),
                    # ipc information
                    "ipc_count": 1,
                    "ipcs_config_id": [ipc_config_id],
                    # communication information
                    "communication_config_ids": [communication_config.get("id")],
                    "is_image_saving": str(data.get('is_image_saving')).lower() == 'true',
                    # ipc process result
                    "part_count": result,
                    "total_time_used": data.get("Total Use Time(s)",0),
                    "fps": data.get("FPS",0),
                    "mps": data.get("MP/s",0),
                    "max_part_use_time": data.get("Max Part Use Time (s)",0),
                    "min_part_use_time": data.get("Min Part Use Time (s)",0),
                    "avg_part_use_time": data.get("Avg Part Use Time (s)",0),

                    "max_image_capture_time": data.get("Max Image Capture Time",0),
                    "min_image_capture_time": data.get("Min Image Capture Time",0),
                    "avg_image_capture_time": data.get("Avg Image Capture Time",0),

                    "max_cortex_infer_time": data.get("Max Cortex Infer Time (ms)",0),
                    "min_cortex_infer_time": data.get("Min Cortex Infer Time (ms)",0),
                    "avg_cortex_infer_time": data.get("Avg Cortex Infer Time (ms)",0),
                    "ipc_performance_ids": [],
                    "core_allocation": data.get("Core Allocation",0),
                }
                new_data_id = db_instance.add_data(
                    table_name="simulation_result", data_dict=data_dict
                )
                print(f"Task completed, result inserted with ID: {new_data_id}")
                task_result_id = new_data_id
                test_ipc_config_data_dict = {
                    "ipc_config_id": ipc_config_id,
                    "simulation_result_id": new_data_id,
                    "model_size": "5MP",
                    "network_architecture": "V6",
                    "cpu_usage_avg": data.get("CPU Usage AVG (%)",0),
                    "gpus_usage_avg": [data.get("GPU Usage AVG (%)",0)],
                    "gpus_memory_usage_avg":[data.get("GPU Memory Usage AVG (%)",0)],
                    "memory_usage_avg": data.get("Memory Usage AVG (%)",0),
                    "disk_usage_avg": data.get("Disk Usage AVG (%)",0),
                    "disk_read_speed_avg": data.get("Disk Read Speed AVG (MB/s)",0),
                    "disk_write_speed_avg": data.get("Disk Write Speed AVG (MB/s)",0),
                    "workstations_in_use": [True, False, False, False, False, False],
                }
                db_instance.add_data(
                    table_name="ipc_performance", data_dict=test_ipc_config_data_dict
                )
                break  # Exit the loop after 30 seconds and task completion
            else:
                print("Task is running...")
                result=c.get_result()
                print(result)
                time.sleep(1)  # Simulate task running
        else:
            task_status_code = 2  # Task is paused
            c.pause_server()
            print("Task is paused...")
            time.sleep(1)
    c.stop_server()
    task_running = False
    task_hand_paused = False
    task_status_code = 3  # Task stopped
    print("Task stopped")


@runRouter.get("/run")
async def run_task():
    global task_thread, task_running, task_status_code

    async with lock:
        if task_running:
            return {
                "message": "Task is already running",
                "status_code": task_status_code,
            }

        # plc_client = PLCConfigClient()

        # try:
        #     # ✅ 连接PLC
        #     connected = await plc_client.connect()
        #     if not connected:
        #         return {
        #             "message": "无法连接到PLC",
        #             "status_code": task_status_code,
        #         }

        #     # ✅ 写入配置
        #     config_sent = await plc_client.write_config(c.global_communication_data)
        #     if not config_sent:
        #         await plc_client.disconnect()
        #         return {
        #             "message": "PLC配置发送失败",
        #             "status_code": task_status_code,
        #         }

        #     await plc_client.disconnect()

        # except Exception as e:
        #     return {
        #         "message": f"PLC操作失败: {str(e)}",
        #         "status_code": task_status_code,
        #     }
        config=copy.deepcopy(c.global_communication_data)
        # 创建通信实例
        if c.global_communication_data.get("communication_config", {}).get("communication_type") == 2:
            communication = FixedCommunication(config)
        elif c.global_communication_data.get("communication_config", {}).get("communication_type") == 1:
            communication = FlyingCommunication(config)
            part_run = PartProcessor()
            communication.set_part_processor(part_run)
        else:
            raise HTTPException(status_code=503, detail="请先应用通讯配置，再启动")

        # 启动通信
        if not await communication.start():
            raise HTTPException(status_code=503, detail="通信启动失败")


        # ✅ 启动任务线程
        stop_event.clear()
        pause_event.clear()

        task_thread = Thread(
            target=background_task,
            args=(communication,),
            daemon=True
        )
        task_thread.start()

        task_running = True
        task_status_code = 1  # 表示任务已启动

        return {"message": "Task started", "status_code": task_status_code}


@runRouter.get("/pause")
def pause_task():
    global task_running, task_status_code,task_hand_paused
    if not task_running:
        return {"message": "No task is running", "status_code": task_status_code}

    pause_event.set()  # Pause the task
    task_status_code = 2  # Task is paused
    task_hand_paused = True
    return {"message": "Task paused", "status_code": task_status_code}


@runRouter.get("/resume")
def resume_task():
    global task_running, task_status_code
    if not task_running:
        return {"message": "No task is running", "status_code": task_status_code}

    pause_event.clear()  # Resume the task
    task_status_code = 1  # Task is running
    return {"message": "Task resumed", "status_code": task_status_code}


@runRouter.get("/stop")
def stop_task():
    global task_running, task_status_code
    if not task_running:
        return {"message": "No task is running", "status_code": task_status_code}

    stop_event.set()  # Stop the task
    task_thread.join()  # Wait for the thread to finish
    task_running = False
    task_status_code = 3  # Task stopped
    return {"message": "Task stopped", "status_code": task_status_code}


@runRouter.get("/status")
def get_task_status():
    return {"status_code": task_status_code}


@runRouter.get("/result")
def get_task_result():
    data = None
    if task_result_id > 0:
        data_dict = {"id": task_result_id}
        dbData = db_instance.query_data(
            table_name="simulation_result", data_dict=data_dict
        )
        if dbData:
            data = dbData[0]
    return {"data": data}

