<template>
  <div class="app-container">
    <!-- 主内容 -->
    <div class="content">
      <div class="tabs">
        <button :class="{ active: activeTab === '设置' }" @click="switchTab('设置')">设置</button>
        <button :class="{ active: activeTab === '运行' }" @click="switchTab('运行')">运行</button>
      </div>

      <!-- 设置内容 -->
      <div v-if="activeTab === '设置'">
        <h2>控制器设置</h2>
        <table class="data-table">
          <thead>
            <tr>
              <th>是否使用</th>
              <th>控制器ID</th>
              <th>控制器版本</th>
              <th>连接的相机</th>
              <th>相机分辨率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="controller in controllers" :key="controller.id">
              <td><input type="checkbox" v-model="controller.isUsed" /></td>
              <td>{{ controller.id }}</td>
              <td>{{ controller.version }}</td>
              <td>{{ controller.camera }}</td>
              <td>{{ controller.resolution }}</td>
            </tr>
          </tbody>
        </table>

        <h2>通讯设置</h2>
        <table class="data-table">
          <thead>
            <tr>
              <th>是否使用</th>
              <th>控制器ID</th>
              <th>到下一个工位的时间</th>
              <th>sequence的数量</th>
              <th>sequence之间的时间间隔</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="communication in communications" :key="communication.id">
              <td><input type="checkbox" v-model="communication.isUsed" /></td>
              <td>{{ communication.id }}</td>
              <td>{{ communication.to_next_ws_offset }}</td>
              <td>{{ communication.sequence_count }}</td>
              <td>{{ communication.sequences_interval }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 运行内容 -->
      <div v-if="activeTab === '运行'">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import * as echarts from 'echarts';

const activeTab = ref('运行');

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

const controllers = ref([
  { id: '3232238091', version: 'V6', camera: 'L38458111', resolution: '2448*2048', isUsed: true },
  { id: '3232238092', version: 'V6', camera: 'L38458115', resolution: '2448*2048', isUsed: false },
  { id: '3232238093', version: 'V6', camera: 'L38458123', resolution: '2448*2048', isUsed: true },
  { id: '3232238094', version: 'V6', camera: 'L38458235', resolution: '2448*2048', isUsed: true },
  { id: '3232238095', version: 'V6', camera: 'L38458252', resolution: '2448*2048', isUsed: false },
  { id: '3232238096', version: 'V6', camera: 'L38458632', resolution: '2448*2048', isUsed: true }
]);

const communications = ref([
  { id: '3232238091', to_next_ws_offset: 100, sequence_count: 1, sequences_interval: '[100, 100, 100]', isUsed: true },
  { id: '3232238092', to_next_ws_offset: 200, sequence_count: 2, sequences_interval: '[100, 100, 100]', isUsed: false },
  { id: '3232238093', to_next_ws_offset: 300, sequence_count: 3, sequences_interval: '[100, 100, 100]', isUsed: true },
  { id: '3232238094', to_next_ws_offset: 400, sequence_count: 4, sequences_interval: '[100, 100, 100]', isUsed: true },
  { id: '3232238095', to_next_ws_offset: 500, sequence_count: 5, sequences_interval: '[100, 100, 100]', isUsed: false },
  { id: '3232238096', to_next_ws_offset: 600, sequence_count: 6, sequences_interval: '[100, 100, 100]', isUsed: true }
]);

const switchTab = (tab) => {
  activeTab.value = tab;
};

const lineChart = ref(null);
const pieChart = ref(null);

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

.tabs button.active {
  background-color: #007bff;
  color: white;
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
