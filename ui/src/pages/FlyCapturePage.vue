<template>
  <div class="app-container">
    <div class="content">
      <div class="tabs">
        <button @click="activeTab = 'saved'" :class="{ active: activeTab === 'saved' }">保存的设置</button>
        <button @click="activeTab = 'new'" :class="{ active: activeTab === 'new' }">新建设置</button>
      </div>

      <!-- 保存的设置 -->
      <div v-if="activeTab === 'saved'">
        <h2>保存的设置（飞拍）</h2>

        <div class="filters">
          <input type="text" v-model="filterId" placeholder="🔍控制器ID" />
          <input type="text" v-model="filterTimeToNext" placeholder="🔍到下一个工位的时间 (ms)" />
          <input type="text" v-model="filterSequenceCount" placeholder="🔍sequence的数量" />
          <input type="text" v-model="filterSequenceIntervals" placeholder="🔍sequence之间的时间间隔 (us)" />
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>是否启用</th>
              <th>控制器ID</th>
              <th>到下一个工位的时间 (ms)</th>
              <th>sequence的数量</th>
              <th>sequence之间的时间间隔 (us)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in filteredSavedSettings" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.id }}</td>
              <td>{{ entry.timeToNext }}</td>
              <td>{{ entry.sequenceCount }}</td>
              <td>{{ entry.sequenceIntervals }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 新建设置 -->
      <div v-if="activeTab === 'new'">
        <h2>新建设置（飞拍）</h2>
        <div class="toolbar">
          <button @click="saveNewSetting">保存</button>
          <button>取消</button>
          <button>删除</button>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>是否启用</th>
              <th>控制器ID</th>
              <th>到下一个工位的时间 (ms)</th>
              <th>sequence的数量</th>
              <th>sequence之间的时间间隔 (us)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in newSettings" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.controller_id }}</td> <!-- 控制器ID直接显示 -->
              <td><input type="text" v-model="entry.timeToNext" placeholder="到下一个工位的时间 (ms)" :disabled="!entry.enabled" /></td>
              <td><input type="text" v-model="entry.sequenceCount" placeholder="sequence的数量" :disabled="!entry.enabled"/></td>
              <td><input type="text" v-model="entry.sequenceIntervals" placeholder="sequence之间的时间间隔 (us)" :disabled="!entry.enabled"/></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const activeTab = ref('saved');

const filterId = ref('');
const filterTimeToNext = ref('');
const filterSequenceCount = ref('');
const filterSequenceIntervals = ref('');

const savedSettings = ref([]);

const filteredSavedSettings = computed(() => {
  return savedSettings.value.filter((entry) => {
    const matchesId = filterId.value === '' || entry.id.includes(filterId.value);
    const matchesTimeToNext = filterTimeToNext.value === '' || entry.timeToNext.includes(filterTimeToNext.value);
    const matchesSequenceCount =
      filterSequenceCount.value === '' || entry.sequenceCount.toString().includes(filterSequenceCount.value);
    const matchesSequenceIntervals =
      filterSequenceIntervals.value === '' || entry.sequenceIntervals.includes(filterSequenceIntervals.value);

    return matchesId && matchesTimeToNext && matchesSequenceCount && matchesSequenceIntervals;
  });
});

// 新建设置，根据控制器 ID 列表自动补全
const newSettings = ref([]);

const controllerIds = ref([]);

onMounted(() => {
  fetchSavedSettings();
  fetchControllerIds();
});

const fetchSavedSettings = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/communication_config/fly_capture');
    if (response.data && Array.isArray(response.data)) {
      savedSettings.value = response.data.map((item) => ({
        enabled: false,
        id: item.controller_id || '',
        timeToNext: item.to_next_ws_offset || '',
        sequenceCount: item.sequences_id.length,
        sequenceIntervals: item.sequences_interval.join(', '),
      }));
    }
  } catch (error) {
    console.error('Error fetching saved settings:', error);
  }
};

const fetchControllerIds = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/controller_config');
    if (response.data && Array.isArray(response.data)) {
      controllerIds.value = response.data.map((item) => item.controller_id);
      // 使用控制器 ID 生成新建设置的表格
      newSettings.value = controllerIds.value.map((id) => ({
        enabled: false,
        controller_id: id,
        timeToNext: '1500', // 默认值
        sequenceCount: '4', // 默认值
        sequenceIntervals: '30000, 30000, 30000', // 默认值
      }));
    }
  } catch (error) {
    console.error('Error fetching controller IDs:', error);
  }
};

const saveNewSetting = async () => {
  try {
    // 过滤出已勾选的行
    const settingsToSave = newSettings.value
      .filter((entry) => entry.enabled)  // 只处理 enabled 为 true 的行
      .map((entry) => ({
        controller_id: String(entry.controller_id),
        to_next_ws_offset: entry.timeToNext,
        sequence_count: entry.sequenceCount,
        sequences_interval: entry.sequenceIntervals.split(',').map((interval) => parseInt(interval.trim())),
      }));

    // 获取勾选的控制器 ID 列表
    const controllerIdsToSave = settingsToSave.map(entry => entry.controller_id);

    // 创建 workstation_in_use 数组，表示勾选的行是否启用
    const workstationInUse = newSettings.value.map(entry => entry.enabled);

    // 准备需要发送给后端的数据
    const requestData = {
      workstation_configs: settingsToSave,  // workstation_config 数据
      communication_config: {
        part_type: 'test',
        part_interval: 2.8,
        communication_type: 1,
        communication_step: 2,
        workstation_count: settingsToSave.length,  // 勾选的行数
        workstation_config_ids: controllerIdsToSave,  // 勾选的控制器 ID
        workstations_in_use: workstationInUse,  // 创建的布尔数组
      }
    };

    // 发送请求给后端保存 workstation_config 和 communication_config
    const response = await axios.post('http://localhost:5000/api/workstation_config/fly_capture', requestData);

    if (response.status === 200) {
      alert('新设置保存成功！');
      fetchSavedSettings();  // 更新保存的设置列表
    }

  } catch (error) {
    console.error('Error saving new setting:', error);
    alert('保存设置失败，请重试。');
  }
};


</script>

<style>
.app-container {
  display: flex;
  font-family: Arial, sans-serif;
  height: 100vh;
}

.content {
  flex: 1;
  padding: 20px;
}

.tabs button {
  padding: 10px;
  margin-right: 10px;
  cursor: pointer;
}

.tabs .active {
  background-color: #007bff;
  color: white;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

input[type="text"] {
  padding: 5px;
  width: 200px;
  height: 35px; /* 调高搜索框高度 */
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 10px;
}

select {
  padding: 5px;
  width: 200px;
  height: 36px;
  font-size: 14px;
}

button {
  padding: 5px 10px;
  height: 36px;
  font-size: 14px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 10px;
  border: 1px solid #ccc;
  text-align: left;
}
</style>