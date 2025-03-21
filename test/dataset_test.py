# coding: utf-8
# author: Wang Junfeng
import time

from src.database.base import SimulationResult, ConfigurableSimulationSystemDB


def ipc_config_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "name": "us_enterprise",
        "cpu": "13-i8",
        "gpus": ["4080", "4080"],
        "ram": "test_ram",
        "ssds": ["test_ssd1", "test_ssd2"],
        "software_version": "4.7",
    }
    new_data_id = database_test.add_data(table_name="ipc_config", data_dict=test_data_dict)
    return new_data_id


def ipc_config_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "name": "us_enterprise",
        "cpu": "13-i9",
        "gpus": ["4080", "4080"],
        "ram": "test_ram",
        "ssds": ["test_ssd1", "test_ssd2"],
        "software_version": "4.7",
    }
    database_test.update_data(table_name="ipc_config", data_dict=test_data_dict)


def ipc_config_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    query_data_dict = {
        "id": data_id,
        "name": "us_enterprise",
        "cpu": "13-i9",
        "gpus": ["4080", "4080"],
        "ram": "test_ram",
        "ssds": ["test_ssd1", "test_ssd2"],
        "software_version": "4.7",
    }
    query_data = database_test.query_data(table_name="ipc_config", data_dict=query_data_dict)
    print(query_data)


def ipc_config_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="ipc_config", data_id=delete_data_id)


def controller_config_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "controller_id": "312513545",
        "controller_version": "V6",
        "cameras_id": ["15324551"],
        "cameras_type": ["OACH0060UC"],
        "image_width": 4096,
        "image_height": 3000,
        "capture_images_count": 30,
        "network_inference_count": 40,
    }
    new_data_id = database_test.add_data(table_name="controller_config", data_dict=test_data_dict)
    return new_data_id


def controller_config_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "controller_id": "312513545",
        "controller_version": "V6",
        "cameras_id": ["15324552"],
        "cameras_type": ["OACH0060UC", "OACH0080UC"],
        "image_width": 4096,
        "image_height": 3000,
        "capture_images_count": 30,
        "network_inference_count": 40,
    }
    database_test.update_data(table_name="controller_config", data_dict=test_data_dict)


def controller_config_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "controller_id": "312513545",
        "controller_version": "V6",
        "cameras_id": ["15324552"],
        "cameras_type": ["OACH0060UC"],
        "image_width": 4096,
        "image_height": 3000,
        "capture_images_count": 30,
        "network_inference_count": 40,
    }
    query_data = database_test.query_data(table_name="controller_config", data_dict=test_data_dict)
    print(query_data)


def controller_config_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="controller_config", data_id=delete_data_id)


def workstation_config_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "workstation_id": 1,
        "controller_config_id": 2,
        "to_next_ws_offset": 2.1,
        "camera_reset_time": 1.7,
        "sequence_count": 3,
        "sequences_id": [0, 1, 2],
        "sequences_interval": [10, 10, 10],
    }
    new_data_id = database_test.add_data(table_name="workstation_config", data_dict=test_data_dict)
    return new_data_id


def workstation_config_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "workstation_id": 1,
        "controller_config_id": 2,
        "to_next_ws_offset": 2.2,
        "camera_reset_time": 1.7,
        "sequence_count": 4,
        "sequences_id": [0, 1, 2, 3],
        "sequences_interval": [10, 10, 10, 10],
    }
    database_test.update_data(table_name="workstation_config", data_dict=test_data_dict)


def workstation_config_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "workstation_id": 1,
        "controller_config_id": 2,
        "to_next_ws_offset": 2.2,
        "camera_reset_time": 1.7,
        "sequence_count": 4,
        "sequences_id": [0, 1, 2, 3],
        "sequences_interval": [10, 10, 10, 10],

        "controller_version": "V6",
        "cameras_type": ["OACH0060UC"],
    }
    query_data = database_test.query_data(table_name="workstation_config", data_dict=test_data_dict)
    print(query_data)


def workstation_config_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="workstation_config", data_id=delete_data_id)


def communication_config_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "name": "test",
        "part_type": "test",
        "part_interval": 2.8,
        "part_start_to_ws1_interval": 1.5,
        "communication_type": 0,
        "communication_step": 2,
        "workstation_count": 1,
        "workstation_config_ids": [1],
        "workstations_in_use": [True, False, False, False, False, False],
    }
    new_data_id = database_test.add_data(table_name="communication_config", data_dict=test_data_dict)
    return new_data_id


