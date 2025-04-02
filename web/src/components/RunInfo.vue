<template>
    <el-container direction="vertical">
        <el-header
            style="display: flex; justify-content: flex-end; align-items: center; gap: 10px; padding-right: 40px;">
            <el-button type="success" @click="run" :disabled="taskStatus === 1 || taskStatus === 2">运行</el-button>
            <el-button type="warning" @click="togglePause" :disabled="taskStatus === 0 || taskStatus === 3">{{
                pauseButtonText }}</el-button>
            <el-button type="danger" @click="stop" :disabled="taskStatus === 0 || taskStatus === 3">停止</el-button>
            <el-button type="primary" @click="exportData"
                :disabled="taskStatus !== 0 && taskStatus !== 3">数据导出</el-button>
        </el-header>
        <el-main>
            <el-container>
                <el-aside width="64%">
                    <div ref="lineChart" style="height: 250px;"></div>
                    <div ref="pieChart" style="height: 250px;"></div>
                </el-aside>

                <el-main>
                    <el-table :data="tableData" border style="width: 100%">
                        <el-table-column prop="item" label="数据项目"></el-table-column>
                        <el-table-column prop="value" label="值"></el-table-column>
                    </el-table>
                </el-main>
            </el-container>
        </el-main>
    </el-container>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from "vue";
import * as echarts from "echarts";
import { fetchRunInfo, runTask, getTaskStatus, taskPause, taskResume, taskStop, getTaskResult } from "~/api/data";
import * as XLSX from "xlsx";
import { ElMessage } from 'element-plus';
const lineChart = ref(null);
const pieChart = ref(null);

const tableData = ref([
    { item: "CPU使用率", value: "0%" },
    { item: "磁盘占用", value: "0%" },
    { item: "内存占用", value: "0%" },
]);

const activeTab = ref("run");
const taskStatus = ref(0);
let intervalId = null;
let taskIntervalId = null;
const pauseButtonText = computed(() => (taskStatus.value === 2 ? "继续" : "暂停"));

const fetchStatus = async () => {
    try {
        const response = await getTaskStatus();
        taskStatus.value = response.status_code;
        if (taskStatus.value == 0 || taskStatus.value == 3 || taskStatus.value == 4) {
            stopDataFetching()
        }
    } catch (error) {
        console.error("Error fetching status:", error);
    }
};

const run = async () => {
    if (taskStatus.value === 1) return;
    try {
        const response = await runTask();
        taskStatus.value = response.status_code;
        startDataFetching();
    } catch (error) {
        console.error("Error starting task:", error);
    }
};

const togglePause = async () => {
    if (taskStatus.value === 1) {
        try {
            const response = await taskPause();
            taskStatus.value = response.status_code;
            stopDataFetching();
        } catch (error) {
            console.error("Error pausing task:", error);
        }
    } else if (taskStatus.value === 2) {
        try {
            const response = await taskResume();
            taskStatus.value = response.status_code;
            startDataFetching();
        } catch (error) {
            console.error("Error resuming task:", error);
        }
    }
};

const stop = async () => {
    if (taskStatus.value === 0 || taskStatus.value === 3) return;
    try {
        const response = await taskStop();
        taskStatus.value = response.status_code;
        stopDataFetching();
    } catch (error) {
        console.error("Error stopping task:", error);
    }
};

