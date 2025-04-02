interface DeviceInfo {
  id: number;
  cpu: string;
  gpu: string;
  ram: string;
  ssds: string;
  system: string;
}
interface FetchSystemInfoResponse {
  msg: string;
  data: DeviceInfo[];
}
interface Log {
  id: string;
  date: string;
  desc: string;
}
interface FetchLogResponse {
  code: number;
  message: string;
  data: DeviceInfo[];
}
interface CameraInfo {
  isActive: boolean;
  controller_id: string;
  controller_version: string;
  cameras_id: Array<string>;
  image_width: number;
  image_height: number;
  image_channel: number;
  capture_images_count: number;
  network_inference_count: number;
}
interface FetchCameraInfoResponse {
  msg: string;
  data: CameraInfo[];
}
interface DeviceData {
  id: number;
  name: string;
  cpu: string;
  gpu: string;
  camera_count: number;
  camera_resolution: string;
  material_image_count: number;
  material_inference_times: number;
  model_count: number;
  defect_count: number;
}

interface FetchDataResponse {
  code: number;
  message: string;
  data: DeviceData[];
}
interface SelectStringData {
  value: string;
  label: string;
}
interface FetchDataSelectResponse {
  code: number;
  data: {
    cpu_select_options: SelectStringData;
    gpu_select_options: SelectStringData;
  };
}
interface SystemLogResponse {
  msg: string;
  data: string[];
}
interface SettingsData {
  controller_id: string;
  controller_version: string;
  cameras_id: Array<string>;
  image_width: number;
  image_height: number;
  isActive: boolean;
}

interface CommonResponse {
  msg: string;
  data: any;
}
interface WorkStationInfo {
  id: number;
  workstation_id: number;
  controller_config_id: number;
  to_next_ws_offset: number;
  camera_reset_time: number;
  sequence_count: number;
  sequences_id: Array<number>;
  sequences_interval: Array<number>;
}
interface FetchWorkStationInfoResponse {
  msg: string;
  data: WorkStationInfo[];
}
interface WorkStationSettingsData {
  workstation_id: number;
  controller_config_id: number;
  to_next_ws_offset: number;
  camera_reset_time: number;
  sequence_count: number;
  sequences_id: Array<number>;
  sequences_interval: Array<number>;
}
interface WorkStationUpdateSettingsData {
  id: number;
  workstation_id: number;
  controller_config_id: number;
  to_next_ws_offset: number;
  camera_reset_time: number;
  sequence_count: number;
  sequences_id: Array<number>;
  sequences_interval: Array<number>;
}
interface SelectData {
  value: number;
  label: string;
}
interface SelectDataResponse {
  msg: string;
  data: SelectData[];
}

interface CommunicationInfo {
  id: number;
  name: string;
  part_type: string;
  part_interval: number;
  communication_type: number;
  communication_step: number;
  part_start_to_ws1_interval: number;
  workstation_count: number;
  workstation_config_ids: Array<number>;
  workstations_in_use: Array<boolean>;
}
interface FetchCommunicationInfoResponse {
  msg: string;
  data: CommunicationInfo[];
}
interface CommunicationSettingsData {
  name: string;
  part_type: string;
  part_interval: number;
  communication_type: number;
  communication_step: number;
  part_start_to_ws1_interval: number;
  workstation_count: number;
  workstation_config_ids: Array<number>;
  workstations_in_use: Array<boolean>;
}
interface CommunicationUpdateSettingsData {
  id: number;
  name: string;
  part_type: string;
  part_interval: number;
  communication_type: number;
  communication_step: number;
  part_start_to_ws1_interval: number;
  workstation_count: number;
  workstation_config_ids: Array<number>;
  workstations_in_use: Array<boolean>;
}
interface FetchRunInfoResponse {
  cpuData: number[];
  diskData: number[];
  memoryData: { name: string; value: number }[];
  timeData: string[];
}
