<template>
  <div class="app-container">

    <!-- 主内容 -->
    <div class="content">
      <div class="search-bar">
        <input type="text" placeholder="search" />
        <input type="text" placeholder="CPU" />
        <input type="text" placeholder="GPU" />
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button>添加搜索项</button>
        <button>数据查询</button>
        <button>数据导出</button>
      </div>

      <!-- 数据表格 -->
      <table class="data-table">
        <thead>
          <tr>
            <th>CPU</th>
            <th>GPUs</th>
            <th>RAM</th>
            <th>SSDs</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, index) in dataEntries" :key="index">
            <td>{{ entry.cpu }}</td>
            <td>{{ entry.gpu }}</td>
            <td>{{ entry.ram }}</td>
            <td>{{ entry.ssd }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const dataEntries = ref([
  {
    cpu: '13th Gen Intel(R) Core(TM) i7-13700K',
    gpu: 'NVIDIA GeForce RTX 4070 Ti 12282.0MB',
    ram: 'DDR5 5600MT/s 32 GB',
    ssd: 'Samsung SSD 870'
  }
]);

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

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  padding: 5px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

button {
  padding: 5px 10px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #e0e0e0;
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