def communication_config_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "name": "test",
        "part_type": "test",
        "part_interval": 2.9,
        "part_start_to_ws1_interval": 1.5,
        "communication_type": 0,
        "communication_step": 1,
        "workstation_count": 1,
        "workstation_config_ids": [1],
        "workstations_in_use": [True, False, False, False, False, False],
    }
    database_test.update_data(table_name="communication_config", data_dict=test_data_dict)


def communication_config_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "name": "test",
        "part_type": "test",
        "part_interval": 2.8,
        "part_start_to_ws1_interval": 1.5,
        "communication_type": 0,
        "communication_step": 2,
        "workstation_count": 1,
        "workstation_config_ids": [1],
        "workstations_in_use": [True, False, False, False, False, False],

        "controller_version": "V6",
        "cameras_type": ["OACH0060UC"],
    }
    query_data = database_test.query_data(table_name="communication_config", data_dict=test_data_dict)
    print(query_data)


def communication_config_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="communication_config", data_id=delete_data_id)


def ipc_performance_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "ipc_config_id": 1,
        "simulation_result_id": 1,
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
    new_data_id = database_test.add_data(table_name="ipc_performance", data_dict=test_data_dict)
    return new_data_id


def ipc_performance_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        "id": data_id,
        "ipc_config_id": 1,
        "simulation_result_id": 1,
        "model_size": "5MP",
        "network_architecture": "V5",
        "cpu_usage_avg": 20.2283806343907,
        "gpus_usage_avg": [25.7846410684474],
        "gpus_memory_usage_avg": [19.4115372089236],
        "memory_usage_avg": 12.4136894824707,
        "disk_usage_avg": 28.0843071786311,

        "disk_read_speed_avg": 0.000312082075415486,
        "disk_write_speed_avg": 145.954015496326,
        "workstations_in_use": [True, False, False, False, False, False],
    }
    database_test.update_data(table_name="ipc_performance", data_dict=test_data_dict)


def ipc_performance_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        # "id": data_id,
        # "ipc_config_id": 1,
        # "simulation_result_id": 1,
        "model_size": "5",
        "network_architecture": "V",
        "cpu_usage_avg": 20.2283806343907,
        "gpus_usage_avg": [25.7846410684474],
        "gpus_memory_usage_avg": [19.4115372089236],
        "memory_usage_avg": 12.4136894824707,
        "disk_usage_avg": 28.0843071786311,

        "disk_read_speed_avg": 0.000312082075415486,
        "disk_write_speed_avg": 145.954015496326,
        "workstations_in_use": [True, False, False, False, False, False],
    }
    query_data = database_test.query_data(table_name="ipc_performance", data_dict=test_data_dict)
    print(query_data)


def ipc_performance_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="ipc_performance", data_id=delete_data_id)


def simulation_result_add_data_test():
    database_test = ConfigurableSimulationSystemDB()
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
        "ipcs_config_id": ["1"],
        # communication information
        "communication_config_ids": [1],
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
                           "\ncortex: 8, 9, 10, 11, 12, 13, 14\noptix: 20, 21, 22, 23"

    }
    new_data_id = database_test.add_data(table_name="simulation_result", data_dict=test_data_dict)
    return new_data_id


def simulation_result_update_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        # part information
        "id": data_id,
        "detection_dimension": 0,
        "part_type": "test",
        "part_interval": 2.9,
        "total_image_count": 30,
        "total_inference_count": 40,
        "ng_type_count": 10,
        "each_ng_type_defect_count": 5,
        # ipc information
        "ipc_count": 1,
        "ipcs_config_id": ["1"],
        # communication information
        "communication_config_ids": [1],
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

        "ipc_performance_ids": [4],
        "core_allocation": "prod service: 0, 1, 2, 3, 4, 5, 6, 7\nprod ui: 16, 17, 18, 19"
                           "\ncortex: 8, 9, 10, 11, 12, 13, 14\noptix: 20, 21, 22, 23"

    }
    database_test.update_data(table_name="simulation_result", data_dict=test_data_dict)


