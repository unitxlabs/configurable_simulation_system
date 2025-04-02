<script lang="ts" setup>
import {
  Document,
  Menu as IconMenu,
  Location,
  Setting,
} from '@element-plus/icons-vue'

// const isCollapse = ref(true)
function handleOpen(key: string, keyPath: string[]) {
  // eslint-disable-next-line no-console
  console.log(key, keyPath)
}
function handleClose(key: string, keyPath: string[]) {
  // eslint-disable-next-line no-console
  console.log(key, keyPath)
}
</script>

<template>
  <el-menu router default-active="1" class="el-menu-vertical-demo" @open="handleOpen" @close="handleClose">
    <el-menu-item index="/nav/data">
      <el-icon>
        <IconMenu />
      </el-icon>
      <template #title>
        数据
      </template>
    </el-menu-item>
    <el-sub-menu index="1">
      <template #title>
        <el-icon>
          <Location />
        </el-icon>
        <span>设置</span>
      </template>
      <el-menu-item index="/nav/controller">
        控制器
      </el-menu-item>
      <el-menu-item index="/nav/workstation">
        工位
      </el-menu-item>
      <el-menu-item index="/nav/flying_shoot">
        飞拍
      </el-menu-item>
      <el-menu-item index="/nav/fixed_shoot">
        定拍
      </el-menu-item>
    </el-sub-menu>

    <el-menu-item index="/nav/run">
      <el-icon>
        <Document />
      </el-icon>
      <template #title>
        运行
      </template>
    </el-menu-item>
    <el-menu-item index="/nav/log">
      <el-icon>
        <Setting />
      </el-icon>
      <template #title>
        日志
      </template>
    </el-menu-item>
    <el-menu-item index="/nav/info">
      <el-icon>
        <Setting />
      </el-icon>
      <template #title>
        IPC配置
      </template>
    </el-menu-item>
  </el-menu>
</template>
