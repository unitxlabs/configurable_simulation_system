<template>
  <el-container direction="vertical" style="padding: 20px;">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="保存的配置" name="savedConfig">
        <SettingsList :searchConditions="savedSearchConditions" :tableColumns="savedTableColumns"
          :settingsData="savedSettingsData" :searchSettings="handleSearchSettings" :editSetting="handleEditSetting"
          :deleteSetting="handleDeleteSetting" :applySetting="handleApplySetting" :actionColumns="actionTableColumns"
          :tableColumnsForConfig="tableColumnsForConfig" :inputFields="inputFields" />
      </el-tab-pane>

      <el-tab-pane label="新建配置" name="newConfig">
        <NewSettingsForm :tableColumnsForConfig="tableColumnsForConfig" :inputFields="inputFields"
          :settingsData="newSettings" :saveNewSetting="handleSaveSetting" :applyNewSetting=handleApplyNewSetting />
      </el-tab-pane>
    </el-tabs>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { fetchSaveCommunicationInfo, saveNewCommunicationSettingData, updateNewCommunicationSettingData, deleteCommunicationSettingData, fetchSaveWorkStationInfo, applyCommunicationSettingData } from "~/api/data";
const activeTab = ref('savedConfig');

const inputFields = ref([
  { label: '设置名', model: 'name', val: '', ignore: true },
  { label: '物料类型', model: 'part_type', val: '' },
  { label: '设物料时间间隔(s)', model: 'part_interval', val: '' },
  { label: 'part start到第一个工位的时间间隔(s)', model: 'part_start_to_ws1_interval', val: '' },
]);
const savedSearchConditions = ref([
  { placeholder: '按关键字搜索', model: 'part_type' },
  { placeholder: '物料间隔搜索', model: 'part_interval' },
]);
const tableColumnsForConfig = ref([
  { label: '控制器ID', prop: 'workstation_config.controller_config_id' },
  { label: '到下一个工位的时间(ms)', prop: 'workstation_config.to_next_ws_offset' },
  { label: 'sequence数量', prop: 'workstation_config.sequence_count' },
  { label: 'sequence之间的间隔', prop: 'workstation_config.sequences_interval' },
  { label: '相机复位时间', prop: 'workstation_config.camera_reset_time' },
]);
const savedTableColumns = ref([
  { label: '设置名', prop: 'name' },
  { label: '创建时间', prop: 'create_time' },
  { label: '修改时间', prop: 'modified_time' },
]);
const actionTableColumns = ref([
  { label: '编辑' }, { label: '应用' }, { label: '删除' },
])
const newSettings = ref([]);
const fetchSaveWorkStationList = async () => {
  try {
    const data = await fetchSaveWorkStationInfo('');
    newSettings.value = data.data.map(item => ({
      ...item,
      isActive: true
    }));
    fetchSaveCommunicationList('?communication_type=1');
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};
const handleSaveSetting = (inputData, settingsData) => {
  const transformedInputData = {
    name: inputData.name,
    part_type: inputData.part_type,
    part_interval: inputData.part_interval,
    communication_type: 1,
    communication_step: 0,
    part_start_to_ws1_interval: inputData.part_start_to_ws1_interval
  };

  const transformedSettingsData = {
    workstation_count: settingsData.filter(item => item.isActive).length,
    workstation_config_ids: settingsData.map(item => item.workstation_config.id),
    workstations_in_use: settingsData.map(item => item.isActive)
  };


  const mergedData = {
    ...transformedInputData,
    ...transformedSettingsData
  };

  saveNewCommunicationSettingData(mergedData)
    .then(response => {
      ElMessage.success('保存成功');
      fetchSaveWorkStationList()
      console.log('保存成功:', response);
    })
    .catch(error => {
      ElMessage.error('保存失败');
      console.error('保存失败:', error);
    });
}

function toQueryString(params) {
  const query = Object.entries(params)
    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');

  return query ? `?${query}` : '';
}
onMounted(() => {
  fetchSaveWorkStationList();
});
const fetchSaveCommunicationList = async (query) => {
  try {
    const data = await fetchSaveCommunicationInfo(query);
    savedSettingsData.value = data.data
    savedSettingsData.value = data.data.map(item => {
      return {
        ...item,
        configurations: newSettings.value.map(setting => {
          const idIndex = item.workstation_config_ids.indexOf(setting.workstation_config.id);
          return {
            ...setting,
            isActive: idIndex !== -1 ? item.workstations_in_use[idIndex] : setting.isActive
          };
        })
      };
    });
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};
const handleSearchSettings = (searchData) => {
  const queryData = {
    ...searchData,
    communication_type: 1,
  }
  fetchSaveCommunicationList(toQueryString(queryData))
}
const savedSettingsData = ref([]);
const handleEditSetting = (setting) => {
  const transformedInputData = {
    id: setting.id,
    name: setting.name,
    part_type: setting.part_type,
    part_interval: setting.part_interval,
    communication_type: 1,
    communication_step: 0,
    part_start_to_ws1_interval: setting.part_start_to_ws1_interval
  };


  const transformedSettingsData = {
    workstation_count: setting.configurations.filter(item => item.isActive).length,
    workstation_config_ids: setting.configurations.map(item => item.workstation_config.id),
    workstations_in_use: setting.configurations.map(item => item.isActive)
  };


  const mergedData = {
    ...transformedInputData,
    ...transformedSettingsData
  };
  updateNewCommunicationSettingData(mergedData)
    .then(response => {
      ElMessage.success('保存成功');
      fetchSaveWorkStationList()
      console.log('保存成功:', response);
    })
    .catch(error => {
      ElMessage.error('保存失败');
      console.error('保存失败:', error);
    });
}
const handleApplySetting = (setting) => {
  const transformedInputData = {
    id: setting.id,
    name: setting.name,
    part_type: setting.part_type,
    part_interval: setting.part_interval,
    communication_type: 1,
    communication_step: 0,
    part_start_to_ws1_interval: setting.part_start_to_ws1_interval
  };


  const transformedSettingsData = {
    workstation_count: setting.configurations.filter(item => item.isActive).length,
    workstation_config_ids: setting.configurations.map(item => item.workstation_config.id),
    workstations_in_use: setting.configurations.map(item => item.isActive)
  };


  const mergedData = {
    ...transformedInputData,
    ...transformedSettingsData
  };
  handleApplySettings(mergedData)
};
const handleApplySettings = (data) => {
  applyCommunicationSettingData(data)
    .then(response => {
      ElMessage.success('应用成功');
      fetchSaveWorkStationList()
    })
    .catch(error => {
      ElMessage.error('应用失败');
    });
}

const handleApplyNewSetting = (inputData, settingsData) => {
  const transformedInputData = {
    id: 0,
    name: inputData.name,
    part_type: inputData.part_type,
    part_interval: inputData.part_interval,
    communication_type: 1,
    communication_step: 0,
    part_start_to_ws1_interval: inputData.part_start_to_ws1_interval
  };
  console.log(settingsData.filter(item => console.log(item)))

  const transformedSettingsData = {
    workstation_count: settingsData.filter(item => item.isActive).length,
    workstation_config_ids: settingsData.map(item => item.workstation_config.id),
    workstations_in_use: settingsData.map(item => item.isActive)
  };


  const mergedData = {
    ...transformedInputData,
    ...transformedSettingsData
  };
  handleApplySettings(mergedData)
}
const deleteCommunicationData = async (query) => {
  try {
    await deleteCommunicationSettingData(query);
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};
const handleDeleteSetting = (setting) => {
  if (setting.id != '') {
    deleteCommunicationData(`?id=${setting.id}&communication_type=1`)
    fetchSaveWorkStationList()
  }
}
</script>