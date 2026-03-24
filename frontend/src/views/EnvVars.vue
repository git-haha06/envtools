<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('envVars.title') }}</h1>
        <p>{{ t('envVars.subtitle') }}</p>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <!-- PATH Tab -->
      <el-tab-pane :label="t('envVars.pathTab')" name="path">
        <div class="path-split-layout">
          <!-- Left: User PATH -->
          <el-card class="path-split-panel">
            <template #header>
              <div class="tabs-header">
                <div style="display: flex; align-items: center; gap: 6px">
                  <span>{{ t('envVars.userPathTab') }}</span>
                  <el-tag size="small" type="success" effect="plain">{{ store.pathEntries.length }}</el-tag>
                </div>
                <div style="display: flex; gap: 8px">
                  <el-button size="small" @click="refreshAllPath">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                  <el-button size="small" type="primary" @click="showAddPath = true">
                    <el-icon><Plus /></el-icon>
                    {{ t('envVars.add') }}
                  </el-button>
                </div>
              </div>
            </template>
            <el-scrollbar max-height="520px">
              <div v-if="store.pathEntries.length === 0" class="empty-state" style="padding: 20px 0">
                <p>{{ t('envVars.noPathEntries') }}</p>
              </div>
              <div v-for="(entry, i) in store.pathEntries" :key="`usr-${entry}-${i}`" class="path-entry">
                <el-icon><FolderOpened /></el-icon>
                <span class="path-text">{{ entry }}</span>
                <el-tag size="small" type="info" style="flex-shrink: 0">{{ i + 1 }}</el-tag>
                <el-button class="delete-btn" type="danger" text size="small" @click="handleRemovePath(entry)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-scrollbar>
          </el-card>

          <!-- Right: System PATH -->
          <el-card class="path-split-panel path-split-panel-system">
            <template #header>
              <div class="tabs-header">
                <div style="display: flex; align-items: center; gap: 6px">
                  <span>{{ t('envVars.systemPathTab') }}</span>
                  <el-tag size="small" type="info" effect="plain">{{ store.systemPathEntries.length }}</el-tag>
                </div>
                <el-tag size="small" type="info">{{ t('envVars.systemReadonly') }}</el-tag>
              </div>
            </template>
            <el-scrollbar max-height="520px">
              <div v-for="(entry, i) in store.systemPathEntries" :key="`sys-${entry}-${i}`" class="path-entry system-entry">
                <el-icon><FolderOpened /></el-icon>
                <span class="path-text">{{ entry }}</span>
                <el-tag size="small" type="info" style="flex-shrink: 0">{{ i + 1 }}</el-tag>
              </div>
            </el-scrollbar>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- User Variables Tab -->
      <el-tab-pane :label="t('envVars.userVarsTab')" name="user-vars">
        <el-card>
          <template #header>
            <div class="tabs-header">
              <span>{{ t('envVars.userEnvVars') }}</span>
              <div style="display: flex; gap: 8px">
                <el-button size="small" @click="store.loadEnvVars()">
                  <el-icon><Refresh /></el-icon>
                  {{ t('envVars.refresh') }}
                </el-button>
                <el-button size="small" type="primary" @click="showAddEnv = true">
                  <el-icon><Plus /></el-icon>
                  {{ t('envVars.add') }}
                </el-button>
              </div>
            </div>
          </template>
          <el-scrollbar max-height="460px">
            <div v-if="Object.keys(store.envVars).length === 0" class="empty-state">
              <p>{{ t('envVars.noEnvVars') }}</p>
            </div>
            <div v-for="(value, name) in store.envVars" :key="name" class="var-entry">
              <el-icon><Setting /></el-icon>
              <span class="var-name">{{ name }}</span>
              <span class="var-value">{{ value }}</span>
              <div class="var-actions">
                <el-button text size="small" @click="openEditDialog(name, value)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" text size="small" @click="handleRemoveEnvVar(name)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-tab-pane>

      <!-- System Variables Tab -->
      <el-tab-pane :label="t('envVars.systemVarsTab')" name="system-vars">
        <el-card>
          <template #header>
            <div class="tabs-header">
              <span>{{ t('envVars.systemEnvVars') }}</span>
              <div style="display: flex; gap: 8px; align-items: center">
                <el-tag size="small" type="info">{{ t('envVars.systemReadonly') }}</el-tag>
                <el-button size="small" @click="store.loadSystemEnvVars()">
                  <el-icon><Refresh /></el-icon>
                  {{ t('envVars.refresh') }}
                </el-button>
              </div>
            </div>
          </template>
          <el-scrollbar max-height="460px">
            <div v-if="Object.keys(store.systemEnvVars).length === 0" class="empty-state">
              <p>{{ t('envVars.noEnvVars') }}</p>
            </div>
            <div v-for="(value, name) in store.systemEnvVars" :key="name" class="var-entry system-entry">
              <el-icon><Setting /></el-icon>
              <span class="var-name">{{ name }}</span>
              <span class="var-value">{{ value }}</span>
            </div>
          </el-scrollbar>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Add Env Var Dialog -->
    <el-dialog v-model="showAddEnv" :title="t('envVars.addEnvVar')" width="460px">
      <el-form label-position="top">
        <el-form-item :label="t('envVars.name')">
          <el-input v-model="newName" placeholder="VARIABLE_NAME" />
        </el-form-item>
        <el-form-item :label="t('envVars.value')">
          <el-input v-model="newValue" placeholder="value" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEnv = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddEnvVar">{{ t('common.add') }}</el-button>
      </template>
    </el-dialog>

    <!-- Edit Env Var Dialog -->
    <el-dialog v-model="showEditEnv" :title="`${t('envVars.editEnvVar')}: ${editName}`" :width="isPathVar ? '600px' : '460px'">
      <el-form label-position="top">
        <el-form-item :label="t('envVars.value')">
          <template v-if="isPathVar">
            <div class="path-editor">
              <div class="path-editor-hint">{{ t('envVars.pathEditHint') }}</div>
              <div v-for="(line, idx) in editLines" :key="idx" class="path-editor-row">
                <el-tag size="small" type="info" class="path-editor-idx">{{ idx + 1 }}</el-tag>
                <el-input
                  v-model="editLines[idx]"
                  size="small"
                  placeholder="C:\path\to\directory"
                />
                <el-button
                  type="danger" text size="small"
                  @click="editLines.splice(idx, 1)"
                  :disabled="editLines.length <= 1"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button size="small" @click="editLines.push('')" style="margin-top: 8px">
                <el-icon><Plus /></el-icon>
                {{ t('envVars.add') }}
              </el-button>
            </div>
          </template>
          <el-input v-else v-model="editValue" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditEnv = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleEditEnvVar">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- Add PATH Dialog -->
    <el-dialog v-model="showAddPath" :title="t('envVars.addPathEntry')" width="460px">
      <el-form label-position="top">
        <el-form-item :label="t('envVars.dirPath')">
          <el-input v-model="newPath" placeholder="C:\path\to\directory" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPath = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddPath">{{ t('common.add') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores/app'
