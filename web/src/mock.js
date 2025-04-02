// src/mock.js
import Mock from "mockjs";
const mockData = [
  {
    id: 1,
    name: "设备 A",
    cpu: "Intel i7",
    gpu: "NVIDIA RTX 3080",
    camera_count: 4,
    camera_resolution: "1920x1080",
    material_image_count: 1000,
    material_inference_times: 500,
    model_count: 5,
    defect_count: 3,
  },
  {
    id: 2,
    name: "设备 B",
    cpu: "AMD Ryzen 5",
    gpu: "AMD RX 6800",
    camera_count: 6,
    camera_resolution: "1280x720",
    material_image_count: 500,
    material_inference_times: 200,
    model_count: 3,
    defect_count: 1,
  },
  {
    id: 3,
    name: "设备 C",
    cpu: "Intel i9",
    gpu: "NVIDIA RTX 3070",
    camera_count: 2,
    camera_resolution: "2560x1440",
    material_image_count: 3000,
    material_inference_times: 1000,
    model_count: 7,
    defect_count: 0,
  },
  {
    id: 4,
    name: "设备 D",
    cpu: "AMD Ryzen 7",
    gpu: "AMD RX 5700",
    camera_count: 8,
    camera_resolution: "3840x2160",
    material_image_count: 2000,
    material_inference_times: 400,
    model_count: 6,
    defect_count: 2,
  },
  {
    id: 5,
    name: "设备 E",
    cpu: "Intel Xeon",
    gpu: "NVIDIA GTX 1080",
    camera_count: 10,
    camera_resolution: "1920x1080",
    material_image_count: 1500,
    material_inference_times: 700,
    model_count: 8,
    defect_count: 4,
  },
];
Mock.mock(/\/api\/data/, "get", (options) => {
  const query = new URLSearchParams(options.url.split("?")[1] || "");

  const search = query.get("search") || ""; // 搜索关键词
  const cpu = query.get("cpu") || ""; // cpu 参数
  const gpu = query.get("gpu") || ""; // gpu 参数
  const cameraCount = query.get("camera_count") || ""; // camera_count 参数
  const cameraResolution = query.get("camera_resolution") || ""; // camera_resolution 参数
  const materialImageCount = query.get("material_image_count") || ""; // material_image_count 参数
  const materialInferenceTimes = query.get("material_inference_times") || ""; // material_inference_times 参数
  const modelCount = query.get("model_count") || ""; // model_count 参数
  const defectCount = query.get("defect_count") || ""; // defect_count 参数

  // 数据过滤逻辑
  const filteredData = mockData.filter((item) => {
    return (
      (!search ||
        Object.values(item).some((val) =>
          String(val).toLowerCase().includes(search.toLowerCase())
        )) && // 对所有字段进行模糊匹配
      (!cpu ||
        (item.cpu && item.cpu.toLowerCase().includes(cpu.toLowerCase()))) &&
      (!gpu ||
        (item.gpu && item.gpu.toLowerCase().includes(gpu.toLowerCase()))) &&
      (!cameraCount || String(item.camera_count).includes(cameraCount)) &&
      (!cameraResolution ||
        item.camera_resolution
          .toLowerCase()
          .includes(cameraResolution.toLowerCase())) &&
      (!materialImageCount ||
        String(item.material_image_count).includes(materialImageCount)) &&
      (!materialInferenceTimes ||
        String(item.material_inference_times).includes(
          materialInferenceTimes
        )) &&
      (!modelCount || String(item.model_count).includes(modelCount)) &&
      (!defectCount || String(item.defect_count).includes(defectCount))
    );
  });

  return {
    code: 200,
    message: "success",
    data: filteredData,
  };
});
// 模拟动态变化的数据
Mock.mock("/api/runInfo", "get", () => {
  return {
    cpuData: [Mock.Random.integer(30, 100)], // 随机生成 CPU 数据
    diskData: [Mock.Random.integer(20, 100)], // 随机生成磁盘数据
    memoryData: [
      { name: "已用", value: Mock.Random.integer(30, 80) },
      { name: "空闲", value: Mock.Random.integer(20, 70) },
    ], // 随机生成内存占用数据
    timeData: [
      Mock.Random.now(), // 当前时间格式
    ],
  };
});
Mock.mock("/api/systemInfo", "get", () => {
  return {
    data: [
      {
        id: 1,
        cpu: "Intel i7",
        gpu: "NVIDIA RTX 3080",
        ram: "DDR5 5600MT/s 32",
        ssds: "SSD 870",
        system: "Ubuntu 22",
      },
    ],
  };
});
Mock.mock("/api/log", "get", () => {
  const now = Mock.Random.now();
  return {
    data: {
      id: now,
      date: now,
      desc: `这是${now}的日志`,
    },
  };
});