const exportData = async () => {
    if (taskStatus.value === 0 && taskStatus.value === 3) return;
    try {
        const response = await getTaskResult();
        const result = response.data;
        if (!result || !result.simulation_result) {
            return ElMessage.info("暂无结果可导出");
        }
        const headers = ["ID", "名称", "CPU", "GPU"];
        const data = {
            id: result.simulation_result.id,
            name: result.ipc_performances.map(item => item.ipc_config.name).join(", "),
            cpu: result.ipc_performances.map(item => item.ipc_config.cpu).join(", "),
            gpu: result.ipc_performances.map(item => item.ipc_config.gpus.join(", ")).join(", ")
        }
        const sheetData = [headers, ...data];
        console.log(sheetData)

        const worksheet = XLSX.utils.aoa_to_sheet(sheetData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");

        XLSX.writeFile(workbook, "data.xlsx");
    } catch (error) {
        console.error("Error get result task:", error);
    }

}
const initCharts = () => {
    if (
        !lineChart.value ||
        !pieChart.value ||
        lineChart.value.clientWidth === 0 ||
        pieChart.value.clientWidth === 0
    ) {
        setTimeout(initCharts, 100);
        return;
    }
    const currentTime = new Date().toISOString().substring(0, 19);
    const lineChartInstance = echarts.init(lineChart.value);
    lineChartInstance.setOption({
        title: {
            text: "资源使用情况",
            left: "center",
            textStyle: {
                fontWeight: "bold",
            },
        },
        tooltip: { trigger: "axis" },
        legend: { data: ["CPU", "磁盘"], top: "30" },
        xAxis: { type: "category", data: [currentTime] },
        yAxis: { type: "value" },
        series: [
            { name: "CPU", type: "line", data: [0] },
            { name: "磁盘", type: "line", data: [0] },
        ],
    });

    const pieChartInstance = echarts.init(pieChart.value);
    pieChartInstance.setOption({
        title: { text: "内存使用情况", left: "center" },
        tooltip: { trigger: "item" },
        legend: { bottom: 0 },
        series: [
            {
                name: "内存使用",
                type: "pie",
                radius: "50%",
                data: [{ value: 0, name: "已用" },
                { value: 100, name: "空闲" },],
            },
        ],
        label: {
            show: true,
            position: "inside",
            formatter: "{b}: {c}%",
            fontSize: 14,
            fontWeight: "bold",
        },
    });
    updateChartsData()
};
const MAX_DATA_POINTS = 10;
const updateChartsData = async () => {
    try {
        const data = await fetchRunInfo();
        const { cpuData, diskData, memoryData, timeData } = data.data;
        if (!window.chartData) {
            window.chartData = {
                cpu: [],
                disk: [],
                time: [],
            };
        }
        const latestTime = timeData;
        window.chartData.cpu.push(cpuData.at(-1));
        window.chartData.disk.push(diskData.at(-1));
        window.chartData.time.push(latestTime);
        if (window.chartData.cpu.length > MAX_DATA_POINTS) {
            window.chartData.cpu.shift();
            window.chartData.disk.shift();
            window.chartData.time.shift();
        }

        if (lineChart.value) {
            const lineChartInstance = echarts.getInstanceByDom(lineChart.value);
            if (lineChartInstance) {
                lineChartInstance.setOption({
                    xAxis: { type: "category", data: window.chartData.time },
                    series: [
                        { name: "CPU", type: "line", data: window.chartData.cpu },
                        { name: "磁盘", type: "line", data: window.chartData.disk },
                    ],
                });
            }
        }
        if (pieChart.value) {
            const pieChartInstance = echarts.getInstanceByDom(pieChart.value);
            if (pieChartInstance) {
                pieChartInstance.setOption({
                    series: [
                        {
                            name: "内存使用",
                            type: "pie",
                            radius: "50%",
                            data: memoryData,
                        },
                    ],
                });
            }
        }

        tableData.value = [
            { item: "CPU使用率", value: `${cpuData[cpuData.length - 1]}%` },
            { item: "磁盘占用", value: `${diskData[diskData.length - 1]}%` },
            { item: "内存占用", value: `${memoryData[0].value}%` },
        ];
    } catch (error) {
        ElMessage.error("获取数据失败:" + error.response.data.detail);
    }
};

const startDataFetching = () => {
    if ((taskStatus.value === 1 || taskStatus.value === 2) && !intervalId && !taskIntervalId) {
        intervalId = setInterval(updateChartsData, 2000);
        taskIntervalId = setInterval(fetchStatus, 2000);
    }
};

const stopDataFetching = () => {
    if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
    }
    if (taskIntervalId) {
        clearInterval(taskIntervalId);
        taskIntervalId = null;
    }
};

onMounted(() => {
    fetchStatus();
    nextTick(() => {
        initCharts();
    });
});
</script>

<style scoped>
.el-header {
    background: #f5f5f5;
    padding: 10px;
    text-align: right;
}

.el-main {
    padding: 10px;
}

.el-aside {
    border-right: 1px solid #ddd;
    padding: 10px;
}
</style>