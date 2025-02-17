<template>
  <div class="app-container">

    <!-- 主内容 -->
    <div class="content">
      <div class="tabs">
        <button @click="start">运行</button>
        <button @click="pause">暂停</button>
        <button @click="stop">停止</button>
        <button @click="exportData">数据导出</button>
      </div>

      <div class="charts">
        <div class="chart" ref="lineChart"></div>
        <div class="chart" ref="pieChart"></div>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>数据项</th>
            <th>值</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(value, key) in dataMetrics" :key="key">
            <td>{{ key }}</td>
            <td>{{ value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import * as echarts from 'echarts';

const dataMetrics = ref({
  物料类型: 'Test',
  物料CT: '1.5s',
  物料图片: 20,
  总物料数: 109,
  总耗时: '2min34s',
  平均物料耗时: '1.41s',
  超时物料个数: 0,
  'OK 物料个数': 100,
  'NG 物料个数': 9,
  平均图片处理时间: '0.075s',
  平均图片采集时间: '20ms',
  平均图片推理时间: '25ms'
});

const lineChart = ref(null);
const pieChart = ref(null);

const start = () => console.log('运行');
const pause = () => console.log('暂停');
const stop = () => console.log('停止');
const exportData = () => console.log('数据导出');

onMounted(() => {
  const lineInstance = echarts.init(lineChart.value);
  lineInstance.setOption({
    xAxis: { type: 'category', data: ['1', '2', '3', '4'] },
    yAxis: { type: 'value' },
    series: [{ data: [10, 20, 15, 30], type: 'line' }]
  });

  const pieInstance = echarts.init(pieChart.value);
  pieInstance.setOption({
    series: [{
      type: 'pie',
      data: [
        { value: 40, name: '使用' },
        { value: 60, name: '空闲' }
      ]
    }]
  });
});
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

.charts {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.chart {
  width: 45%;
  height: 300px;
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
</style>
