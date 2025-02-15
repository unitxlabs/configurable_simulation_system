<template>
  <div class="app-container">

    <!-- 主内容 -->
    <div class="content">
      <table class="data-table">
        <thead>
          <tr>
            <th>CPU</th>
            <th>GPUs</th>
            <th>RAM</th>
            <th>SSDs</th>
            <th>系统</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, index) in ipcData" :key="index">
            <td>{{ entry.cpu }}</td>
            <td><a :href="entry.gpu.link">{{ entry.gpu.name }}</a></td>
            <td>{{ entry.ram }}</td>
            <td><a :href="entry.ssd.link">{{ entry.ssd.name }}</a></td>
            <td>{{ entry.os }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const ipcData = ref([
  {
    cpu: '13th Gen Intel(R) Core(TM) i7-13700K',
    gpu: { name: 'NVIDIA GeForce RTX 4070 Ti 12282.0MB', link: '#' },
    ram: 'DDR5 5600MT/s 32 GB',
    ssd: { name: 'Samsung SSD 870', link: '#' },
    os: 'Ubuntu 22.0'
  }
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

a {
  color: blue;
  text-decoration: underline;
}
</style>
