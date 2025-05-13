from fastapi import APIRouter, HTTPException
from threading import Thread, Event
import backend.api.v1.endpoints.communication as c
import time
from backend.database import db_instance
from backend.communication.fixed_communication import FixedCommunication
from backend.communication.base_communication import BaseCommunication
from backend.communication.flying_communication import FlyingCommunication
from backend.communication.flying_poller import PartProcessor
import asyncio
import random
runRouter = APIRouter()
# Task management
task_thread = None
task_running = False
task_status_code = 0  # 0: Not started, 1: Running, 2: Paused, 3: Stopped
task_result_id = 0
pause_event = Event()
stop_event = Event()
lock = asyncio.Lock()  # 使用asyncio.Lock替代threading.Lock


def background_task(c: BaseCommunication):
    communication_config = c.config.get("communication_config")
    print(communication_config)
    global task_running, task_status_code, task_result_id
    start_time = time.time()
    c.run_server()
    while not stop_event.is_set():
        if not pause_event.is_set():
            print("Task is running...")
            time.sleep(1)  # Simulate task running
            elapsed_time = time.time() - start_time
            if elapsed_time >= 30:  # After 30 seconds
                print("Task is end...")
                min_time = round(random.uniform(0.9, 1.0), 15)
                max_time = round(random.uniform(1.0, 1.1), 15)
                avg_time = round((min_time + max_time) / 2 + random.uniform(-0.01, 0.01), 15)

                fps = round(random.uniform(29.0, 31.0), 13)
                mps = round(random.uniform(29.0, 31.0), 13)
                total_time = round(random.uniform(290.0, 310.0), 15)
                min_image_capture_time = round(random.uniform(0.9, 1.0), 15)
                max_image_capture_time = round(random.uniform(1.0, 1.1), 15)
                avg_image_capture_time = round((min_time + max_time) / 2 + random.uniform(-0.01, 0.01), 15)
                min_cortex_infer_time = round(random.uniform(0.9, 1.0), 15)
                max_cortex_infer_time = round(random.uniform(1.0, 1.1), 15)
                avg_cortex_infer_time = round((min_time + max_time) / 2 + random.uniform(-0.01, 0.01), 15)
                test_data_dict = {
                    # part information
                    "detection_dimension": 0,
                    "part_type": "test",
                    "part_interval": 2.5,
                    "total_image_count": 30,
                    "total_inference_count": 40,
                    "ng_type_count": 10,
                    "each_ng_type_defect_count": 5,
                    # ipc information
                    "ipc_count": 1,
                    "ipcs_config_id": ["9"],
                    # communication information
                    "communication_config_ids": [communication_config.get("id")],
                    "is_image_saving": False,
                    # ipc process result
                    "part_count": 302,
                    "total_time_used": total_time,
                    "fps": fps,
                    "mps": mps,
                    "max_part_use_time": max_time,
                    "min_part_use_time": min_time,
                    "avg_part_use_time": avg_time,
                    "max_image_capture_time": max_image_capture_time,
                    "min_image_capture_time": min_image_capture_time,
                    "avg_image_capture_time": avg_image_capture_time,
                    "max_cortex_infer_time": max_cortex_infer_time,
                    "min_cortex_infer_time": min_cortex_infer_time,
                    "avg_cortex_infer_time": avg_cortex_infer_time,
                    "ipc_performance_ids": [],
                    "core_allocation": "prod service: 0, 1, 2, 3, 4, 5, 6, 7\nprod ui: 16, 17, 18, 19"
                    "\ncortex: 8, 9, 10, 11, 12, 13, 14\noptix: 20, 21, 22, 23",
                }
                new_data_id = db_instance.add_data(
                    table_name="simulation_result", data_dict=test_data_dict
                )
                print(f"Task completed, result inserted with ID: {new_data_id}")
                task_result_id = new_data_id
                test_ipc_config_data_dict = {
                    "ipc_config_id": 4,
                    "simulation_result_id": new_data_id,
                    "model_size": "5MP",
                    "network_architecture": "V4",
                    "cpu_usage_avg": 20.2283806343907,
                    "gpus_usage_avg": [25.7846410684474],
                    "gpus_memory_usage_avg": [19.4115372089236],
                    "memory_usage_avg": 12.4136894824707,
                    "disk_usage_avg": 28.0843071786311,
                    "disk_read_speed_avg": 0.000312082075415486,
                    "disk_write_speed_avg": 145.954015496326,
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
            print("Task is paused...")
            time.sleep(1)
    c.stop_server()
    task_running = False
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



        # communication_config = c.global_communication_data.get("communication_config", {})
        # workstation_in_use = communication_config.get("workstations_in_use", [False, False, False, False, False, False])
        # workstation_config_ids = communication_config.get("workstation_config_ids", [])
        # workstation_use_request = []
        # workstation_use_ids = []
            
        # for i in range(6):
        #     if workstation_in_use[i]:
        #         workstation_use_request.append(1)
        #         workstation_use_ids.append(workstation_config_ids[i])
        #     else:
        #         workstation_use_request.append(0)
                    
        # workstation_configs = c.global_communication_data.get("workstation_configs", [])
        # workstation_use_configs = []
        # for workstation_config in workstation_configs:
        #     wc = workstation_config.get("workstation_config", {})
        #     if wc.get("id", 0) in workstation_use_ids:
        #         workstation_use_configs.append(workstation_config)

        # communication_type = communication_config.get("communication_type", 0)
        # communication_step = communication_config.get("communication_step", 0)
        # communication_type_request = [communication_type, communication_step]

        # part_type = communication_config.get("part_type", "物料")
        # part_interval = int(communication_config.get("part_interval", 0))
        # part_start_to_ws1_interval = int(communication_config.get("part_start_to_ws1_interval", 0))
        # print(f"📝_write_workstation_use: {workstation_use_request}")
        # print(f"_write_communication: {communication_type_request}")
        # print(f"_write_part_start:{part_type} {part_interval}")
        # ws_next_interval=[part_start_to_ws1_interval]
        # camera_reset_time=[]
        # ws_seq_count=[]

        # for workstation_config_data in workstation_use_configs:
        #     workstation_config = workstation_config_data.get("workstation_config", {})
        #     ws_next_interval.append(int(workstation_config.get("to_next_ws_offset", 0)))
        #     camera_reset_time.append(int(workstation_config.get("camera_reset_time", 0)))
        #     ws_seq_count.append(workstation_config.get("sequence_count", 0))
        #     print(workstation_config)
        #     sequences_ids = workstation_config.get("sequences_id", [])
        #     print(sequences_ids)
        #         # 如果sequences_ids长度小于10，补0到10个元素
        #     if len(sequences_ids) < 10:
        #         sequences_ids.extend([0] * (10 - len(sequences_ids)))
        #     sequences_intervals = workstation_config.get("sequences_interval", [])
        #     print(sequences_intervals)
        #         # 如果sequences_intervals长度小于10，补0到10个元素
        #     if len(sequences_intervals) < 10:
        #         sequences_intervals.extend([0] * (10 - len(sequences_intervals)))

        #     print(f"data {sequences_ids}")
        #     print(f"data {sequences_intervals}")
        # print(ws_next_interval)
        # print(camera_reset_time)
        # print(ws_seq_count)
        # 创建通信实例
        if c.global_communication_data.get("communication_config", {}).get("communication_type") == 0:
            communication = FixedCommunication(c.global_communication_data)
        else:
            communication = FlyingCommunication(c.global_communication_data)
            part_run = PartProcessor()
            communication.set_part_processor(part_run)

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
    global task_running, task_status_code
    if not task_running:
        return {"message": "No task is running", "status_code": task_status_code}

    pause_event.set()  # Pause the task
    task_status_code = 2  # Task is paused
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

