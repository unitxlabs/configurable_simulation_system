import axios from "axios";

axios.defaults.baseURL = "/api";

interface FetchDataResponse {
  cpuData: number[];
  diskData: number[];
  memoryData: { name: string; value: number }[];
  timeData: string[];
}

export const fetchRunInfo = (): Promise<FetchDataResponse> => {
  return axios.get("/runInfo").then((response) => response.data);
};
export const fetchData = (search: string): Promise<FetchDataResponse> => {
  return axios.get(`/data/list?${search}`).then((response) => {
    return response.data;
  });
};
