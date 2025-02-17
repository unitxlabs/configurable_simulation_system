<template>
  <div class="sidebar">
    <!-- 循环生成菜单项，并绑定点击事件 -->
    <div
      class="menu-item"
      v-for="item in menuItems"
      :key="item"
      @click="navigateTo(item)"
    >
      {{ item }}
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'; // 引入 vue-router 的 hook

export default {
  name: 'Sidebar',
  setup() {
    const router = useRouter();  // 获取路由实例

    // 菜单项数组
    const menuItems = [
      '数据', '设置', '控制器', '通讯', '飞拍', '定拍', '运行', '日志', 'IPC配置'
    ];

    // 导航到对应的路由
    const navigateTo = (item) => {
      switch (item) {
        case '数据':
          router.push('/data');  // 跳转到数据页面
          break;
        case '设置':
          router.push('/settings');
          break;
        case '控制器':
          router.push('/controller');
          break;
        case '通讯':
          router.push('/communication');
          break;
        case '飞拍':
          router.push('/fly-capture');
          break;
        case '定拍':
          router.push('/fixed-capture');
          break;
        case '运行':
          router.push('/running');
          break;
        case '日志':
          router.push('/logs');
          break;
        case 'IPC配置':
          router.push('/ipc-config');
          break;
        default:
          break;
      }
    };

    return {
      menuItems,
      navigateTo
    };
  },
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
</style>
