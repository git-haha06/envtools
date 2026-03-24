<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('envs.title') }}</h1>
        <p>{{ t('envs.subtitle') }}</p>
      </div>
      <el-button :loading="store.scanning" @click="store.scanEnvironments()">
        <el-icon v-if="!store.scanning"><Refresh /></el-icon>
        {{ t('envs.rescan') }}
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="search"
        :placeholder="t('envs.search')"
        :prefix-icon="Search"
        clearable
        style="max-width: 300px"
      />
      <el-radio-group v-model="categoryFilter" size="default">
        <el-radio-button value="all">{{ t('envs.all') }}</el-radio-button>
        <el-radio-button value="Runtime">{{ t('envs.runtime') }}</el-radio-button>
        <el-radio-button value="Database">{{ t('envs.database') }}</el-radio-button>
        <el-radio-button value="DevTool">{{ t('envs.devtool') }}</el-radio-button>
        <el-radio-button value="SDK">{{ t('envs.sdk') }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-tabs v-model="activeTab">
      <!-- Detected Tab -->
      <el-tab-pane :label="`${t('envs.detected')} (${filteredDetected.length})`" name="detected">
        <div v-if="filteredDetected.length === 0" class="empty-state">
          <el-icon><Box /></el-icon>
          <p>{{ t('envs.noEnvsFound') }}</p>
        </div>
        <div v-else class="env-grid">
          <div v-for="env in filteredDetected" :key="env.id" class="env-item">
            <div class="env-item-top">
              <div :class="['env-icon', env.category]">
                <el-icon v-if="env.category === 'Runtime'"><Cpu /></el-icon>
                <el-icon v-else-if="env.category === 'Database'"><Coin /></el-icon>
                <el-icon v-else-if="env.category === 'DevTool'"><SetUp /></el-icon>
                <el-icon v-else><Box /></el-icon>
              </div>
              <div class="env-info">
                <div class="name">{{ env.display_name }}</div>
                <div class="path">{{ env.path || '—' }}</div>
              </div>
              <div class="env-actions">
                <el-tooltip :content="t('envPanel.title')" placement="top">
                  <el-button text size="small" @click="openEnvPanel(env)">
                    <el-icon><Operation /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-button v-if="env.path" type="danger" text size="small" @click="handleUninstall(env)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="env-item-tags">
              <el-tag v-if="env.version" size="small" type="info">{{ env.version }}</el-tag>
              <el-tag v-if="env.in_user_path" size="small" type="success">PATH</el-tag>
              <el-tag v-else-if="env.in_system_path" size="small" type="" effect="plain">{{ t('envVars.pathSourceSystem') }} PATH</el-tag>
              <template v-if="getEnvStatus(env.id)">
                <el-tag v-if="getEnvStatus(env.id).running" size="small" type="success" effect="dark" class="status-tag">
                  <span class="status-dot running"></span>{{ t('status.running') }}
                </el-tag>
                <el-tag v-else-if="getEnvStatus(env.id).running === false" size="small" type="info" effect="plain" class="status-tag">
                  <span class="status-dot stopped"></span>{{ t('status.stopped') }}
                </el-tag>
                <el-tag
                  v-for="p in getEnvStatus(env.id).ports.filter(x => x.open)"
                  :key="p.port" size="small" type="warning" effect="plain"
                >:{{ p.port }}</el-tag>
              </template>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Manual Tab -->
      <el-tab-pane :label="`${t('envs.manual')} (${filteredManual.length})`" name="manual">
        <div style="margin-bottom: 16px">
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            {{ t('manual.addBtn') }}
          </el-button>
        </div>
        <div v-if="filteredManual.length === 0" class="empty-state">
          <el-icon><FolderOpened /></el-icon>
          <p>{{ t('manual.noManualEnvs') }}</p>
        </div>
        <div v-else class="env-grid">
          <div v-for="env in filteredManual" :key="env.id" class="env-item">
            <div class="env-item-top">
              <div :class="['env-icon', env.category]">
                <el-icon v-if="env.category === 'Runtime'"><Cpu /></el-icon>
                <el-icon v-else-if="env.category === 'Database'"><Coin /></el-icon>
                <el-icon v-else-if="env.category === 'DevTool'"><SetUp /></el-icon>
                <el-icon v-else><Box /></el-icon>
              </div>
              <div class="env-info">
                <div class="name">{{ env.display_name }}</div>
                <div class="path">{{ env.bin_path }}</div>
              </div>
              <div class="env-actions">
                <el-tooltip :content="t('envPanel.title')" placement="top">
                  <el-button text size="small" @click="openEnvPanel(env)">
                    <el-icon><Operation /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-button v-if="env.version_command" text size="small" @click="handleRefreshVersion(env.id)">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button type="danger" text size="small" @click="handleRemoveManual(env.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="env-item-tags">
              <el-tag size="small" type="warning">{{ t('manual.badge') }}</el-tag>
              <el-tag v-if="env.version" size="small" type="info">{{ env.version }}</el-tag>
              <template v-if="getEnvStatus(env.id)">
                <el-tag v-if="getEnvStatus(env.id).running" size="small" type="success" effect="dark" class="status-tag">
                  <span class="status-dot running"></span>{{ t('status.running') }}
                </el-tag>
                <el-tag v-else-if="getEnvStatus(env.id).running === false" size="small" type="info" effect="plain" class="status-tag">
                  <span class="status-dot stopped"></span>{{ t('status.stopped') }}
                </el-tag>
                <el-tag
                  v-for="p in getEnvStatus(env.id).ports.filter(x => x.open)"
                  :key="p.port" size="small" type="warning" effect="plain"
                >:{{ p.port }}</el-tag>
              </template>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Add Manual Env Dialog -->
    <el-dialog v-model="showAddDialog" :title="t('manual.title')" width="520px">
      <el-form label-position="top">
        <el-form-item :label="t('manual.name')">
          <el-input v-model="form.name" :placeholder="t('manual.namePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('manual.displayName')">
          <el-input v-model="form.display_name" :placeholder="t('manual.displayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('manual.category')">
          <el-select v-model="form.category" style="width: 100%">
            <el-option value="Runtime" :label="t('envs.runtime')" />
            <el-option value="Database" :label="t('envs.database')" />
            <el-option value="DevTool" :label="t('envs.devtool')" />
            <el-option value="SDK" :label="t('envs.sdk')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('manual.path')">
          <el-input v-model="form.path" :placeholder="t('manual.pathPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('manual.binSubdir')">
          <el-input v-model="form.bin_subdir" :placeholder="t('manual.binSubdirPlaceholder')" />
          <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px">{{ t('manual.binSubdirHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('manual.versionCmd')">
          <el-input v-model="form.version_command" :placeholder="t('manual.versionCmdPlaceholder')" />
          <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px">{{ t('manual.versionCmdHint') }}</div>
        </el-form-item>
        <el-form-item>
          <div style="display: flex; align-items: center; justify-content: space-between; width: 100%">
            <div>
              <div style="font-size: 14px">{{ t('manual.addToPath') }}</div>
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">{{ t('manual.addToPathHint') }}</div>
            </div>
            <el-switch v-model="form.add_to_path" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddManual">{{ t('common.add') }}</el-button>
      </template>
    </el-dialog>

    <!-- ══════ Environment Panel Dialog ══════ -->
    <el-dialog
      v-model="showPanel"
      :title="`${t('envPanel.title')} - ${panelEnv?.display_name || ''}`"
      width="900px"
      top="4vh"
      :close-on-click-modal="false"
    >
      <!-- Status + PATH toolbar -->
      <div v-if="panelStatus" class="panel-status-bar">
        <div class="panel-status-indicator">
          <span :class="['status-dot-lg', panelStatus.running ? 'running' : 'stopped']"></span>
          <span :style="{ fontWeight: 600, color: panelStatus.running ? 'var(--el-color-success)' : 'var(--el-text-color-secondary)' }">
            {{ panelStatus.running ? t('status.running') : t('status.stopped') }}
          </span>
          <span v-if="panelStatus.pid" style="font-size: 12px; color: var(--el-text-color-secondary); margin-left: 4px">
            PID: {{ panelStatus.pid }}
          </span>
        </div>
        <div class="panel-status-ports">
          <el-tag
            v-for="p in panelStatus.ports" :key="p.port"
            size="small"
            :type="p.open ? 'success' : 'info'"
            :effect="p.open ? 'dark' : 'plain'"
          >
            {{ p.label }} :{{ p.port }}
            <el-icon v-if="p.open" style="margin-left: 2px"><SuccessFilled /></el-icon>
          </el-tag>
        </div>
        <el-button text size="small" :loading="statusLoading" @click="refreshPanelStatus" style="margin-left: auto">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>

      <div class="panel-toolbar">
        <div class="panel-toolbar-path">
          <el-icon><FolderOpened /></el-icon>
          <span class="panel-path-text">{{ panelBinPath }}</span>
        </div>
        <el-button
          v-if="panelIsInPath"
          size="small" type="warning" plain
          @click="handlePanelRemovePath"
        >
          <el-icon><Remove /></el-icon>
          {{ t('envPanel.removeFromPath') }}
        </el-button>
        <el-button
          v-else
          size="small" type="success" plain
          @click="handlePanelAddPath"
        >
          <el-icon><CirclePlus /></el-icon>
          {{ t('envPanel.addToPath') }}
        </el-button>
        <el-tag :type="panelIsInPath ? 'success' : 'info'" size="small">
          {{ panelIsInPath ? t('envPanel.pathInPath') : t('envPanel.pathNotInPath') }}
        </el-tag>
      </div>

      <el-tabs v-model="panelTab">
        <!-- ── Config Files Tab ── -->
        <el-tab-pane :label="t('envPanel.configTab')" name="config">
          <div class="config-editor-layout">
            <div class="config-file-list">
              <div v-if="configLoading" style="text-align: center; padding: 20px; color: var(--el-text-color-secondary)">
                <el-icon class="is-loading"><Loading /></el-icon>
                <div style="margin-top: 8px; font-size: 12px">{{ t('configFile.discovering') }}</div>
              </div>
              <template v-else>
                <div
                  v-for="(file, idx) in configFiles" :key="file.path"
                  :class="['config-file-item', { active: selectedFileIdx === idx }]"
                  @click="selectConfigFile(idx)"
                >
                  <el-icon><Document /></el-icon>
                  <div class="config-file-item-info">
                    <div class="config-file-item-name">
                      {{ file.name }}
                      <el-tag v-if="file.custom" size="small" type="warning" style="margin-left: 4px; transform: scale(0.85)">{{ t('configFile.customTag') }}</el-tag>
                    </div>
                    <div class="config-file-item-path">{{ file.path }}</div>
                  </div>
                  <el-button
                    v-if="file.custom"
                    text size="small" type="danger"
                    @click.stop="handleRemoveCustomFile(idx)"
                    style="flex-shrink: 0"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <div v-if="configFiles.length === 0" style="text-align: center; padding: 16px; color: var(--el-text-color-secondary); font-size: 12px">
                  {{ t('configFile.noFilesHint') }}
                </div>
              </template>
              <!-- Manual add file -->
              <div class="config-file-add">
                <el-input
                  v-model="manualFilePath"
                  size="small"
                  :placeholder="t('configFile.pathPlaceholder')"
                  @keyup.enter="handleAddManualFile"
                >
                  <template #append>
                    <el-button :icon="Plus" @click="handleAddManualFile" />
                  </template>
                </el-input>
              </div>
            </div>

            <div class="config-editor-area">
              <div v-if="selectedFileIdx === null" class="config-editor-placeholder">
                <el-icon style="font-size: 32px; opacity: 0.3"><Document /></el-icon>
                <p>{{ t('configFile.selectFile') }}</p>
              </div>
              <template v-else>
                <div class="config-editor-toolbar">
                  <span class="config-editor-filepath">{{ configFiles[selectedFileIdx]?.path }}</span>
                  <el-button type="primary" size="small" :loading="configSaving" @click="handleSaveConfigFile">
                    <el-icon><Check /></el-icon>
                    {{ t('common.save') }}
                  </el-button>
                </div>
                <el-input
                  v-model="configContent"
                  type="textarea"
                  :autosize="false"
                  class="config-textarea"
                  spellcheck="false"
                />
              </template>
            </div>
          </div>
        </el-tab-pane>

        <!-- ── Service Control Tab ── -->
        <el-tab-pane :label="t('envPanel.cmdTab')" name="commands">
          <div class="cmd-panel">
            <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 10px; word-break: break-all">
              {{ t('svcCmd.cwdHint') }}: <code style="background: var(--el-fill-color-light); padding: 1px 6px; border-radius: 3px">{{ panelBinPath }}</code>
            </div>
            <!-- Predefined commands -->
            <div v-if="envCommands.length > 0" class="cmd-buttons">
              <el-button
                v-for="cmd in envCommands"
                :key="cmd.id"
                :type="cmd.type || 'default'"
                :loading="runningCmd === cmd.id"
                :disabled="isCmdDisabled(cmd)"
                @click="handleRunPresetCmd(cmd)"
              >
                {{ i18n.locale === 'zh-CN' ? cmd.label_zh : cmd.label_en }}
              </el-button>
            </div>
            <div v-else style="color: var(--el-text-color-secondary); font-size: 13px; margin-bottom: 12px">
              {{ t('svcCmd.noCommands') }}
            </div>

            <!-- Custom command -->
            <div class="cmd-custom">
              <span style="font-size: 13px; font-weight: 500; margin-bottom: 6px; display: block">{{ t('svcCmd.customCmd') }}</span>
              <div style="display: flex; gap: 8px">
                <el-input
                  v-model="customCmd"
                  :placeholder="t('svcCmd.customPlaceholder')"
                  @keyup.enter="handleRunCustomCmd"
                />
                <el-button type="primary" :loading="runningCmd === '__custom__'" @click="handleRunCustomCmd">
                  <el-icon><CaretRight /></el-icon>
                  {{ t('svcCmd.run') }}
                </el-button>
              </div>
            </div>

            <!-- Output -->
            <div class="cmd-output-header">
              <span style="font-size: 13px; font-weight: 500">{{ t('svcCmd.output') }}</span>
              <el-button text size="small" @click="cmdOutput = ''">{{ t('svcCmd.clearOutput') }}</el-button>
            </div>
            <div class="cmd-output">
              <pre>{{ cmdOutput || '...' }}</pre>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '../stores/app'
import { useI18nStore } from '../i18n'
import * as api from '../api'

const store = useAppStore()
const i18n = useI18nStore()
const { t } = i18n

// ── List state ──
const search = ref('')
const categoryFilter = ref('all')
const activeTab = ref('detected')
const showAddDialog = ref(false)
const form = ref({
  name: '', display_name: '', category: 'Runtime',
  path: '', bin_subdir: '', version_command: '', add_to_path: false,
})

// ── Status state ──
const envStatusMap = ref({})
const statusLoading = ref(false)

// ── Panel state ──
const showPanel = ref(false)
const panelEnv = ref(null)
const panelTab = ref('config')
const panelPathEntries = ref([])
const panelPathEntriesExpanded = ref([])

// Config state
const configFiles = ref([])
const configLoading = ref(false)
const configContent = ref('')
const configSaving = ref(false)
const selectedFileIdx = ref(null)
const manualFilePath = ref('')

// Command state
const envCommands = ref([])
const customCmd = ref('')
const cmdOutput = ref('')
const runningCmd = ref(null)

// ── Computed ──
const panelBinPath = computed(() => {
  if (!panelEnv.value) return ''
  return panelEnv.value.bin_path || panelEnv.value.path || ''
})

const panelEnvPath = computed(() => {
  if (!panelEnv.value) return ''
  return panelEnv.value.path || panelEnv.value.bin_path || ''
})

const panelStatus = computed(() => {
  if (!panelEnv.value) return null
  return getEnvStatus(panelEnv.value.id || panelEnv.value.name)
})

const panelIsInPath = computed(() => {
  const bp = panelBinPath.value.toLowerCase().replace(/[\\/]+$/, '')
  if (!bp) return false
  return panelPathEntriesExpanded.value.some(p => p.toLowerCase().replace(/[\\/]+$/, '') === bp)
})

const filteredDetected = computed(() => {
  return store.environments.filter(e => {
    const matchSearch = e.display_name.toLowerCase().includes(search.value.toLowerCase()) ||
      e.name.toLowerCase().includes(search.value.toLowerCase())
    const matchCategory = categoryFilter.value === 'all' || e.category === categoryFilter.value
    return matchSearch && matchCategory
  })
})

const filteredManual = computed(() => {
  return store.manualEnvs.filter(e => {
    const matchSearch = e.display_name.toLowerCase().includes(search.value.toLowerCase()) ||
      e.name.toLowerCase().includes(search.value.toLowerCase())
    const matchCategory = categoryFilter.value === 'all' || e.category === categoryFilter.value
    return matchSearch && matchCategory
  })
})

// ── List handlers ──
async function handleUninstall(env) {
  if (!env.path) return
  try {
    await ElMessageBox.confirm(t('manual.removeConfirm'), { type: 'warning' })
    await store.uninstallPackage(env.path)
    ElMessage.success(t('envs.uninstallSuccess'))
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`${t('envs.uninstallFailed')}: ${e}`)
  }
}

