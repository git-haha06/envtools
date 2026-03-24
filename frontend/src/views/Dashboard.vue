<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('dashboard.title') }}</h1>
        <p>{{ t('dashboard.subtitle') }}</p>
      </div>
      <el-button :loading="store.scanning" @click="refresh">
        <el-icon v-if="!store.scanning"><Refresh /></el-icon>
        {{ store.scanning ? t('dashboard.scanning') : t('dashboard.refresh') }}
      </el-button>
    </div>

    <div class="stat-cards">
      <el-card shadow="hover">
        <div class="stat-card">
          <div class="stat-value">{{ totalCount }}</div>
          <div class="stat-label">{{ t('dashboard.totalInstalled') }}</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-card runtime">
          <div class="stat-value">{{ runtimeCount }}</div>
          <div class="stat-label">{{ t('dashboard.runtimes') }}</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-card database">
          <div class="stat-value">{{ databaseCount }}</div>
          <div class="stat-label">{{ t('dashboard.databases') }}</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-card devtool">
          <div class="stat-value">{{ devToolCount }}</div>
          <div class="stat-label">{{ t('dashboard.devTools') }}</div>
        </div>
      </el-card>
    </div>

    <el-card class="section-card" v-if="store.systemInfo">
      <template #header>{{ t('dashboard.systemInfo') }}</template>
      <div class="system-info-grid">
        <div class="system-info-item">
          <span class="label">{{ t('dashboard.os') }}</span>
          <span class="value">{{ store.systemInfo.os }}</span>
        </div>
        <div class="system-info-item">
          <span class="label">{{ t('dashboard.version') }}</span>
          <span class="value">{{ store.systemInfo.os_version }}</span>
        </div>
        <div class="system-info-item">
          <span class="label">{{ t('dashboard.arch') }}</span>
          <span class="value">{{ store.systemInfo.arch }}</span>
        </div>
        <div class="system-info-item">
          <span class="label">{{ t('dashboard.hostname') }}</span>
          <span class="value">{{ store.systemInfo.hostname }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="section-card">
      <template #header>{{ t('dashboard.detectedEnvs') }}</template>
      <div v-if="store.scanning" class="empty-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>{{ t('dashboard.scanningSystem') }}</p>
      </div>
      <div v-else-if="allEnvs.length === 0" class="empty-state">
        <el-icon><Box /></el-icon>
        <p>{{ t('dashboard.noEnvsDetected') }}</p>
        <el-button type="primary" style="margin-top: 12px" @click="$router.push('/install')">
          {{ t('dashboard.goToInstall') }}
        </el-button>
      </div>
      <div v-else class="env-grid">
        <div v-for="env in allEnvs" :key="env.id" class="env-item">
          <div :class="['env-icon', env.category]">
            <el-icon v-if="env.category === 'Runtime'"><Cpu /></el-icon>
            <el-icon v-else-if="env.category === 'Database'"><Coin /></el-icon>
            <el-icon v-else-if="env.category === 'DevTool'"><SetUp /></el-icon>
            <el-icon v-else><Box /></el-icon>
          </div>
          <div class="env-info">
            <div class="name">
              {{ env.display_name }}
              <el-tag v-if="env.version" size="small" type="info" style="margin-left: 6px">
                {{ env.version }}
              </el-tag>
            </div>
            <div class="path">{{ env.path || t('dashboard.systemPath') }}</div>
          </div>
          <el-tag v-if="env.in_path" size="small" type="success">PATH</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useI18nStore } from '../i18n'

const store = useAppStore()
const { t } = useI18nStore()

const allEnvs = computed(() => [...store.environments, ...store.manualEnvs])
const totalCount = computed(() => allEnvs.value.length)
const runtimeCount = computed(() => allEnvs.value.filter(e => e.category === 'Runtime').length)
const databaseCount = computed(() => allEnvs.value.filter(e => e.category === 'Database').length)
const devToolCount = computed(() => allEnvs.value.filter(e => e.category === 'DevTool').length)

async function refresh() {
  await Promise.all([store.scanEnvironments(), store.loadSystemInfo(), store.loadManualEnvs()])
}

onMounted(refresh)
</script>
