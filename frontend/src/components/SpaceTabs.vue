<template>
  <Select
    class="!w-fit"
    v-if="screen.width < 640"
    :options="spaceTabs"
    :modelValue="currentTab"
    @update:modelValue="changeTab"
  />
  <div v-else class="flex items-center rounded-[10px] bg-surface-gray-2 p-0.5">
    <router-link
      v-for="tab in spaceTabs"
      :key="tab.value"
      :to="tabRoute(tab.value)"
      class="inline-flex h-6.5 shrink-0 items-center justify-center gap-2 rounded-[9px] px-2 text-base transition-colors focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3"
      :class="
        tab.value === currentTab
          ? 'border border-outline-gray-1 bg-surface-white text-ink-gray-8 shadow-sm'
          : 'text-ink-gray-5 hover:bg-surface-gray-3/80 hover:text-ink-gray-7'
      "
    >
      {{ tab.label }}
    </router-link>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Select } from 'frappe-ui'
import { useScreenSize } from '@/composables/useScreenSize'

const props = defineProps<{
  spaceId: string
}>()

const currentRoute = useRoute()
const router = useRouter()
const screen = useScreenSize()

const spaceTabs = [
  { label: 'Journey', value: 'journey' },
  { label: 'Discussions', value: 'discussions' },
  { label: 'Pages', value: 'pages' },
  { label: 'Tasks', value: 'tasks' },
]

const currentTab = computed(() => {
  let currentPage = currentRoute.name?.toString() || 'SpaceJourney'
  return {
    SpaceDiscussions: 'discussions',
    SpacePages: 'pages',
    SpaceTasks: 'tasks',
    SpaceJourney: 'journey',
  }[currentPage]
})

function changeTab(value: string) {
  if (!value || value === currentTab.value) return

  let routeName = getRouteName(value)
  if (!routeName) return

  router.push({ name: routeName, params: { spaceId: props.spaceId } }).catch(() => {})
}

function tabRoute(value: string) {
  return {
    name: getRouteName(value),
    params: { spaceId: props.spaceId },
  }
}

function getRouteName(value: string) {
  return {
    discussions: 'SpaceDiscussions',
    pages: 'SpacePages',
    tasks: 'SpaceTasks',
    journey: 'SpaceJourney',
  }[value]
}
</script>