async function handleAddManual() {
  try {
    await store.addManualEnv({ ...form.value, version_command: form.value.version_command || null })
    ElMessage.success(t('manual.addSuccess'))
    showAddDialog.value = false
    form.value = { name: '', display_name: '', category: 'Runtime', path: '', bin_subdir: '', version_command: '', add_to_path: false }
  } catch (e) {
    ElMessage.error(`${t('manual.addFailed')}: ${e}`)
  }
}

async function handleRemoveManual(envId) {
  try {
    await ElMessageBox.confirm(t('manual.removeConfirm'), { type: 'warning' })
    await store.removeManualEnv(envId)
    ElMessage.success(t('manual.removeSuccess'))
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`${t('manual.removeFailed')}: ${e}`)
  }
}

async function handleRefreshVersion(envId) {
  try {
    await store.refreshManualEnvVersion(envId)
    ElMessage.success(t('manual.refreshVersion'))
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

// ── Panel ──
async function openEnvPanel(env) {
  panelEnv.value = env
  panelTab.value = 'config'
  configFiles.value = []
  configContent.value = ''
  selectedFileIdx.value = null
  manualFilePath.value = ''
  envCommands.value = []
  cmdOutput.value = ''
  customCmd.value = ''
  showPanel.value = true

  configLoading.value = true
  try {
    const [files, cmds, pathRes] = await Promise.all([
      api.discoverConfigFiles(env.id || env.name, panelBinPath.value || null),
      api.getEnvCommands(env.id || env.name),
      api.getPathEntries(),
    ])
    configFiles.value = files
    envCommands.value = cmds
    panelPathEntries.value = pathRes.entries || pathRes
    panelPathEntriesExpanded.value = pathRes.expanded || pathRes.entries || pathRes
    refreshPanelStatus()
    if (files.length === 1) await selectConfigFile(0)
  } catch (e) {
    console.error(e)
  } finally {
    configLoading.value = false
  }
}

// ── Config file handlers ──
async function selectConfigFile(idx) {
  selectedFileIdx.value = idx
  configContent.value = ''
  try {
    const result = await api.readConfigFile(configFiles.value[idx].path)
    configContent.value = result.content
  } catch (e) {
    ElMessage.error(`${t('configFile.loadFailed')}: ${e}`)
  }
}

async function handleSaveConfigFile() {
  if (selectedFileIdx.value === null) return
  configSaving.value = true
  try {
    await api.saveConfigFile(configFiles.value[selectedFileIdx.value].path, configContent.value)
    ElMessage.success(t('configFile.saved'))
  } catch (e) {
    ElMessage.error(`${t('configFile.saveFailed')}: ${e}`)
  } finally {
    configSaving.value = false
  }
}

async function handleAddManualFile() {
  const p = manualFilePath.value.trim()
  if (!p) return
  if (configFiles.value.some(f => f.path === p)) {
    const idx = configFiles.value.findIndex(f => f.path === p)
    await selectConfigFile(idx)
    manualFilePath.value = ''
    return
  }
  try {
    const envId = panelEnv.value.id || panelEnv.value.name
    const result = await api.addCustomConfigFile(envId, p)
    configFiles.value.push(result)
    manualFilePath.value = ''
    await selectConfigFile(configFiles.value.length - 1)
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

async function handleRemoveCustomFile(idx) {
  const file = configFiles.value[idx]
  if (!file?.custom) return
  try {
    const envId = panelEnv.value.id || panelEnv.value.name
    await api.removeCustomConfigFile(envId, file.path)
    configFiles.value.splice(idx, 1)
    if (selectedFileIdx.value === idx) {
      selectedFileIdx.value = null
      configContent.value = ''
    } else if (selectedFileIdx.value !== null && selectedFileIdx.value > idx) {
      selectedFileIdx.value--
    }
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

// ── PATH handlers ──
async function reloadPanelPath() {
  const res = await api.getPathEntries()
  panelPathEntries.value = res.entries || res
  panelPathEntriesExpanded.value = res.expanded || res.entries || res
}

async function handlePanelAddPath() {
  const bp = panelBinPath.value
  if (!bp) return
  try {
    const res = await api.addToPath(bp)
    await reloadPanelPath()
    if (res && res.adjusted) {
      ElMessage.success(`${t('envVars.pathAutoAdjusted')}: ${res.path}`)
    } else {
      ElMessage.success(t('envPanel.pathAdded'))
    }
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

async function handlePanelRemovePath() {
  const bp = panelBinPath.value
  if (!bp) return
  try {
    await api.removeFromPath(bp)
    await reloadPanelPath()
    ElMessage.success(t('envPanel.pathRemoved'))
  } catch (e) {
    ElMessage.error(`${t('common.failed')}: ${e}`)
  }
}

// ── Command handlers ──
async function handleRunPresetCmd(cmd) {
  runningCmd.value = cmd.id
  try {
    const result = await api.runCommand(cmd.cmd, panelBinPath.value, null, cmd.background || false, panelEnvPath.value)
    const label = i18n.locale === 'zh-CN' ? cmd.label_zh : cmd.label_en
    const expanded = cmd.cmd.replace(/\{bin_path\}/g, panelBinPath.value).replace(/\{env_path\}/g, panelEnvPath.value)
    appendOutput(label, expanded, result)
    if (['start', 'stop', 'restart', 'quit', 'reload'].includes(cmd.id)) {
      setTimeout(refreshPanelStatus, 1500)
    }
  } catch (e) {
    appendOutput('Error', cmd.cmd, { exit_code: -1, stdout: '', stderr: String(e) })
  } finally {
    runningCmd.value = null
  }
}

async function handleRunCustomCmd() {
  const cmd = customCmd.value.trim()
  if (!cmd) return
  runningCmd.value = '__custom__'
  try {
    const result = await api.runCommand(cmd, panelBinPath.value, null, false, panelEnvPath.value)
    appendOutput(t('svcCmd.customCmd'), cmd, result)
  } catch (e) {
    appendOutput('Error', cmd, { exit_code: -1, stdout: '', stderr: String(e) })
  } finally {
    runningCmd.value = null
  }
}

function appendOutput(label, cmd, result) {
  const time = new Date().toLocaleTimeString()
  let text = `\n[${time}] ${label}\n$ ${cmd}\n`
  if (result.stdout) text += result.stdout
  if (result.stderr) text += result.stderr
  if (!result.stdout && !result.stderr) text += '(no output)\n'
  text += `--- ${t('svcCmd.exitCode')}: ${result.exit_code} ---\n`
  cmdOutput.value += text
}

function getEnvStatus(envId) {
  return envStatusMap.value[envId] || null
}

function isCmdDisabled(cmd) {
  const status = panelStatus.value
  if (!status || status.running === null) return false
  const id = cmd.id
  if (status.running) {
    return id === 'start'
  } else {
    return ['stop', 'quit', 'reload', 'reopen', 'restart'].includes(id)
  }
}

async function loadAllStatus() {
  statusLoading.value = true
  try {
    const results = await api.getEnvStatusAll()
    const map = {}
    for (const s of results) map[s.env_id] = s
    envStatusMap.value = map
  } catch (e) {
    console.error('Failed to load status:', e)
  } finally {
    statusLoading.value = false
  }
}

async function refreshPanelStatus() {
  if (!panelEnv.value) return
  const envId = panelEnv.value.id || panelEnv.value.name
  const envPath = panelEnv.value.path || panelEnv.value.bin_path || null
  statusLoading.value = true
  try {
    const s = await api.getEnvStatus(envId, envPath)
    envStatusMap.value = { ...envStatusMap.value, [s.env_id]: s }
  } catch (e) {
    console.error(e)
  } finally {
    statusLoading.value = false
  }
}

onMounted(() => {
  Promise.all([store.scanEnvironments(), store.loadManualEnvs()])
  loadAllStatus()
})
</script>
