<template>
  <el-tabs v-model="activeTab" type="border-card">
    <el-tab-pane :label="title" name="name">
      <el-row style="position: relative;">
        <el-col :span="18">
          <el-descriptions :column="4" border>
            <el-descriptions-item v-for="(field, index) in inputFields" :key="index" :label="field.label">
              {{ formatFieldValue(field) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-col>

        <!-- <el-col :span="6" class="fixed-button-group">
            <el-button type="primary" @click="handleApply()">加载</el-button>
            <el-button @click="handleDelete()">删除</el-button>
          </el-col> -->
      </el-row>
      <el-table :data="settingsData" style="width: 100%;margin-top: 10px;" stripe :max-height="computedHeight">
        <el-table-column label="激活状态" prop="isActive">
          <template #default="scope">
            <el-switch v-model="scope.row.isActive" disabled />
          </template>
        </el-table-column>
        <el-table-column v-for="(column, index) in tableColumnsForConfig" :key="index" :label="column.label"
          :prop="column.prop" />
      </el-table>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup>
import { ref, computed } from 'vue';
const activeTab = ref('name');
const props = defineProps([
  'title',
  'inputFields',
  'tableColumnsForConfig',
  'settingsData',
]);
const formatFieldValue = (field) => {
  if (field) {
    if ((field.model === 'create_time' || field.model === 'modified_time') && field.val) {
      return field.val.replace("T", " ").split(".")[0];
    }
    return field.val;
  }
};
const windowHeight = ref(window.innerHeight)

const computedHeight = computed(() => {
  return Math.max((windowHeight.value - 420) / 2, 160) + 'px'
})
</script>
<style scoped>
.fixed-button-group {
  position: absolute;
  right: 0;
  top: 0;
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>