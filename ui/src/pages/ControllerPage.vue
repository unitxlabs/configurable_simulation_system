<template>
  <div class="app-container">
    <!-- 主内容 -->
    <div class="content">
      <div class="tabs">
        <button
          @click="activeTab = 'saved'"
          :class="{ active: activeTab === 'saved' }"
          class="tab-button"
        >
          保存的设置
        </button>
        <button
          @click="activeTab = 'new'"
          :class="{ active: activeTab === 'new' }"
          class="tab-button"
        >
          新建设置
        </button>
      </div>

      <!-- 保存的设置选项卡 -->
      <div v-if="activeTab === 'saved'" class="tab-content">
        <div v-if="activeTab === 'saved'" class="tab-frame"></div>
        <h2>保存的设置</h2>
        <div class="search-bar">
          <input v-model="searchName" placeholder="🔍 控制器ID" />
          <input v-model="searchID" placeholder="🔍 控制器版本" />
          <input v-model="searchResolution" placeholder="🔍 相机分辨率" />
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
            <tr v-for="(entry, index) in filteredControllers" :key="index" :class="{'odd-row': index % 2 === 0, 'even-row': index % 2 !== 0}">
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
      <div v-if="activeTab === 'new'" class="tab-content">
        <div v-if="activeTab === 'new'" class="tab-frame"></div>
        <h2>新建设置</h2>
        <div class="toolbar">
          <button @click="saveNewController">保存</button>
          <button @click="addNewRow">添加一行</button> <!-- 添加一行按钮 -->
          <button @click="deleteLastRow">删除最下面一行</button> <!-- 删除最下面一行按钮 -->
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
            <tr v-for="(entry, index) in newControllers" :key="index" :class="{'odd-row': index % 2 === 0, 'even-row': index % 2 !== 0}">
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
const controllerConfig = ref([]);

// 默认初始化一行新数据
const newControllers = ref([
  { enabled: false, id: '', version: 'V4', camera: '', resolution: '' }
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
  const resolutionPattern = /^\d+\*\d+$/;
  for (const entry of newControllers.value) {
    if (entry.enabled && !resolutionPattern.test(entry.resolution)) {
      alert('相机分辨率格式不正确！必须是数字*数字的形式');
      return;
    }
  }

  const newControllerData = newControllers.value
    .filter(entry => entry.enabled)
    .map(entry => ({
      controller_name: entry.id,
      enabled: entry.enabled,
      controller_id: entry.id,
      controller_version: entry.version,
      cameras_id: [entry.camera],
      image_width: entry.resolution.split('*')[0],
      image_height: entry.resolution.split('*')[1]
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
    newControllers.value.pop();
  } else {
    alert('至少保留一行数据');
  }
};
</script>

<style scoped>
.app-container {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.tabs {
  margin-bottom: 20px;
  display: flex;
}

.tab-button {
  padding: 10px 20px;
  margin-right: 10px;
  cursor: pointer;
  background-color: #4d4d4d; /* 深灰色 */
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  color: white;
}

.tab-button.active {
  background-color: #333; /* 深灰色激活状态 */
  color: white;
  border: 1px solid #4d4d4d;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.tab-button:hover {
  background-color: #333; /* 深灰色按钮悬停效果 */
}

.tab-content {
  position: relative;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
  margin-top: 20px;
  transition: all 0.3s ease;
}

.tab-frame {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border: 3px solid #4d4d4d; /* 蓝色边框 */
  border-radius: 10px;
  pointer-events: none; /* 允许点击通过框架 */
  transition: all 0.3s ease;
  opacity: 0; /* 初始为透明 */
}

.tab-content.active .tab-frame {
  opacity: 1; /* 当tab是active时，显示框架 */
}

.search-bar input {
  padding: 8px;
  margin-right: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.toolbar button {
  padding: 10px 20px;
  margin-right: 10px;
  cursor: pointer;
  background-color: #333;
  color: white;
  border: none;
  border-radius: 5px;
  transition: background-color 0.3s;
}

.toolbar button:hover {
  background-color: #4d4d4d;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.data-table th, .data-table td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}

.data-table th {
  background-color: #333; /* 表头深灰色 */
  color: white; /* 白色字体 */
}

.data-table .odd-row {
  background-color: white; /* 奇数行白色 */
}

.data-table .even-row {
  background-color: #f0f0f0; /* 偶数行浅灰色 */
}

/* 鼠标悬停时的效果 */
.data-table tr:hover {
  background-color: #ddd;
}

input[type="text"], select {
  padding: 8px 12px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

input[type="checkbox"] {
  width: 20px;
  height: 20px;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.tab-content .tab-frame {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 3px solid #007bff;
  border-radius: 10px;
  pointer-events: none; /* To allow clicking through the frame */
  transition: all 0.3s ease;
}

.tab-content.active .tab-frame {
  opacity: 1;
}
</style>
