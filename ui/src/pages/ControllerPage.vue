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
        <input v-model="newControllerName" placeholder="新设置名" />
        <div class="toolbar">
          <button @click="saveNewController">保存</button>
          <button>取消</button>
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
            <tr v-for="(entry, index) in newControllers" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.id }}</td>
              <td>{{ entry.version }}</td>
              <td>{{ entry.camera }}</td>
              <td>{{ entry.resolution }}</td>
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
const newControllerName = ref('');
const controllerConfig = ref([]);  // 保存从后端获取的控制器配置数据
const newControllers = ref([
  { enabled: true, id: '3232238088', version: 'V4', camera: 'L38458167', resolution: '2448*2048' },
  { enabled: true, id: '3232238089', version: 'V5', camera: 'L38458223', resolution: '2448*2048' }
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
  const newControllerData = newControllers.value.map(entry => ({
    controller_name: newControllerName.value,
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
</style>
