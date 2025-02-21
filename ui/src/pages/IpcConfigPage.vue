<template>
  <div class="app-container">
    <!-- 主内容 -->
    <div class="content">
      <table class="data-table">
        <thead>
          <tr>
            <th>CPU</th>
            <th>GPU</th>
            <th>RAM</th>
            <th>SSD</th>
            <th>系统</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="ipcData">
            <td>{{ ipcData.cpu }}</td>
            <td>{{ ipcData.gpu }}</td>
            <td>{{ ipcData.ram }}</td>
            <td>{{ ipcData.ssd }}</td>
            <td>{{ ipcData.os }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 定义响应式数据对象
const ipcData = ref(null);

// 获取 JSON 数据
const fetchHardwareInfo = async () => {
  try {
    const response = await fetch('/system_info.json'); // 确保 JSON 在 public 目录下
    if (!response.ok) throw new Error('Failed to fetch hardware data');
    ipcData.value = await response.json();
  } catch (error) {
    console.error('Error loading hardware info:', error);
  }
};

// 组件挂载后加载数据
onMounted(fetchHardwareInfo);
</script>

<style scoped>
.app-container {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.content {
  padding: 20px;
}

.tabs {
  margin-bottom: 20px;
  display: flex;
}

.tabs button {
  padding: 10px 20px;
  margin-right: 10px;
  cursor: pointer;
  background-color: #4d4d4d;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  color: white;
}

.tabs .active {
  background-color: #333;
  color: white;
  border: 1px solid #4d4d4d;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.tabs button:hover {
  background-color: #333;
}

.search-bar input {
  padding: 8px;
  margin-right: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.tab-content {
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #f9f9f9;
  margin-top: 20px;
}

.toolbar {
  margin-top: 20px;
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

.data-table th,
.data-table td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}

.data-table th {
  background-color: #333;
  color: white;
}

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
</style>
