<template>
  <el-container direction="vertical" style="padding: 20px;">
    <el-card style="flex: 1;">
      <el-table :data="tableData" border style="width: 98%;" :max-height="computedHeight">
        <el-table-column prop="date" label="时间" width="300px"></el-table-column>
        <el-table-column prop="desc" label="描述"></el-table-column>
      </el-table>
    </el-card>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { fetchSystemLog } from "~/api/data";
import { ElMessage } from 'element-plus';
const tableData = ref([
]);
const getLog = async () => {
  try {
    const data = await fetchSystemLog();
    tableData.value = data.data
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }

};

const tableRef = ref(null);
let intervalId = null;
onMounted(() => {
  intervalId = setInterval(getLog, 1000);
});
onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
})
const windowHeight = ref(window.innerHeight)

const computedHeight = computed(() => {
  return Math.max(windowHeight.value - 100, 640) + 'px'
})
</script>