<template>
  <div class="app-container">

    <!-- 主内容 -->
    <div class="content">
      <div class="tabs">
        <button @click="activeTab = 'saved'" :class="{ active: activeTab === 'saved' }">保存的设置</button>
        <button @click="activeTab = 'new'" :class="{ active: activeTab === 'new' }">新建设置</button>
      </div>

      <div v-if="activeTab === 'saved'">
        <h2>保存的设置</h2>
        <div class="toolbar">
          <label>握手步数：</label>
          <select v-model="handshakeSteps">
            <option value="2">2步</option>
            <option value="4">4步</option>
          </select>
          <input type="text" placeholder="物料类型" />
          <input type="text" placeholder="物料时间间隔 (s)" />
          <input type="text" placeholder="part start 到第一个工位的时间间隔 (s)" />
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
            <tr v-for="(entry, index) in savedControllers" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.id }}</td>
              <td>{{ entry.version }}</td>
              <td>{{ entry.camera }}</td>
              <td>{{ entry.resolution }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="activeTab === 'new'">
        <h2>新建设置</h2>
        <input v-model="newControllerName" placeholder="新设置名" />
        <div class="toolbar">
          <button>应用</button>
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
import { ref } from 'vue';

const activeTab = ref('saved');
const newControllerName = ref('');
const handshakeSteps = ref('2');
const savedControllers = ref([
  { enabled: true, id: '3232238091', version: 'V6', camera: 'L38458111', resolution: '2448*2048' },
  { enabled: true, id: '3232238092', version: 'V6', camera: 'L38458115', resolution: '2448*2048' }
]);
const newControllers = ref([
  { enabled: true, id: '3232238093', version: 'V6', camera: 'L38458123', resolution: '2448*2048' },
  { enabled: true, id: '3232238094', version: 'V6', camera: 'L38458235', resolution: '2448*2048' }
]);
</script>

<style>
.app-container {
  display: flex;
  font-family: Arial, sans-serif;
  height: 100vh;
}

.sidebar {
  width: 150px;
  background-color: #f0f0f0;
  padding: 10px;
}

.sidebar ul {
  list-style: none;
  padding: 0;
}

.sidebar li {
  padding: 8px;
  cursor: pointer;
}

.sidebar .active {
  background-color: #a0c4ff;
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

.toolbar {
  margin-bottom: 10px;
}

.toolbar button {
  margin-right: 10px;
  padding: 5px 10px;
  cursor: pointer;
}

.toolbar select, .toolbar input {
  margin-right: 10px;
  padding: 5px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
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
