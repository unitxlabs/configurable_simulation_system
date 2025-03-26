from fastapi import APIRouter
from threading import Thread, Event, Lock
import backend.api.v1.endpoints.communication as c
import time

runRouter = APIRouter()
# Task management
task_thread = None
task_running = False
task_status_code = 0  # 0: Not started, 1: Running, 2: Paused, 3: Stopped
pause_event = Event()
stop_event = Event()
lock = Lock()  # Ensure thread safety


def background_task():
    global task_running, task_status_code
    while not stop_event.is_set():
        if not pause_event.is_set():
            task_status_code = 1  # Task is running
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
        task_thread = Thread(target=background_task, daemon=True)
        task_thread.start()
        task_running = True
        task_status_code = 1  # Task is running
    print(c.global_communication_data)
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
