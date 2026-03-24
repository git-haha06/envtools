<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="sidebar-title">
          <h1>EnvTools</h1>
          <p>{{ t('sidebar.subtitle') }}</p>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/">
          <el-icon><Odometer /></el-icon>
          {{ t('nav.dashboard') }}
        </router-link>
        <router-link to="/environments">
          <el-icon><Box /></el-icon>
          {{ t('nav.environments') }}
        </router-link>
        <router-link to="/install">
          <el-icon><Download /></el-icon>
          {{ t('nav.install') }}
        </router-link>
        <router-link to="/env-vars">
          <el-icon><Setting /></el-icon>
          {{ t('nav.envVars') }}
        </router-link>
        <router-link to="/settings">
          <el-icon><Tools /></el-icon>
          {{ t('nav.settings') }}
        </router-link>
      </nav>
      <div class="sidebar-footer">v0.1.0</div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useI18nStore } from '../i18n'
const { t } = useI18nStore()
</script>
