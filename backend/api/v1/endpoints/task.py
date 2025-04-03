from fastapi import APIRouter
from threading import Thread, Event, Lock
import backend.api.v1.endpoints.communication as c
import time
from backend.database import db_instance

runRouter = APIRouter()
# Task management
task_thread = None
task_running = False
task_status_code = 0  # 0: Not started, 1: Running, 2: Paused, 3: Stopped
task_result_id = 0
pause_event = Event()
stop_event = Event()
lock = Lock()  # Ensure thread safety


def background_task(c: any):
    communication_config = c.get("communication_config")
    print(communication_config)
    global task_running, task_status_code, task_result_id
    start_time = time.time()
    while not stop_event.is_set():
        if not pause_event.is_set():
            print("Task is running...")
            time.sleep(1)  # Simulate task running
            elapsed_time = time.time() - start_time
            if elapsed_time >= 30:  # After 30 seconds
                print("Task is end...")
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
                    "total_time_used": 300.422652244568,
                    "fps": 30.1575128649901,
                    "mps": 30.1575128649901,
                    "max_part_use_time": 1.09100008010864,
                    "min_part_use_time": 0.924000024795532,
                    "avg_part_use_time": 0.957632112662529,
                    "max_image_capture_time": 1.09100008010864,
                    "min_image_capture_time": 0.924000024795532,
                    "avg_image_capture_time": 0.957632112662529,
                    "max_cortex_infer_time": 1.09100008010864,
                    "min_cortex_infer_time": 0.924000024795532,
                    "avg_cortex_infer_time": 0.957632112662529,
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
                time.sleep(1)  # Simulate task running
        else:
            task_status_code = 2  # Task is paused
            print("Task is paused...")
            time.sleep(1)

    task_running = False
    task_status_code = 3  # Task stopped
    print("Task stopped")


@runRouter.get("/run")
def run_task():
    global task_thread, task_running, task_status_code
    with lock:
        if task_running:
            return {
                "message": "Task is already running",
                "status_code": task_status_code,
            }

        stop_event.clear()
        pause_event.clear()  # Default to running state
        task_thread = Thread(
            target=background_task, args=(c.global_communication_data,), daemon=True
        )
        task_thread.start()
        task_running = True
        task_status_code = 1  # Task is running
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


def transform_data(data):
    # 获取workstation_config_ids和workstations_in_use
    c_name = data["communication_config"]["name"]
    workstations_in_use = data["communication_config"]["workstations_in_use"]
    workstation_configs = data["workstation_configs"]

    # 生成转换后的数据
    result = []
    address = 7526  # 初始化地址
    for i, ws_config in enumerate(workstation_configs):
        if workstations_in_use[i]:
            workstation_id = ws_config["workstation_config"]["workstation_id"]
            controller_config = ws_config["controller_config"]

            # 生成name字段
            name = f"{c_name}_{workstation_id}"

            # 生成camera字段
            camera = []
            for camera_id in controller_config["cameras_id"]:
                controller_port_id = controller_config["controller_id"]
                camera.append(
                    {"camera_id": camera_id, "controller_port_id": controller_port_id}
                )
            current_address = address
            address += 2  # signal的address使用current_address，然后address加2
            part_id_address = address
            address += 2  # part_id的address

            # 生成station_done字段
            station_done = {
                "signal": {
                    "request": {
                        "address": str(current_address),  # 使用当前的地址
                        "length": "1",
                        "default_signal": [0, 1, 2],
                    }
                },
                "part_id": {
                    "request": {"address": str(part_id_address), "length": "1"}
                },
            }

            result.append(
                {"name": name, "camera": camera, "station_done": station_done}
            )

    return result


@runRouter.get("/info")
def run_task_info():
    print(c.global_communication_data)
    data = transform_data(c.global_communication_data)
    return {"message": "Task started", "data": data}
