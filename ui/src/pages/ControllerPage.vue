<template>
  <div class="app-container">
    <!-- 主内容 -->
    <div class="content">
      <div class="tabs">
        <button @click="activeTab = 'saved'" :class="{ active: activeTab === 'saved' }">保存的设置</button>
        <button @click="activeTab = 'new'" :class="{ active: activeTab === 'new' }">新建设置</button>
      </div>

      <!-- 保存的设置选项卡 -->
      <div v-if="activeTab === 'saved'">
        <h2>保存的设置</h2>
        <div class="search-bar">
          <input v-model="searchName" placeholder="🔍控制器ID" />
          <input v-model="searchID" placeholder="🔍控制器版本" />
          <input v-model="searchResolution" placeholder="🔍相机分辨率" />
          <button @click="searchConfig">搜索</button>
          <button>新建</button>
        </div>
        <div class="toolbar">
          <button>应用</button>
          <button>复制</button>
          <button>取消</button>
          <button>保存</button>
          <button>删除</button>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>是否启用</th>
              <th>控制器ID</th>
              <th>控制器版本</th>
              <th>连接的相机</th>
              <th>相机分辨率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in filteredControllers" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.controller_id }}</td>
              <td>{{ entry.controller_version }}</td>
              <td>{{ entry.cameras_id.join(', ') }}</td>
              <td>{{ entry.image_width }}x{{ entry.image_height }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 新建设置选项卡 -->
      <div v-if="activeTab === 'new'">
        <h2>新建设置</h2>
        <div class="toolbar">
          <button @click="saveNewController">保存</button>
          <button>取消</button>
          <button>删除</button>
        </div>
        <button @click="addNewRow">添加一行</button> <!-- 添加一行按钮 -->
        <button @click="deleteLastRow">删除最下面一行</button> <!-- 删除最下面一行按钮 -->
        <table class="data-table">
          <thead>
            <tr>
              <th>是否启用</th>
              <th>控制器ID</th>
              <th>控制器版本</th>
              <th>连接的相机</th>
              <th>相机分辨率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in newControllers" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td><input type="text" v-model="entry.id" placeholder="控制器ID" :disabled="!entry.enabled" /></td>
              <td>
                <select v-model="entry.version" :disabled="!entry.enabled">
                  <option value="V4">V4</option>
                  <option value="V5">V5</option>
                  <option value="V6">V6</option>
                </select>
              </td>
              <td><input type="text" v-model="entry.camera" placeholder="连接的相机" :disabled="!entry.enabled" /></td>
              <td><input type="text" v-model="entry.resolution" placeholder="相机分辨率" :disabled="!entry.enabled" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const activeTab = ref('saved');
const searchName = ref('');
const searchID = ref('');
const searchResolution = ref('');
const controllerConfig = ref([]);  // 保存从后端获取的控制器配置数据

// 默认初始化一行新数据
const newControllers = ref([
  { enabled: false, id: '', version: 'V4', camera: '', resolution: '' }  // 默认版本为V4
]);

// 获取控制器配置数据
onMounted(async () => {
  try {
    const response = await fetch('http://localhost:5000/api/controller_config');
    const data = await response.json();
    if (Array.isArray(data)) {
      controllerConfig.value = data;
    } else {
      console.error('Error: Invalid data format');
    }
  } catch (error) {
    console.error('Error fetching data:', error);
  }
});

// 搜索功能：过滤控制器配置
const searchConfig = () => {
  console.log('搜索条件:', searchName.value, searchID.value, searchResolution.value);
};

// 计算属性：根据搜索条件过滤控制器配置
const filteredControllers = computed(() => {
  return controllerConfig.value.filter(entry => {
    const matchesName = searchName.value ? entry.controller_id.includes(searchName.value) : true;
    const matchesID = searchID.value ? entry.controller_version.includes(searchID.value) : true;
    const matchesResolution = searchResolution.value ?
      (entry.image_width.toString().includes(searchResolution.value) || entry.image_height.toString().includes(searchResolution.value)) :
      true;

    return matchesName && matchesID && matchesResolution;
  });
});

// 保存新控制器数据到数据库
const saveNewController = async () => {
  // 验证相机分辨率格式
  const resolutionPattern = /^\d+\*\d+$/;  // 正则表达式，要求格式为数字*数字
  for (const entry of newControllers.value) {
    if (entry.enabled && !resolutionPattern.test(entry.resolution)) {
      alert('相机分辨率格式不正确！必须是数字*数字的形式');
      return; // 如果不符合格式，则不保存并提示用户
    }
  }

  // 过滤启用的控制器数据
  const newControllerData = newControllers.value
    .filter(entry => entry.enabled) // 只提交启用的控制器
    .map(entry => ({
      controller_name: entry.id,
      enabled: entry.enabled,
      controller_id: entry.id,
      controller_version: entry.version,
      cameras_id: [entry.camera],  // 这里假设只有一个相机
      image_width: entry.resolution.split('*')[0],  // 分辨率宽度
      image_height: entry.resolution.split('*')[1]  // 分辨率高度
    }));

  try {
    const response = await fetch('http://localhost:5000/api/controller_config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newControllerData),
    });
    const result = await response.json();
    if (response.ok) {
      alert('保存成功');
    } else {
      alert('保存失败');
    }
  } catch (error) {
    console.error('Error saving new controller:', error);
  }
};

// 添加一行新数据
const addNewRow = () => {
  newControllers.value.push({ enabled: false, id: '', version: 'V4', camera: '', resolution: '' });
};

// 删除最下面一行
const deleteLastRow = () => {
  if (newControllers.value.length > 1) {
    newControllers.value.pop(); // 删除数组中的最后一项
  } else {
    alert('至少保留一行数据'); // 至少保留一行数据
  }
};
</script>

<style scoped>
/* 样式可以根据需要进行调整 */
.app-container {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.tabs {
  margin-bottom: 20px;
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

.toolbar {
  margin-bottom: 10px;
}

.toolbar button {
  margin-right: 10px;
  padding: 5px 10px;
  cursor: pointer;
}

.search-bar {
  margin-bottom: 10px;
}

.search-bar input {
  margin-right: 5px;
  padding: 5px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.data-table th, .data-table td {
  padding: 10px;
  border: 1px solid #ccc;
  text-align: left;
}

input[type="text"] {
  margin-bottom: 10px;
  padding: 5px;
  width: 200px;
}

select {
  margin-bottom: 10px;
  padding: 5px;
}
</style>
