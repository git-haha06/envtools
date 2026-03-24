import { defineStore } from 'pinia'
import * as api from '../api'

export const useAppStore = defineStore('app', {
  state: () => ({
    environments: [],
    manualEnvs: [],
    systemInfo: null,
    packages: [],
    config: null,
    mirrorConfigs: [],
    envVars: {},
    systemEnvVars: {},
    pathEntries: [],
    pathEntriesExpanded: [],
    systemPathEntries: [],
    systemPathEntriesExpanded: [],
    scanning: false,
    installing: null,
  }),
  actions: {
    async scanEnvironments() {
      this.scanning = true
      try {
        this.environments = await api.scanEnvironments()
      } finally {
        this.scanning = false
      }
    },
    async loadSystemInfo() {
      this.systemInfo = await api.getSystemInfo()
    },
    async loadPackages() {
      this.packages = await api.getAvailablePackages()
    },
    async loadConfig() {
      this.config = await api.getAppConfig()
    },
    async saveConfig(config) {
      await api.saveAppConfig(config)
      this.config = config
    },
    async loadMirrorConfigs() {
      this.mirrorConfigs = await api.getMirrorConfigs()
    },
    async loadEnvVars() {
      this.envVars = await api.getEnvVars()
    },
    async loadSystemEnvVars() {
      this.systemEnvVars = await api.getSystemEnvVars()
    },
    async loadPathEntries() {
      const res = await api.getPathEntries()
      this.pathEntries = res.entries || res
      this.pathEntriesExpanded = res.expanded || res.entries || res
    },
    async loadSystemPathEntries() {
      const res = await api.getSystemPathEntries()
      this.systemPathEntries = res.entries || res
      this.systemPathEntriesExpanded = res.expanded || res.entries || res
    },
    async installPackage(packageName, version, useMirror) {
      this.installing = packageName
      try {
        const result = await api.installPackage({
          package_name: packageName,
          version,
          use_mirror: useMirror,
          install_dir: this.config?.install_dir || null,
        })
        await this.scanEnvironments()
        return result
      } finally {
        this.installing = null
      }
    },
    async uninstallPackage(installPath) {
      await api.uninstallPackage(installPath)
      await this.scanEnvironments()
    },
    async setEnvVar(name, value) {
      await api.setEnvVar(name, value)
      await this.loadEnvVars()
    },
    async removeEnvVar(name) {
      await api.removeEnvVar(name)
      await this.loadEnvVars()
    },
    async addToPath(path) {
      const res = await api.addToPath(path)
      await this.loadPathEntries()
      return res
    },
    async removeFromPath(path) {
      await api.removeFromPath(path)
      await this.loadPathEntries()
    },
    async setMirrorSource(name, url) {
      await api.setMirrorSource(name, url)
      await this.loadMirrorConfigs()
    },
    async loadManualEnvs() {
      this.manualEnvs = await api.getManualEnvs()
    },
    async addManualEnv(request) {
      const env = await api.addManualEnv(request)
      await this.loadManualEnvs()
      return env
    },
    async removeManualEnv(envId) {
      await api.removeManualEnv(envId)
      await this.loadManualEnvs()
    },
    async refreshManualEnvVersion(envId) {
      const result = await api.refreshManualEnvVersion(envId)
      await this.loadManualEnvs()
      return result.version
    },
  },
})
