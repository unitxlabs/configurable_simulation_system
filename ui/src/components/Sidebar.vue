<template>
  <div class="sidebar">
    <!-- 循环生成菜单项，并绑定点击事件 -->
    <div
      v-for="(item, index) in menuItems"
      :key="index"
      class="menu-item"
    >
      <!-- 如果是“设置”，则显示子菜单 -->
      <div @click="navigateTo(item)">
        {{ item.name }}
      </div>

      <!-- 子菜单，只有在点击“设置”时展开 -->
      <div v-if="item.name === '设置' && isSettingsOpen" class="submenu">
        <div
          class="submenu-item"
          v-for="subItem in settingsSubMenu"
          :key="subItem.name"
          @click.stop="navigateTo(subItem)"
        >
          {{ subItem.name }}
        </div>
      </div>

      <!-- 子菜单，只有在点击“通讯”时展开 -->
      <div v-if="item.name === '通讯' && isCommunicationOpen" class="submenu">
        <div
          class="submenu-item"
          v-for="subItem in communicationSubMenu"
          :key="subItem.name"
          @click.stop="navigateTo(subItem)"
        >
          {{ subItem.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'; // 引入 ref 来声明响应式变量
import { useRouter } from 'vue-router';

export default {
  name: 'Sidebar',
  setup() {
    const router = useRouter(); // 获取路由实例

    // 菜单项数组
    const menuItems = [
      { name: '数据', route: '/data' },
      { name: '设置', route: '' }, // "设置"项没有直接路由，点击时展开子菜单
      { name: '运行', route: '/running' },
      { name: '日志', route: '/logs' },
      { name: 'IPC配置', route: '/ipc-config' }
    ];

    // 设置子菜单项
    const settingsSubMenu = [
      { name: '控制器', route: '/controller' },
      { name: '飞拍', route: '/fly-capture' },
      { name: '定拍', route: '/fixed-capture' }
    ];


    // 控制“设置”和“通讯”菜单的展开与折叠
    const isSettingsOpen = ref(false);
    const isCommunicationOpen = ref(false);

    // 点击菜单项进行路由导航
const navigateTo = (item) => {
  if (item.name === '通讯') {
    // 切换“通讯”子菜单的展开与折叠
    isCommunicationOpen.value = !isCommunicationOpen.value;
  } else if (item.name === '设置') {
    // 切换“设置”子菜单的展开与折叠
    isSettingsOpen.value = !isSettingsOpen.value;
  }

  // 路由跳转，放在切换子菜单状态之后
  if (item.route) {
    router.push(item.route);
  }
};
    return {
      menuItems,
      navigateTo,
      settingsSubMenu,
      isSettingsOpen,
      isCommunicationOpen
    };
  }
};
</script>

<style scoped>
.sidebar {
  width: 200px;
  background-color: #f0f0f0;
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.menu-item {
  padding: 10px;
  border-bottom: 1px solid #ccc;
  cursor: pointer;
}

.menu-item:hover {
  background-color: #e0e0e0;
}

.submenu {
  margin-top: 10px;
  padding-left: 20px;
}

.submenu-item {
  padding: 8px;
  border-bottom: 1px solid #ddd;
  cursor: pointer;
}

.submenu-item:hover {
  background-color: #e0e0e0;
}
</style>
