<template>
  <router-view />
</template>

<script setup>
import { watchEffect } from 'vue'
import { useI18nStore } from './i18n'
import { useAppStore } from './stores/app'

const i18n = useI18nStore()
const appStore = useAppStore()

watchEffect(async () => {
  const config = appStore.config
  const theme = config?.theme || 'system'
  const html = document.documentElement
  if (theme === 'dark') {
    html.classList.add('dark')
  } else if (theme === 'light') {
    html.classList.remove('dark')
  } else {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }
})
</script>
