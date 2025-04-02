<template>
    <el-container direction="vertical" style="padding: 20px">
        <el-tabs v-model="activeTab" type="border-card" @tab-click="handleTabClick">
            <el-tab-pane label="设置" name="config">
                <RunSettingsForm title="控制器设置" :tableColumnsForConfig="tableColumnsForControllerConfig"
                    :inputFields="controllerInputFields" :settingsData="controllerSettingsData" />
                <RunSettingsForm style="margin-top: 40px;" title="通讯设置"
                    :tableColumnsForConfig="tableColumnsForCommunicationConfig" :inputFields="inputFields"
                    :settingsData="communicationSettingsData" />
            </el-tab-pane>

            <el-tab-pane label="运行" name="run">
                <RunInfo ref="runInfoComponent"></RunInfo>
            </el-tab-pane>
        </el-tabs>
    </el-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { fetchApplyCommunicationSettingData } from "~/api/data";
import { ElMessage } from 'element-plus';
const activeTab = ref("config");
const handleTabClick = (tab) => {
    if (tab.name === "run") {
        const runInfoComponent = $refs.runInfoComponent;
        if (runInfoComponent) {
            runInfoComponent.initCharts();
        }
    }
};
const controllerInputFields = ref([]);
const tableColumnsForControllerConfig = ref([
    { label: '控制器 ID', prop: 'controller_id' },
    { label: '控制器版本', prop: 'controller_version' },
    { label: '相机', prop: 'cameras_id' },
    { label: '相机分辨率', prop: 'resolution' },
]);
const inputFields = ref([
    { label: '设置名', model: 'name' },
    { label: '物料类型', model: 'part_type' },
    { label: '物料时间间隔(s)', model: 'part_interval' },
    { label: 'part start到第一个工位的时间间隔(s)', model: 'part_start_to_ws1_interval' },
    { label: '创建时间', model: 'create_time' },
    { label: '修改时间', model: 'modified_time' },
]);

const tableColumnsForCommunicationConfig = ref([
    { label: '控制器ID', prop: 'controller_config_id' },
    { label: '到下一个工位的时间(ms)', prop: 'to_next_ws_offset' },
    { label: 'sequence数量', prop: 'sequence_count' },
    { label: 'sequence之间的间隔', prop: 'sequences_interval' },
    { label: '相机复位时间', prop: 'camera_reset_time' },
]);
const controllerSettingsData = ref([]);
const communicationSettingsData = ref([]);
onMounted(() => {
    fetchApplyConfig();
});
const fetchApplyConfig = async () => {
    try {
        const data = await fetchApplyCommunicationSettingData();
        if (data && data.data) {
            const { communication_config, workstation_configs } = data.data;
            if (communication_config.communication_step) {
                inputFields.value.splice(4, 0,
                    { label: '握手步数', model: 'communication_step' },)
            }
            inputFields.value.forEach(field => {
                if (field.model in communication_config) {
                    field.val = communication_config[field.model];
                }
            });

            controllerSettingsData.value = workstation_configs.map(ws => {
                const isActive = communication_config.workstation_config_ids.includes(ws.workstation_config.id) &&
                    communication_config.workstations_in_use[communication_config.workstation_config_ids.indexOf(ws.workstation_config.id)];

                return {
                    controller_id: ws.controller_config.controller_id,
                    controller_version: ws.controller_config.controller_version,
                    cameras_id: ws.controller_config.cameras_id.join(", "),
                    resolution: `${ws.controller_config.image_width}x${ws.controller_config.image_height}`,
                    isActive: isActive,
                };
            });

            communicationSettingsData.value = workstation_configs.map(ws => {
                const isActive = communication_config.workstation_config_ids.includes(ws.workstation_config.id) &&
                    communication_config.workstations_in_use[communication_config.workstation_config_ids.indexOf(ws.workstation_config.id)];
                return {
                    controller_config_id: ws.controller_config.id,
                    to_next_ws_offset: ws.workstation_config.to_next_ws_offset,
                    sequence_count: ws.workstation_config.sequence_count,
                    camera_reset_time: ws.workstation_config.camera_reset_time,
                    sequences_interval: ws.workstation_config.sequences_interval.join(", "),
                    isActive: isActive,
                };
            });
        }
    } catch (error) {
        ElMessage.error("获取数据失败:" + error.response.data.detail);
    }
};
</script>
