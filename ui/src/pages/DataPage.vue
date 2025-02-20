<template>
  <div class="app-container">
    <div class="content">
      <div class="search-bar">
        <input type="text" placeholder="🔍Search" v-model="searchQuery" />
        <input type="text" placeholder="🔍CPU" v-model="cpuQuery" />
        <input type="text" placeholder="🔍GPU" v-model="gpuQuery" />
      </div>

      <div class="actions">
        <button @click="searchData">数据查询</button>
        <button @click="exportToCSV">导出数据库数据</button> <!-- 修改导出按钮的文本 -->
      </div>

      <!-- 数据表格 -->
      <table class="data-table">
        <thead>
          <tr>
            <th>CPU</th>
            <th>GPU</th>
            <th>RAM</th>
            <th>SSD</th>
          </tr>
        </thead>
        <tbody>
          <!-- 渲染数据 -->
          <tr v-for="(entry, index) in filteredEntries" :key="index">
            <td>{{ entry.cpu }}</td>
            <td>{{ entry.gpus.join(', ') }}</td> <!-- 将数组转换为逗号分隔的字符串 -->
            <td>{{ entry.ram }}</td>
            <td>{{ entry.ssds.join(', ') }}</td> <!-- 将数组转换为逗号分隔的字符串 -->
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';

const dataEntries = ref([]); // 定义一个响应式变量用于存储后端返回的数据
const searchQuery = ref('');
const cpuQuery = ref('');
const gpuQuery = ref('');

// 使用 fetch 获取数据
onMounted(async () => {
  try {
    const response = await fetch('http://localhost:5000/api/config');
    const data = await response.json(); // 解析 JSON 数据

    // 将返回的数据转换为合适的格式
    dataEntries.value = data.map(item => ({
      cpu: item.cpu,
      gpus: item.gpus,
      ram: item.ram,
      ssds: item.ssds
    }));
  } catch (error) {
    console.error('Error fetching data:', error);
  }
});

// 计算属性：根据搜索条件过滤数据
const filteredEntries = computed(() => {
  return dataEntries.value.filter(entry => {
    // 过滤条件：如果输入框中有内容，才做过滤
    const matchesSearchQuery = entry.cpu.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      entry.gpus.some(gpu => gpu.toLowerCase().includes(gpuQuery.value.toLowerCase())) ||
      entry.ram.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      entry.ssds.some(ssd => ssd.toLowerCase().includes(searchQuery.value.toLowerCase()));

    const matchesCpuQuery = entry.cpu.toLowerCase().includes(cpuQuery.value.toLowerCase());
    const matchesGpuQuery = entry.gpus.some(gpu => gpu.toLowerCase().includes(gpuQuery.value.toLowerCase()));

    // 返回匹配的记录
    return (matchesSearchQuery && matchesCpuQuery && matchesGpuQuery);
  });
});

// 查询数据的函数
const searchData = () => {
  // 触发过滤逻辑，已通过计算属性自动处理
};

// 导出数据库表数据的函数
const exportToCSV = async () => {
  try {
    // 发送请求到后端导出数据
    const response = await fetch('http://localhost:5000/api/export_simulation_result', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    // 判断请求是否成功
    if (!response.ok) {
      throw new Error('导出数据失败');
    }

    // 创建一个临时的下载链接
    const blob = await response.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'simulation_result.csv'; // 设置下载文件名
    link.click(); // 触发下载
  } catch (error) {
    console.error('Error exporting data:', error);
    alert('导出数据失败，请重试。');
  }
};
</script>

<style scoped>
/* 样式保持不变 */
</style>
