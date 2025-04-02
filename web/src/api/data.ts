import axios from "axios";

axios.defaults.baseURL = "http://192.168.89.41:9999/api/v1";

export const fetchSystemInfo = (): Promise<FetchSystemInfoResponse> => {
  return axios.get(`/system/info`).then((response) => {
    return response.data;
  });
};

export const fetchLog = (): Promise<FetchLogResponse> => {
  return axios.get(`/log`).then((response) => {
    return response.data;
  });
};

export const fetchCameraInfo = (): Promise<FetchCameraInfoResponse> => {
  return axios.get(`/controller/list`).then((response) => {
    return response.data;
  });
};
export const fetchSaveCameraInfo = (
  query: string
): Promise<FetchCameraInfoResponse> => {
  return axios.get(`/controller/data${query}`).then((response) => {
    return response.data;
  });
};

export const saveNewSettingData = (
  data: SettingsData[]
): Promise<CommonResponse> => {
  return axios.post(`/controller/save`, data).then((response) => {
    return response.data;
  });
};
export const deleteSettingData = (query: string): Promise<CommonResponse> => {
  return axios.post(`/controller/delete${query}`).then((response) => {
    return response.data;
  });
};

export const fetchSystemLog = (): Promise<SystemLogResponse> => {
  return axios.get(`/system/log`).then((response) => {
    return response.data;
  });
};

export const fetchData = (search: string): Promise<FetchDataResponse> => {
  return axios.get(`/data/list?${search}`).then((response) => {
    return response.data;
  });
};
export const fetchSelectData = (): Promise<FetchDataSelectResponse> => {
  return axios.get(`/data/select`).then((response) => {
    return response.data;
  });
};
export const fetchCameraSelect = (
  status: string
): Promise<SelectDataResponse> => {
  return axios.get(`/controller/select?status=${status}`).then((response) => {
    return response.data;
  });
};
export const fetchSaveWorkStationInfo = (
  query: string
): Promise<FetchWorkStationInfoResponse> => {
  return axios.get(`/workstation/data${query}`).then((response) => {
    return response.data;
  });
};

export const saveNewWorkStationSettingData = (
  data: WorkStationSettingsData
): Promise<CommonResponse> => {
  return axios.post(`/workstation/save`, data).then((response) => {
    return response.data;
  });
};
export const updateNewWorkStationSettingData = (
  data: WorkStationUpdateSettingsData
): Promise<CommonResponse> => {
  return axios.post(`/workstation/update`, data).then((response) => {
    return response.data;
  });
};
export const deleteWorkStationSettingData = (
  query: string
): Promise<CommonResponse> => {
  return axios.post(`/workstation/delete${query}`).then((response) => {
    return response.data;
  });
};

export const fetchSaveCommunicationInfo = (
  query: string
): Promise<FetchWorkStationInfoResponse> => {
  return axios.get(`/communication/data${query}`).then((response) => {
    return response.data;
  });
};

export const saveNewCommunicationSettingData = (
  data: WorkStationSettingsData
): Promise<CommonResponse> => {
  return axios.post(`/communication/save`, data).then((response) => {
    return response.data;
  });
};
export const updateNewCommunicationSettingData = (
  data: WorkStationUpdateSettingsData
): Promise<CommonResponse> => {
  return axios.post(`/communication/update`, data).then((response) => {
    return response.data;
  });
};
export const deleteCommunicationSettingData = (
  query: string
): Promise<CommonResponse> => {
  return axios.post(`/communication/delete${query}`).then((response) => {
    return response.data;
  });
};
export const applyCommunicationSettingData = (
  data: WorkStationUpdateSettingsData
): Promise<CommonResponse> => {
  return axios.post(`/communication/apply`, data).then((response) => {
    return response.data;
  });
};
export const fetchRunInfo = (): Promise<FetchRunInfoResponse> => {
  return axios.get("/system/runInfo").then((response) => response.data);
};

export const fetchApplyCommunicationSettingData =
  (): Promise<CommonResponse> => {
    return axios.get(`/communication/applied_data`).then((response) => {
      return response.data;
    });
  };

export const runTask = (): Promise<CommonResponse> => {
  return axios.get("/task/run").then((response) => response.data);
};
export const getTaskStatus = (): Promise<CommonResponse> => {
  return axios.get("/task/status").then((response) => response.data);
};
export const taskPause = (): Promise<CommonResponse> => {
  return axios.get("/task/pause").then((response) => response.data);
};
export const taskResume = (): Promise<CommonResponse> => {
  return axios.get("/task/resume").then((response) => response.data);
};
export const taskStop = (): Promise<CommonResponse> => {
  return axios.get("/task/stop").then((response) => response.data);
};
export const getTaskResult = (): Promise<CommonResponse> => {
  return axios.get("/task/result").then((response) => response.data);
};
