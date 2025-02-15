import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../pages/HomePage.vue'; 
import DataPage from '../pages/DataPage.vue';
import SettingsPage from '../pages/SettingsPage.vue';
import ControllerPage from '../pages/ControllerPage.vue';
import CommunicationPage from '../pages/CommunicationPage.vue';
import FlyCapturePage from '../pages/FlyCapturePage.vue';
import FixedCapturePage from '../pages/FixedCapturePage.vue';
import RunningPage from '../pages/RunningPage.vue';
import LogsPage from '../pages/LogsPage.vue';
import IpcConfigPage from '../pages/IpcConfigPage.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage, 
  },
  {
    path: '/data',
    name: 'data',
    component: DataPage,
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsPage,
  },
  {
    path: '/controller',
    name: 'controller',
    component: ControllerPage,
  },
  {
    path: '/communication',
    name: 'communication',
    component: CommunicationPage,
  },
  {
    path: '/fly-capture',
    name: 'flyCapture',
    component: FlyCapturePage,
  },
  {
    path: '/fixed-capture',
    name: 'fixedCapture',
    component: FixedCapturePage,
  },
  {
    path: '/running',
    name: 'running',
    component: RunningPage,
  },
  {
    path: '/logs',
    name: 'logs',
    component: LogsPage,
  },
  {
    path: '/ipc-config',
    name: 'ipcConfig',
    component: IpcConfigPage,
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;

