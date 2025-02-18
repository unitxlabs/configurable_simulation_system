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
        <div class="filters">
          <input v-model="searchQuery" placeholder="🔍 搜索" />
          <input v-model="filterMaterial" placeholder="物料间隔" />
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
              <th>到下一个工位的时间 (ms)</th>
              <th>sequence的数量</th>
              <th>sequence之间的时间间隔 (us)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in savedSettings" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.id }}</td>
              <td>{{ entry.timeToNext }}</td>
              <td>{{ entry.sequenceCount }}</td>
              <td>{{ entry.sequenceIntervals }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="activeTab === 'new'">
        <h2>新建设置</h2>
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
              <th>到下一个工位的时间 (ms)</th>
              <th>sequence的数量</th>
              <th>sequence之间的时间间隔 (us)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in newSettings" :key="index">
              <td><input type="checkbox" v-model="entry.enabled" /></td>
              <td>{{ entry.id }}</td>
              <td>{{ entry.timeToNext }}</td>
              <td>{{ entry.sequenceCount }}</td>
              <td>{{ entry.sequenceIntervals }}</td>
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
const searchQuery = ref('');
const filterMaterial = ref('');
const savedSettings = ref([
  { enabled: true, id: '3232238091', timeToNext: '2000', sequenceCount: '3', sequenceIntervals: '30000, 50000' },
  { enabled: true, id: '3232238092', timeToNext: '2100', sequenceCount: '4', sequenceIntervals: '30000, 30000, 30000' }
]);
const newSettings = ref([
  { enabled: true, id: '3232238093', timeToNext: '1500', sequenceCount: '4', sequenceIntervals: '30000, 30000, 30000' },
  { enabled: true, id: '3232238094', timeToNext: '1600', sequenceCount: '2', sequenceIntervals: '30000, 30000' }
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
