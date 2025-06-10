<template>
  <el-container direction="vertical" style="padding: 20px;">
    <el-card>
      <el-row style="position: relative; padding-right: 220px;">
        <el-col :span="18">
          <el-form :model="form" label-width="100px">
            <el-row :gutter="10">
              <el-col :span="8" v-for="(field, index) in defaultFields" :key="field.key + index">
                <el-form-item :label="field.label">
                  <el-select v-model="form[field.key]" style="width: 240px" v-if="field.source" placeholder="请选择">
                    <el-option v-for="item in field.source.value" :key="item.value" :label="item.label"
                      :value="item.value" />
                  </el-select>
                  <el-input v-else v-model="form[field.key]" :placeholder="`请输入${field.label}`" clearable
                    @keyup.enter="searchData">
                    <template #prefix>
                      <el-icon>
                        <Search />
                      </el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="10">
              <template v-for="(item, index) in dynamicFields" :key="item.key+index">
                <el-col :span="10">
                  <el-form-item :label="item.label">
                    <el-input v-model="item.value" :placeholder="'请输入' + item.label" clearable
                      @keyup.enter="searchData">
                      <template #prefix>
                        <el-icon>
                          <Search />
                        </el-icon>
                      </template>
                    </el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="2" style="display: flex;">
                  <el-button type="danger" @click="removeField(item.key)" size="small">删除</el-button>
                </el-col>
              </template>
            </el-row>
          </el-form>
        </el-col>

        <el-col :span="6" class="fixed-button-group">
          <el-button type="primary" @click="showDialog = true">添加搜索框</el-button>
          <el-button type="success" @click="searchData">数据查询</el-button>
          <el-button type="warning" @click="exportData">导出</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-dialog v-model="showDialog" title="选择搜索条件" width="400px">
      <el-form>
        <el-form-item label="请选择要添加的搜索条件">
          <el-select v-model="selectedField" placeholder="请选择" style="width: 100%;">
            <el-option v-for="option in availableFields" :key="option.key" :label="option.label" :value="option.key" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddField">确定</el-button>
      </template>
    </el-dialog>

    <!-- 底部表格 -->
    <el-card style="margin-top: 20px; flex: 1;">
      <el-table ref="tableRef" :data="tableData" border style="width: 100%;" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55"></el-table-column> <!-- 选择列 -->
        <el-table-column prop="id" label="ID" width="80" :formatter="formatID"></el-table-column>
        <el-table-column prop="name" label="名称" width="120" :formatter="formatName"></el-table-column>
<!--        <el-table-column prop="material_image_count" label="物料图片数量" :formatter="formatMIC"></el-table-column>
        <el-table-column prop="material_inference_times" label="物料图片推理次数" :formatter="formatMIT"></el-table-column>
        -->
        <el-table-column prop="controller_version" label="控制器版本" :formatter="formatCV"></el-table-column>
        <el-table-column prop="fps" label="FramesPerSecond" :formatter="formatFps"></el-table-column>
        <el-table-column prop="mps" label="MegapixelsPerSecond" :formatter="formatMps"></el-table-column>
        <el-table-column prop="avg_part_use_time" label="AvgPartUseTime" :formatter="formatAvgPartUseTime"></el-table-column>
        <el-table-column prop="avg_image_capture_time" label="AvgImageCaptureTime" :formatter="formatAvgImageCaptureTime"></el-table-column>
        <el-table-column prop="avg_cortex_infer_time" label="AvgCortexInferTime" :formatter="formatAvgCortexInferTime"></el-table-column>
        <el-table-column prop="cpu" label="CPU" :formatter="formatCPU"></el-table-column>
        <el-table-column prop="gpu" label="GPU" :formatter="formatGPU"></el-table-column> 
      </el-table>
    </el-card>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import { fetchData, fetchSelectData } from "~/api/data";
import * as XLSX from "xlsx";
const form = ref({
  search: '',
  cpu: '',
  gpu: ''
});
const cpuOptions = ref([]);
const gpuOptions = ref([]);
const defaultFields = [
  { key: 'search', label: '搜索' },
  { key: 'cpu', label: 'CPU', source: cpuOptions },
  { key: 'gpu', label: 'GPU', source: gpuOptions }
];
const fieldOptions = [
  { key: 'camera_count', label: '相机个数' },
  // { key: 'camera_resolution', label: '相机分辨率' },
  //{ key: 'total_image_count', label: '物料图片数量' },
  //{ key: 'total_inference_count', label: '物料图片推理次数' },
  // { key: 'model_count', label: '模型数量' },
  { key: 'each_ng_type_defect_count', label: '缺陷数量' },
  { key: 'part_interval', label: '物料间隔' },
  { key: 'cameras_type', label: '相机型号' }
  // ,
  // { key: 'controller_version', label: '控制器版本' }
];

const dynamicFields = ref([]);

const showDialog = ref(false);
const selectedField = ref('');

const availableFields = computed(() => {
  const addedKeys = dynamicFields.value.map(item => item.key);
  return fieldOptions.filter(option => !addedKeys.includes(option.key));
});

const confirmAddField = () => {
  if (!selectedField.value) {
    ElMessage.warning("请选择要添加的搜索条件");
    return;
  }
  const field = fieldOptions.find(f => f.key === selectedField.value);
  if (field) {
    dynamicFields.value.push({ key: field.key, label: field.label, value: '' });
    selectedField.value = '';
    showDialog.value = false;
  }
};

const removeField = (key) => {
  dynamicFields.value = dynamicFields.value.filter(field => field.key !== key);
};

