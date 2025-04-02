<template>
  <div>
    <el-card>
      <el-row :gutter="20">
        <el-col v-for="(field, index) in searchFields" :key="index" :span="6">
          <el-input v-model="field.value" :placeholder="field.placeholder" />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card style="margin-top: 20px;">
      <el-table :data="settingsData" style="width: 100%" stripe>
        <el-table-column v-for="column in tableColumns" :key="column.prop" :label="column.label" :prop="column.prop">
          <template v-slot="scope">
            <span v-if="column.prop === 'resolution'">
              {{ scope.row.image_width }} x {{ scope.row.image_height }}
            </span>
            <span v-else-if="column.prop === 'create_time'">
              {{ formatDate(scope.row[column.prop]) }}
            </span>
            <span v-else-if="column.prop === 'modified_time'">
              {{ formatDate(scope.row[column.prop]) }}
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <template v-for="action in actionColumns" :key="action.label">
              <el-button :type="action.label == '删除' ? 'danger' : ''" @click="handleAction(action, scope.row)">
                {{ action.label }}
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>


    <el-dialog v-model="isEditDialogVisible" title="编辑设置" @close="resetEditData" align-center>
      <el-form :model="editForm" ref="editFormRef" label-position="left" label-width="auto">
        <el-form-item v-for="(field, index) in inputFields" :key="index" :label="field.label" v-show="!field.ignore">
          <el-select v-model="field.val" style="width: 240px" v-if="field.source">
            <el-option v-for="item in field.source" :key="item.val" :label="item.label" :value="item.val" />
          </el-select>
          <el-input v-else v-model="editForm[field.model]" :placeholder="`请输入${field.label}`" />
        </el-form-item>

        <el-table :data="editForm.configurations" style="width: 100%" stripe>
          <el-table-column label="是否使用" prop="isActive">
            <template #default="scope">
              <el-switch v-model="scope.row.isActive" />
            </template>
          </el-table-column>
          <el-table-column v-for="(column, index) in tableColumnsForConfig" :key="index" :label="column.label"
            :prop="column.prop" />
        </el-table>

      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="isEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, defineProps, reactive } from 'vue';

const props = defineProps([
  'searchConditions',
  'tableColumns',
  'settingsData',
  'actionColumns',
  'searchSettings',
  'editSetting',
  'copySetting',
  'deleteSetting',
  'applySetting',
  'inputFields',
  'tableColumnsForConfig',
]);
const searchFields = ref(props.searchConditions.map(field => ({ ...field, value: '' })));
const formatDate = (isoString) => {
  if (!isoString) return "";
  return isoString.replace("T", " ").split(".")[0];
}
const handleSearch = () => {
  const searchData = searchFields.value.reduce((acc, field) => {
    acc[field.model] = field.value;
    return acc;
  }, {});

  console.log('搜索条件:', searchData);
  props.searchSettings(searchData);
};
const isEditDialogVisible = ref(false);
const editForm = reactive({
  id: null,
  configurations: [],
});
const handleAction = (action, row) => {
  if (action.label == '编辑') {
    editSetting(row)
  } else if (action.label == '删除') {
    props.deleteSetting(row);
  } else if (action.label == '应用') {
    props.applySetting(row);
  } else {
  }
};

const editSetting = (row) => {
  editForm.id = row.id;
  props.inputFields.forEach(field => {
    editForm[field.model] = row[field.model] || '';
  });
  let configurations = []
  console.log(row)
  if (row.configurations) {
    configurations = JSON.parse(JSON.stringify(row.configurations));
  }
  editForm.configurations = configurations
  isEditDialogVisible.value = true;
};


const submitEdit = () => {
  props.editSetting(editForm);
  isEditDialogVisible.value = false;
  resetEditData();
};


const resetEditData = () => {
  editForm.id = null;
  editForm.name = '';
  editForm.configurations = [];
  props.inputFields.forEach(field => {
    editForm[field.model] = '';
  });
};

</script>