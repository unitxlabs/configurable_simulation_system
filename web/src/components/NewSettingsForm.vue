<template>
  <div>
    <el-card>
      <el-row style="position: relative;">
        <el-col :span="18">
          <el-form label-width="150px" label-position="left">
            <el-row :gutter="10">
              <el-col :span="8" v-for="(field, index) in inputFields" :key="field.key || index">
                <el-form-item :label="field.label">
                  <el-select v-model="field.val" style="width: 240px" v-if="field.source">
                    <el-option v-for="item in field.source" :key="item.val" :label="item.label" :value="item.val" />
                  </el-select>
                  <el-input v-else v-model="field.val" :placeholder="`请输入${field.label}`" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-col>

        <el-col :span="6" class="fixed-button-group">
          <el-button type="primary" :disabled="isSaveOrApplyDisabled" @click="handleSave()">保存</el-button>
          <el-button v-if="isApplyShow" :disabled="isSaveOrApplyDisabled" @click="handleApply()">应用</el-button>
        </el-col>
      </el-row>
    </el-card>
    <el-card style="margin-top: 20px;">
      <el-table :data="settingsData" style="width: 100%" stripe>
        <el-table-column label="是否使用" prop="isActive">
          <template #default="scope">
            <el-switch v-model="scope.row.isActive" />
          </template>
        </el-table-column>
        <el-table-column v-for="(column, index) in tableColumnsForConfig" :key="index" :label="column.label">
          <template v-slot="scope">
            <span v-if="column.prop === 'resolution'">
              {{ scope.row.image_width }} x {{ scope.row.image_height }}
            </span>
            <span v-else>
              {{ getNestedValue(scope.row, column.prop) }}
            </span>
          </template>
        </el-table-column>
        <!-- <el-table-column label="操作">
          <template v-slot="scope">
            <el-button @click="deleteNewSetting(scope.row)">删除</el-button>
          </template>
        </el-table-column> -->
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue';
const props = defineProps([
  'title',
  'inputFields',
  'tableColumnsForConfig',
  'settingsData',
  'saveNewSetting',
  'applyNewSetting',
  'deleteNewSetting'
]);
const isSaveOrApplyDisabled = computed(() => {
  return props.inputFields.some(field => !field.val);
});
const getNestedValue = (row, path) => {
  const keys = path.split('.');
  return keys.reduce((obj, key) => (obj && obj[key] !== undefined) ? obj[key] : '', row);
}
const isApplyShow = computed(() => {
  return props.applyNewSetting != undefined && props.applyNewSetting != '';
});
const handleSave = () => {
  const inputData = props.inputFields.reduce((acc, field) => {
    acc[field.model] = field.val;
    return acc;
  }, {});

  props.saveNewSetting(inputData, props.settingsData);
};

const handleApply = () => {
  const inputData = props.inputFields.reduce((acc, field) => {
    acc[field.model] = field.val;
    return acc;
  }, {});
  props.applyNewSetting(inputData, props.settingsData);
};

</script>
<style scoped>
.fixed-button-group {
  padding-left: 10px;
}
</style>