<template>
    <el-container direction="vertical" style="padding: 20px;">
        <el-card>
            <el-button type="primary" @click="handleAdd">新增</el-button>
        </el-card>

        <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑' : '新增'">
            <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
                <el-form-item label="工位ID" prop="workstation_id">
                    <el-input v-model.number="form.workstation_id" type="number" />
                </el-form-item>
                <el-form-item label="控制器ID">
                    <el-select v-model="form.controller_config_id" placeholder="请选择控制器" @focus="fetchCameraSelectData"
                        :loading="loading">
                        <el-option v-for="item in controllerOptions" :key="item.value" :label="item.label"
                            :value="item.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="到下一工位时间">
                    <el-input v-model="form.to_next_ws_offset" type="number" />
                </el-form-item>
                <el-form-item label="Sequence 数量">
                    <el-input v-model="form.sequence_count" type="number" />
                </el-form-item>
                <el-form-item label="相机复位时间">
                    <el-input v-model="form.camera_reset_time" type="number" />
                </el-form-item>
                <el-form-item label="Sequences ID">
                    <el-input v-model="sequences_id_input" placeholder="用逗号分隔" />
                </el-form-item>
                <el-form-item label="Sequences 之间的间隔">
                    <el-input v-model="sequences_interval_input" placeholder="用逗号分隔" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSave">保存</el-button>
            </template>
        </el-dialog>

        <el-card style="margin-top: 20px; flex: 1;">
            <el-table :data="tableData" border style="width: 100%">
                <el-table-column prop="workstation_config.workstation_id" label="工位ID" width="80" />
                <el-table-column prop="workstation_config.to_next_ws_offset" label="到下一工位时间" />
                <el-table-column prop="workstation_config.controller_config_id" label="控制器ID">
                    <template #default="{ row }">
                        {{ getControllerLabel(row.workstation_config.controller_config_id) }}
                    </template>
                </el-table-column>
                <el-table-column prop="workstation_config.sequence_count" label="Sequence 数量" />
                <el-table-column prop="workstation_config.camera_reset_time" label="相机复位时间" />
                <el-table-column prop="workstation_config.sequences_id" label="Sequences IDs">
                    <template #default="{ row }">
                        {{ row.workstation_config.sequences_id.join(', ') }}
                    </template>
                </el-table-column>
                <el-table-column prop="workstation_config.sequences_interval" label="Sequences 之间的间隔">
                    <template #default="{ row }">
                        {{ row.workstation_config.sequences_interval.join(', ') }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="180">
                    <template #default="{ row }">
                        <el-button @click="handleEdit(row)">编辑</el-button>
                        <el-button type="danger" @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
    </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { fetchCameraSelect, fetchSaveWorkStationInfo, saveNewWorkStationSettingData, updateNewWorkStationSettingData, deleteWorkStationSettingData } from "~/api/data";

const tableData = ref([]);
const controllerOptions = ref([]);
const allControllerOptions = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref(null);
const form = ref({ workstation_id: null });
const sequences_id_input = ref('');
const sequences_interval_input = ref('');

onMounted(() => {
    fetchWorkStationData('');
    fetchCameraSelectAllData();
});

const getControllerLabel = (configId) => {
    const match = allControllerOptions.value.find((item) => item.value === configId);
    return match ? match.label : "未知控制器";
};

const fetchWorkStationData = async (query) => {
    try {
        const data = await fetchSaveWorkStationInfo(query);
        tableData.value = data.data;
    } catch (error) {
        ElMessage.error("获取数据失败:" + error.response.data.detail);
    }
};
const loading = ref(false);
const fetchCameraSelectData = async () => {
    if (controllerOptions.value.length > 0) return;
    loading.value = true
    try {
        const data = await fetchCameraSelect('online');
        controllerOptions.value = data.data;
    } catch (error) {
        ElMessage.error("获取数据失败:" + error.response.data.detail);
    } finally {
        loading.value = false
    }
};
const fetchCameraSelectAllData = async () => {
    try {
        const data = await fetchCameraSelect('');
        allControllerOptions.value = data.data;
    } catch (error) {
        ElMessage.error("获取数据失败:" + error.response.data.detail);
    }
};
const handleDelete = async (setting) => {
    if (setting.id && setting.workstation_id) {
        await deleteWorkStationSettingData(`?id=${setting.id}&workstation_id=${setting.workstation_id}`);
        fetchWorkStationData('');
    }
};

const rules = ref({
    workstation_id: [
        { required: true, message: "工位ID不能为空", trigger: "blur" },
        { type: "number", min: 1, max: 6, message: "工位ID必须是1-6之间的数字", trigger: "blur" },
        {
            validator: (rule, value, callback) => {
                if (!value || value < 1 || value > 6) {
                    callback(new Error("工位ID必须是1-6之间的数字"));
                } else if (tableData.value.some(item => item.workstation_config.workstation_id === value && !isEdit.value)) {
                    callback(new Error("工位ID已存在"));
                } else {
                    callback();
                }
            },
            trigger: "blur"
        }
    ]
});

const handleAdd = () => {
    form.value = { workstation_id: null, controller_config_id: '', sequence_count: '', camera_reset_time: '', to_next_ws_offset: '', sequences_id: [], sequences_interval: [] };
    sequences_id_input.value = '';
    sequences_interval_input.value = '';
    isEdit.value = false;
    dialogVisible.value = true;
};

const handleEdit = (row) => {
    form.value = { ...row.workstation_config };
    sequences_id_input.value = row.workstation_config.sequences_id.join(', ');
    sequences_interval_input.value = row.workstation_config.sequences_interval.join(', ');
    isEdit.value = true;
    dialogVisible.value = true;
};

const handleSave = async () => {
    await formRef.value.validate(async (valid) => {
        if (!valid) return;

        form.value.sequences_id = sequences_id_input.value.split(',').map((i) => i.trim());
        form.value.sequences_interval = sequences_interval_input.value.split(',').map((i) => i.trim());

        try {
            if (isEdit.value) {
                await updateNewWorkStationSettingData({ ...form.value });
                ElMessage.success("修改成功");
            } else {
                await saveNewWorkStationSettingData({ ...form.value });
                ElMessage.success("新增成功");
            }
            fetchWorkStationData('');
            dialogVisible.value = false;
        } catch (error) {
            ElMessage.error("新增失败");
        }
    });
};
</script>
