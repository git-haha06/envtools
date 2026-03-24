<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('install.title') }}</h1>
        <p>{{ t('install.subtitle') }}</p>
      </div>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="search"
        :placeholder="t('install.search')"
        :prefix-icon="SearchIcon"
        clearable
        style="max-width: 300px"
      />
      <el-select v-model="categoryFilter" style="width: 160px">
        <el-option value="all" :label="t('install.allCategories')" />
        <el-option value="runtime" :label="t('envs.runtime')" />
        <el-option value="database" :label="t('envs.database')" />
        <el-option value="devtool" :label="t('envs.devtool')" />
        <el-option value="sdk" :label="t('envs.sdk')" />
      </el-select>
    </div>

    <div v-if="filtered.length === 0" class="empty-state">
      <el-icon><Download /></el-icon>
      <p>{{ t('install.noPackages') }}</p>
      <p style="font-size: 12px; margin-top: 4px">
        {{ search ? t('install.tryDifferent') : t('install.noRegistry') }}
      </p>
    </div>

    <div v-else class="pkg-grid">
      <el-card v-for="pkg in filtered" :key="pkg.package.name" shadow="hover">
        <div class="pkg-card">
          <div :class="['env-icon', categoryClass(pkg.package.category)]">
            <el-icon v-if="pkg.package.category === 'runtime'"><Cpu /></el-icon>
            <el-icon v-else-if="pkg.package.category === 'database'"><Coin /></el-icon>
            <el-icon v-else-if="pkg.package.category === 'devtool'"><SetUp /></el-icon>
            <el-icon v-else><Box /></el-icon>
          </div>
          <div style="flex: 1; min-width: 0">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px">
              <span style="font-weight: 600; font-size: 14px">{{ pkg.package.display_name }}</span>
              <el-icon v-if="isInstalled(pkg.package.name)" color="#22c55e"><CircleCheck /></el-icon>
            </div>
            <p style="font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden">
              {{ pkg.package.description }}
            </p>
            <div style="display: flex; gap: 6px; margin-bottom: 10px">
              <el-tag size="small" type="info">{{ pkg.versions.recommended }}</el-tag>
              <el-tag size="small">{{ pkg.package.category }}</el-tag>
            </div>
            <div style="display: flex; gap: 8px">
              <el-button
                size="small" type="primary"
                :loading="store.installing === pkg.package.name"
                @click="openInstallDialog(pkg)"
              >
                <el-icon><Download /></el-icon>
                {{ isInstalled(pkg.package.name) ? t('install.reinstall') : t('install.installBtn') }}
              </el-button>
              <el-button
                v-if="pkg.package.website"
                size="small" text
                @click="openUrl(pkg.package.website)"
              >
                <el-icon><Link /></el-icon>
                {{ t('install.website') }}
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Install Dialog -->
    <el-dialog v-model="showDialog" :title="`${t('install.installTitle')} ${selectedPkg?.package?.display_name || ''}`" width="480px">
      <template v-if="selectedPkg">
        <p style="color: var(--el-text-color-secondary); font-size: 14px; margin-bottom: 16px">
          {{ selectedPkg.package.description }}
        </p>
        <el-form label-position="top">
          <el-form-item :label="t('install.version')">
            <el-select v-model="selectedVersion" style="width: 100%">
              <el-option
                v-for="v in selectedPkg.versions.available" :key="v" :value="v"
                :label="`${v}${v === selectedPkg.versions.recommended ? ` (${t('install.recommended')})` : ''}`"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <div style="display: flex; align-items: center; justify-content: space-between; width: 100%">
              <span>{{ t('install.useMirror') }}</span>
              <el-switch v-model="useMirror" />
            </div>
            <div v-if="useMirror" style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px">
              {{ t('install.mirrorHint') }}
            </div>
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showDialog = false">{{ t('install.cancel') }}</el-button>
        <el-button type="primary" :loading="!!store.installing" @click="handleInstall">
          <el-icon><Download /></el-icon>
          {{ t('install.installBtn') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search as SearchIcon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores/app'
import { useI18nStore } from '../i18n'

const store = useAppStore()
const { t } = useI18nStore()

const search = ref('')
const categoryFilter = ref('all')
const showDialog = ref(false)
const selectedPkg = ref(null)
const selectedVersion = ref('')
const useMirror = ref(false)

const installedIds = computed(() => new Set(store.environments.map(e => e.id)))

const filtered = computed(() => {
  return store.packages.filter(pkg => {
    const s = search.value.toLowerCase()
    const matchSearch = pkg.package.display_name.toLowerCase().includes(s) ||
      pkg.package.name.toLowerCase().includes(s) ||
      pkg.package.description.toLowerCase().includes(s)
    const matchCategory = categoryFilter.value === 'all' || pkg.package.category === categoryFilter.value
    return matchSearch && matchCategory
  })
})

function categoryClass(cat) {
  const map = { runtime: 'Runtime', database: 'Database', devtool: 'DevTool', sdk: 'SDK' }
  return map[cat] || 'SDK'
}

function isInstalled(name) { return installedIds.value.has(name) }
function openUrl(url) { window.open(url, '_blank') }

function openInstallDialog(pkg) {
  selectedPkg.value = pkg
  selectedVersion.value = pkg.versions.recommended
  useMirror.value = store.config?.use_mirror || false
  showDialog.value = true
}

async function handleInstall() {
  if (!selectedPkg.value || !selectedVersion.value) return
  try {
    await store.installPackage(selectedPkg.value.package.name, selectedVersion.value, useMirror.value)
    ElMessage.success(`${selectedPkg.value.package.display_name} ${selectedVersion.value} ${t('install.installSuccess')}`)
    showDialog.value = false
  } catch (e) {
    ElMessage.error(`${t('install.installFailed')}: ${e}`)
  }
}

onMounted(async () => {
  await Promise.all([store.loadPackages(), store.loadConfig(), store.scanEnvironments()])
})
</script>
