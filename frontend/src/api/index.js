import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const scanEnvironments = () => api.get('/scan').then(r => r.data)
export const getSystemInfo = () => api.get('/system-info').then(r => r.data)

export const getAppConfig = () => api.get('/config').then(r => r.data)
export const saveAppConfig = (config) => api.post('/config', config).then(r => r.data)

export const getMirrorConfigs = () => api.get('/mirrors').then(r => r.data)
export const setMirrorSource = (name, url) => api.post(`/mirrors/${name}`, { url }).then(r => r.data)

export const getEnvVars = () => api.get('/env-vars').then(r => r.data)
export const getSystemEnvVars = () => api.get('/system-env-vars').then(r => r.data)
export const setEnvVar = (name, value) => api.post('/env-vars', { name, value }).then(r => r.data)
export const removeEnvVar = (name) => api.delete(`/env-vars/${name}`).then(r => r.data)

export const getPathEntries = () => api.get('/path').then(r => r.data)
export const getSystemPathEntries = () => api.get('/system-path').then(r => r.data)
export const addToPath = (path) => api.post('/path', { path }).then(r => r.data)
export const removeFromPath = (path) => api.delete('/path', { data: { path } }).then(r => r.data)

export const getManualEnvs = () => api.get('/manual-envs').then(r => r.data)
export const addManualEnv = (request) => api.post('/manual-envs', request).then(r => r.data)
export const removeManualEnv = (envId) => api.delete(`/manual-envs/${envId}`).then(r => r.data)
export const refreshManualEnvVersion = (envId) => api.post(`/manual-envs/${envId}/refresh`).then(r => r.data)

export const getAvailablePackages = () => api.get('/packages').then(r => r.data)
export const installPackage = (data) => api.post('/install', data).then(r => r.data)
export const uninstallPackage = (installPath) => api.post('/uninstall', { install_path: installPath }).then(r => r.data)

export const discoverConfigFiles = (envId, envPath) => api.get('/config-files', { params: { env_id: envId, env_path: envPath } }).then(r => r.data)
export const readConfigFile = (path) => api.get('/config-files/read', { params: { path } }).then(r => r.data)
export const saveConfigFile = (path, content) => api.post('/config-files/save', { path, content }).then(r => r.data)
export const addCustomConfigFile = (envId, filePath) => api.post('/custom-config-files', { env_id: envId, file_path: filePath }).then(r => r.data)
export const removeCustomConfigFile = (envId, filePath) => api.delete('/custom-config-files', { data: { env_id: envId, file_path: filePath } }).then(r => r.data)

export const getEnvCommands = (envId) => api.get(`/commands/${envId}`).then(r => r.data)
export const getEnvStatusAll = (ids) => api.get('/env-status', { params: { ids: ids ? ids.join(',') : '' } }).then(r => r.data)
export const getEnvStatus = (envId, envPath) => api.get(`/env-status/${envId}`, { params: { env_path: envPath || '' } }).then(r => r.data)
export const runCommand = (cmd, binPath, cwd, background, envPath) => api.post('/run-command', { cmd, bin_path: binPath, cwd, background, env_path: envPath }).then(r => r.data)