const generateQueryParams = () => {
  let params = { ...form.value };

  dynamicFields.value.forEach(field => {
    if (field.value) {
      params[field.key] = field.value;
    }
  });

  return Object.keys(params)
    .filter(key => params[key])
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
};

const searchData = async () => {
  const queryString = generateQueryParams();
  console.log("查询数据 GET 请求参数:", queryString);
  try {
    const data = await fetchData(queryString);
    tableData.value = data.data
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }

};
const getSelectData = async () => {
  try {
    const data = await fetchSelectData();
    gpuOptions.value = data.data.gpu_select_options
    cpuOptions.value = data.data.cpu_select_options
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }

};
const getColumnWidths = (aoa) =>{
  const colWidths = [];

  aoa.forEach(row => {
    row.forEach((cell, idx) => {
      const len = cell ? String(cell).length : 0;
      colWidths[idx] = Math.max(colWidths[idx] || 10, len + 2);
    });
  });

  return colWidths.map(wch => ({ wch }));
}
const exportData = async () => {
  await nextTick();

  if (selectedRows.value.length === 0) {
    ElMessage.warning("请勾选要导出的数据");
    return;
  }
  const exportParams = selectedRows.value.map(row => {
    return {
      id: row.simulation_result.id,
      name: row.ipc_performances.map(item => item.ipc_config.name).join(", "),
      cpu: row.ipc_performances.map(item => item.ipc_config.cpu).join(", "),
      gpu: row.ipc_performances.map(item => item.ipc_config.gpus.join(", ")).join(", "),
      //物料图片数量: row.simulation_result.total_image_count,
      //物料图片推理次数: row.simulation_result.total_inference_count,
      控制器版本: "V6",
      FramesPerSecond: row.simulation_result.fps,
      MegapixelsperSecond: row.simulation_result.mps,
      AvgPartUseTime: row.simulation_result.avg_part_use_time,
      AvgImageCaptureTime: row.simulation_result.avg_image_capture_time,
      AvgCortexInferTime: row.simulation_result.avg_cortex_infer_time,
      DetectionDimension: row.simulation_result.detection_dimension,
      PartType: row.simulation_result.part_type,
      PartInterval: row.simulation_result.part_interval,
      NgTypeCount: row.simulation_result.ng_type_count,
      EachNgTypeDefectCount: row.simulation_result.each_ng_type_defect_count,
      IpcCount: row.simulation_result.ipc_count,
      IsImageSaving: row.simulation_result.is_image_saving,
      PartCount: row.simulation_result.part_count,
      TotalTimeUsed: row.simulation_result.total_time_used,
      MaxPartUseTime: row.simulation_result.max_part_use_time,
      MinPartUseTime: row.simulation_result.min_part_use_time,
      Max_Image_Capture_Time: row.simulation_result.max_image_capture_time,
      Min_Image_Capture_Time: row.simulation_result.min_image_capture_time,
      MaxCortexInferTime: row.simulation_result.max_cortex_infer_time,
      MinCortexInferTime: row.simulation_result.min_cortex_infer_time,
      CoreAllocation: row.simulation_result.core_allocation
    };
  });

  console.log("导出的数据:", exportParams);

  if (!tableRef.value) return;

  const columns = tableRef.value.columns.filter(col => col.type !== "selection");

  // const headers = columns.map(col => col.label);
  // const data = selectedRows.value.map(row => columns.map(col => col.formatter ? col.formatter(row, null, row[col.property], col) : row[col.property]));
  const headers = Object.keys(exportParams[0]); // 获取字段名数组
  const data = exportParams.map(record => headers.map(key => record[key]));
  const sheetData = [headers, ...data];
  console.log(sheetData)

  const worksheet = XLSX.utils.aoa_to_sheet(sheetData);
  worksheet['!cols'] = getColumnWidths(sheetData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");

  XLSX.writeFile(workbook, "data.xlsx");
};
const selectedRows = ref([]);
const handleSelectionChange = (selection) => {
  selectedRows.value = selection;
};
const tableData = ref([
]);

const tableRef = ref(null);
onMounted(() => {
  searchData()
  getSelectData()
});
const formatCPU = (row) => {
  return row.ipc_performances.map(item => item.ipc_config.cpu).join(", ");
};

const formatGPU = (row) => {
  return row.ipc_performances.map(item => item.ipc_config.gpus.join(", ")).join(", ");
};

const formatName = (row) => {
  return row.ipc_performances.map(item => item.ipc_config.name).join(", ");
};

const formatID = (row) => {
  return row.simulation_result.id;
};

const formatMIC = (row) => {
  return row.simulation_result.total_image_count;
};
const formatMIT = (row) => {
  return row.simulation_result.total_inference_count;
};
const formatCV = (row) => {
  return "V6";
};
const formatFps = (row) => {
  return row.simulation_result.fps;
};
const formatMps = (row) => {
  return row.simulation_result.mps;
};
const formatAvgPartUseTime = (row) => {
  return row.simulation_result.avg_part_use_time;
};
const formatAvgImageCaptureTime = (row) => {
  return row.simulation_result.avg_image_capture_time;
};
const formatAvgCortexInferTime = (row) => {
  return row.simulation_result.avg_cortex_infer_time;
};

</script>

<style scoped>
.fixed-button-group {
  position: absolute;
  right: 0;
  top: 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.el-dialog {
  border-radius: 10px;
}

.el-dialog__title {
  font-size: 18px;
  font-weight: bold;
}

.el-form-item {
  margin-bottom: 20px;
}
</style>
