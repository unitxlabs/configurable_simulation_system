<template>
  <el-container direction="vertical" style="padding: 20px;">

    <el-card style="margin-top: 20px; flex: 1;">
      <el-table :data="tableData" border style="width: 100%;">
        <el-table-column prop="cpu" label="CPU"></el-table-column>
        <el-table-column prop="gpu" label="GPU"></el-table-column>
        <el-table-column prop="ram" label="RAM"></el-table-column>
        <el-table-column prop="ssds" label="SSDS"></el-table-column>
        <el-table-column prop="name" label="系统"></el-table-column>
      </el-table>
    </el-card>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { fetchSystemInfo } from "~/api/data";
import { ElMessage } from 'element-plus';
const tableData = ref([
]);
const getSystemInfo = async () => {
  try {
    const data = await fetchSystemInfo();
    console.log(data)
    tableData.value = data.data
  } catch (error) {
    ElMessage.error("获取数据失败:" + error.response.data.detail);
  }

};

const tableRef = ref(null);
onMounted(() => {
  getSystemInfo()
});
</script>
