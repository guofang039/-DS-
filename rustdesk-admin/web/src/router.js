import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Layout from './views/Layout.vue'
import Dashboard from './views/Dashboard.vue'
import Users from './views/Users.vue'
import Devices from './views/Devices.vue'
import Audit from './views/Audit.vue'
import Update from './views/Update.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'users', component: Users },
      { path: 'devices', component: Devices },
      { path: 'audit', component: Audit },
      { path: 'update', component: Update }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
