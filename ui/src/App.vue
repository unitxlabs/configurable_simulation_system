<template>
  <div id="app">
    <Sidebar />
    <router-view /> <!-- 路由视图 -->
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue';

export default {
  name: 'App',
  components: {
    Sidebar,
  },
};
</script>

<style>
#app {
  display: flex;
  height: 100vh;
}
</style>
