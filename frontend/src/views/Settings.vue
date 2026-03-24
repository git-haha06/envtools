<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('settings.title') }}</h1>
        <p>{{ t('settings.subtitle') }}</p>
      </div>
      <el-button type="primary" :loading="saving" @click="handleSave">
        <el-icon><Check /></el-icon>
        {{ t('settings.save') }}
      </el-button>
    </div>

    <div v-if="!localConfig" class="empty-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>{{ t('settings.loading') }}</p>
    </div>

    <template v-else>
      <!-- General Settings -->
      <el-card class="section-card">
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px">
            <el-icon><Setting /></el-icon>
            {{ t('settings.general') }}
          </div>
        </template>
        <div style="display: flex; flex-direction: column; gap: 20px">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="font-size: 14px; font-weight: 500">{{ t('settings.mirrorDefault') }}</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px">
                {{ t('settings.mirrorDefaultDesc') }}
              </div>
            </div>
            <el-switch v-model="localConfig.use_mirror" />
          </div>
          <el-divider style="margin: 0" />
          <div>
            <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px">{{ t('settings.installDir') }}</div>
            <el-input v-model="localConfig.install_dir" />
            <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px">
              {{ t('settings.installDirDesc') }}
            </div>
          </div>
          <el-divider style="margin: 0" />
          <div>
            <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px">{{ t('settings.theme') }}</div>
            <el-select v-model="localConfig.theme" style="width: 200px">
              <el-option value="system" :label="t('settings.themeSystem')" />
              <el-option value="light" :label="t('settings.themeLight')" />
              <el-option value="dark" :label="t('settings.themeDark')" />
            </el-select>
          </div>
          <el-divider style="margin: 0" />
          <div>
            <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px">{{ t('settings.language') }}</div>
            <el-select v-model="localConfig.language" style="width: 200px" @change="handleLanguageChange">
              <el-option value="zh-CN" :label="t('settings.langZh')" />
              <el-option value="en" :label="t('settings.langEn')" />
            </el-select>
          </div>
        </div>
      </el-card>

      <!-- Mirror Sources -->
      <el-card class="section-card">
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px">
            <el-icon><Connection /></el-icon>
            {{ t('settings.mirrorSources') }}
          </div>
        </template>
        <div v-if="store.mirrorConfigs.length === 0" class="empty-state">
          <p>{{ t('settings.noMirrors') }}</p>
        </div>
        <div v-for="m in store.mirrorConfigs" :key="m.name" class="mirror-item">
          <div style="display: flex; align-items: center; gap: 8px">
            <h4>{{ m.display_name }}</h4>
            <el-tag v-if="m.current_source" size="small" type="success">{{ t('settings.active') }}</el-tag>
          </div>
          <div v-if="m.current_source" class="mirror-url">{{ m.current_source }}</div>
          <div style="display: flex; gap: 8px; margin-top: 8px">
            <el-button size="small" @click="handleSwitchMirror(m.name, m.official_source)">
              {{ t('settings.official') }}
            </el-button>
            <el-button size="small" @click="handleSwitchMirror(m.name, m.mirror_source)">
              <el-icon><Switch /></el-icon>
              {{ t('settings.mirror') }}
            </el-button>
          </div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores/app'
import { useI18nStore } from '../i18n'

const store = useAppStore()
const i18n = useI18nStore()
const { t } = i18n

const localConfig = ref(null)
const saving = ref(false)

watch(() => store.config, (cfg) => {
  if (cfg) localConfig.value = { ...cfg }
}, { immediate: true })

function handleLanguageChange(val) {
  i18n.setLocale(val)
}

async function handleSave() {
  if (!localConfig.value) return
  saving.value = true
  try {
    await store.saveConfig(localConfig.value)
    ElMessage.success(t('settings.saved'))
  } catch (e) {
    ElMessage.error(`${t('settings.saveFailed')}: ${e}`)
  } finally {
    saving.value = false
  }
}

async function handleSwitchMirror(name, url) {
  try {
    await store.setMirrorSource(name, url)
    ElMessage.success(`${name} ${t('settings.sourceUpdated')}`)
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

onMounted(async () => {
  await Promise.all([store.loadConfig(), store.loadMirrorConfigs()])
})
</script>