def simulation_result_query_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    test_data_dict = {
        # part information
        "id": data_id,
        "detection_dimension": 0,
        "part_type": "test",
        "part_interval": 2.9,
        "total_image_count": 30,
        "total_inference_count": 40,
        "ng_type_count": 10,
        "each_ng_type_defect_count": 5,
        # ipc information
        "ipc_count": 1,
        "ipcs_config_id": ["1"],
        # communication information
        "communication_config_ids": [1],
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

        "ipc_performance_ids": [4],
        "core_allocation": "prod service: 0, 1, 2, 3, 4, 5, 6, 7\nprod ui: 16, 17, 18, 19"
                           "\ncortex: 8, 9, 10, 11, 12, 13, 14\noptix: 20, 21, 22, 23"

    }
    query_data = database_test.query_data(table_name="simulation_result", data_dict=test_data_dict)

    print(query_data)


def simulation_result_delete_data_test(data_id=None):
    database_test = ConfigurableSimulationSystemDB()
    delete_data_id = data_id
    database_test.delete_data(table_name="simulation_result", data_id=delete_data_id)


def simulation_result_query_test():
    database_test = ConfigurableSimulationSystemDB()
    simulation_result = database_test.session.get(SimulationResult, 1)
    if simulation_result:
        if simulation_result.ipc_performance_ids is None:
            simulation_result.ipc_performance_ids = []
        # simulation_result.ipc_performance_ids.append(1)
        updated_list = simulation_result.ipc_performance_ids + [1]
        simulation_result.ipc_performance_ids = updated_list  # 显式赋值

        # database_test.session.add(simulation_result)
        database_test.session.commit()


def used_controller_id_test():
    database_test = ConfigurableSimulationSystemDB()
    used_controller_ids = database_test.get_used_controller_ids()
    print(f"used_controller_ids: {used_controller_ids}")
    controller_id = 1
    is_controller_id_used = database_test.is_controller_used(controller_id)
    print(f"is controller id {controller_id} used {is_controller_id_used}")
    controller_usage = database_test.get_controller_usage()
    print(f"controller_usage: {controller_usage}")

    all_controller_ids = database_test.get_all_controller_ids()
    print(f"all_controller_ids: {all_controller_ids}")


def used_cpu_gpus_test():
    database_test = ConfigurableSimulationSystemDB()
    used_cpus = database_test.get_used_cpu()
    print(f"used_cpus: {used_cpus}")

    used_gpus = database_test.get_used_gpus()
    print(f"used_cpus: {used_gpus}")


if __name__ == "__main__":
    # new_ipc_config_id = ipc_config_add_data_test()
    # print(f"new_ipc_config_id: {new_ipc_config_id}")
    # new_ipc_config_id = 14
    # ipc_config_update_data_test(new_ipc_config_id)
    # ipc_config_query_data_test(new_ipc_config_id)
    # ipc_config_delete_data_test(new_ipc_config_id)

    # new_controller_config_id = controller_config_add_data_test()
    # print(f"new_controller_config_id: {new_controller_config_id}")
    # new_controller_config_id = 2
    # controller_config_update_data_test(new_controller_config_id)
    # controller_config_query_data_test(new_controller_config_id)
    # controller_config_delete_data_test(new_controller_config_id)

    # new_workstation_config_id = workstation_config_add_data_test()
    # print(f"new_workstation_config_id: {new_workstation_config_id}")
    # new_workstation_config_id = 1
    # workstation_config_update_data_test(new_workstation_config_id)
    # workstation_config_query_data_test(new_workstation_config_id)
    # workstation_config_delete_data_test(new_workstation_config_id)

    # new_communication_config_id = communication_config_add_data_test()
    # print(f"new_communication_config_id: {new_communication_config_id}")
    new_communication_config_id = 1
    # communication_config_update_data_test(new_communication_config_id)
    communication_config_query_data_test(new_communication_config_id)
    # communication_config_delete_data_test(new_communication_config_id)

    # new_ipc_performance_id = ipc_performance_add_data_test()
    # print(f"new_ipc_performance_id: {new_ipc_performance_id}")
    # new_ipc_performance_id = 7
    # ipc_performance_update_data_test(new_ipc_performance_id)
    # ipc_performance_query_data_test(new_ipc_performance_id)
    # ipc_performance_delete_data_test(new_ipc_performance_id)

    # new_simulation_result_id = simulation_result_add_data_test()
    # print(f"new_simulation_result_id: {new_simulation_result_id}")
    # new_simulation_result_id = 1
    # simulation_result_update_data_test(new_simulation_result_id)
    # simulation_result_query_data_test(new_simulation_result_id)
    # simulation_result_delete_data_test(new_simulation_result_id)

    # simulation_result_query_test()

    # used_controller_id_test()

    # used_cpu_gpus_test()

    print(f"Done")