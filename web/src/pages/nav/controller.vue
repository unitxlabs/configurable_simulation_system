<template>
  <el-container direction="vertical" style="padding: 20px;">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="保存的配置" name="savedConfig">
        <SettingsList :searchConditions="savedSearchConditions" :tableColumns="savedTableColumns"
          :settingsData="savedSettingsData" :searchSettings="handleSearchSettings" :actionColumns="actionTableColumns"
          :deleteSetting="handleDeleteNewSetting" :tableColumnsForConfig="tableColumnsForConfig"
          :inputFields="inputFields" />
      </el-tab-pane>

      <el-tab-pane label="新建配置" name="newConfig">
        <NewSettingsForm :tableColumnsForConfig="tableColumnsForConfig" :inputFields="inputFields"
          :settingsData="newSettings" :saveNewSetting="handleSaveSetting" />
      </el-tab-pane>
    </el-tabs>
  </el-container>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { fetchCameraInfo, saveNewSettingData, fetchSaveCameraInfo, deleteSettingData } from "~/api/data";
const activeTab = ref('savedConfig');

const inputFields = ref([]);
const savedSearchConditions = ref([
  { placeholder: '按关键字搜索', model: 'controller_id' },
  { placeholder: '按控制器型号搜索', model: 'controller_version' },
  { placeholder: '按相机编号搜索', model: 'cameras_id' },
]);

const tableColumnsForConfig = ref([
  { label: '控制器 ID', prop: 'controller_id' },
  { label: '控制器版本', prop: 'controller_version' },
  { label: '相机', prop: 'cameras_id' },
  { label: '相机分辨率', prop: 'resolution' },
]);
const savedTableColumns = ref([
  { label: 'ID', prop: 'id' },
  { label: '控制器 ID', prop: 'controller_id' },
  { label: '控制器版本', prop: 'controller_version' },
  { label: '相机', prop: 'cameras_id' },
  { label: '相机分辨率', prop: 'resolution' },
]);
const actionTableColumns = ref([
  { label: '删除' },
])
const newSettings = ref([]);

const fetchNewSettingsData = async () => {
  try {
    const data = await fetchCameraInfo();
    newSettings.value = data.data
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};

watch(activeTab, (newTab) => {
  if (newTab === 'newConfig') {
    fetchNewSettingsData();
  }
});
const savedSettingsData = ref([]);
function toQueryString(params) {
  const query = Object.entries(params)
    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');

  return query ? `?${query}` : '';
}
const fetchCameraData = async (query) => {
  try {
    const data = await fetchSaveCameraInfo(query);
    console.log(data)
    savedSettingsData.value = data.data
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};
const deleteCameraData = async (query) => {
  try {
    await deleteSettingData(query);
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }
};
const handleSearchSettings = (searchData) => {
  fetchCameraData(toQueryString(searchData))
}

const handleSaveSetting = (inputData, settingsData) => {
  if (settingsData.length == 0) {
    ElMessage.warning('没有控制器数据');
    return
  }
  const filteredSettings = settingsData.filter(item => item.isActive);

  saveNewSettingData(filteredSettings)
    .then(response => {
      ElMessage.success('保存成功');
      fetchCameraData('');
      activeTab.value = "savedConfig"
    })
    .catch(error => {
      ElMessage.error('保存失败');
    });
}
const handleDeleteNewSetting = (setting) => {
  if (setting.id != '' && setting.controller_id != '') {
    deleteCameraData(`?id=${setting.id}&controller_id=${setting.controller_id}`)
    fetchCameraData('')
  }
}
onMounted(() => {
  fetchCameraData('');
});
</script>