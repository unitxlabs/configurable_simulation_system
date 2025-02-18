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