import { useI18nStore } from '../i18n'
import * as api from '../api'

const store = useAppStore()
const { t } = useI18nStore()

const activeTab = ref('path')
const showAddEnv = ref(false)
const showEditEnv = ref(false)
const showAddPath = ref(false)
const newName = ref('')
const newValue = ref('')
const newPath = ref('')
const editName = ref('')
const editValue = ref('')
const editLines = ref([])

const isPathVar = computed(() => editName.value.toLowerCase() === 'path')

function openEditDialog(name, value) {
  editName.value = name
  if (name.toLowerCase() === 'path') {
    editLines.value = value.split(';').filter(p => p.trim() !== '')
    if (editLines.value.length === 0) editLines.value = ['']
  } else {
    editValue.value = value
  }
  showEditEnv.value = true
}

async function refreshAllPath() {
  await Promise.all([store.loadPathEntries(), store.loadSystemPathEntries()])
}

async function handleAddEnvVar() {
  if (!newName.value.trim()) return
  try {
    await api.setEnvVar(newName.value.trim(), newValue.value)
    ElMessage.success(`${t('envVars.varSet')}: "${newName.value}"`)
    showAddEnv.value = false
    newName.value = ''
    newValue.value = ''
    store.loadEnvVars()
  } catch (e) {
    ElMessage.error(`${t('envVars.failed')}: ${e}`)
  }
}

async function handleEditEnvVar() {
  try {
    const finalValue = isPathVar.value
      ? editLines.value.filter(l => l.trim() !== '').join(';')
      : editValue.value
    await api.setEnvVar(editName.value, finalValue)
    ElMessage.success(`"${editName.value}" ${t('envVars.varUpdated')}`)
    showEditEnv.value = false
    store.loadEnvVars()
  } catch (e) {
    ElMessage.error(`${t('envVars.failed')}: ${e}`)
  }
}

async function handleRemoveEnvVar(name) {
  try {
    await api.removeEnvVar(name)
    ElMessage.success(`"${name}" ${t('envVars.varRemoved')}`)
    store.loadEnvVars()
  } catch (e) {
    ElMessage.error(`${t('envVars.failed')}: ${e}`)
  }
}

async function handleAddPath() {
  if (!newPath.value.trim()) return
  try {
    const result = await store.addToPath(newPath.value.trim())
    if (result && result.adjusted) {
      ElMessage.success(`${t('envVars.pathAutoAdjusted')}: ${result.path}`)
    } else {
      ElMessage.success(t('envVars.pathAdded'))
    }
    showAddPath.value = false
    newPath.value = ''
  } catch (e) {
    ElMessage.error(`${t('envVars.failed')}: ${e}`)
  }
}

async function handleRemovePath(path) {
  try {
    await store.removeFromPath(path)
    ElMessage.success(t('envVars.pathRemoved'))
  } catch (e) {
    ElMessage.error(`${t('envVars.failed')}: ${e}`)
  }
}

onMounted(async () => {
  await Promise.all([
    store.loadEnvVars(),
    store.loadPathEntries(),
    store.loadSystemEnvVars(),
    store.loadSystemPathEntries(),
  ])
})
</script>
