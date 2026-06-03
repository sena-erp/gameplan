<template>
  <div class="mt-5 body-container">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <SpaceTabs :spaceId="spaceId" />
      <div v-if="summary" class="flex items-center gap-2">
        <Button icon-left="lucide-refresh-cw" @click="reloadJourney">Refresh</Button>
        <Button variant="solid" icon-left="lucide-plus" @click="openMilestoneDialog">
          Add milestone
        </Button>
      </div>
    </div>

    <div v-if="journey.loading" class="py-8">
      <LoadingText text="Loading journey..." />
    </div>

    <EmptyStateBox v-else-if="journey.error">
      <ErrorMessage :message="journey.error" />
    </EmptyStateBox>

    <EmptyStateBox v-else-if="!summary">
      <div class="flex flex-col items-center gap-3">
        <div class="text-ink-gray-6">No journey for this space</div>
        <Button
          variant="solid"
          icon-left="lucide-map"
          :loading="newJourney.loading"
          @click="createJourney"
        >
          Create journey
        </Button>
      </div>
    </EmptyStateBox>

    <div v-else class="space-y-6">
      <div class="rounded border bg-surface-white p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="text-xl font-semibold text-ink-gray-8">{{ summary.journey.title }}</h2>
            <div class="mt-1 text-base text-ink-gray-5">
              {{ summary.progress.done_task_count }} of {{ summary.progress.task_count }} active
              tasks done
            </div>
          </div>
          <div class="text-right text-lg font-semibold text-ink-gray-8">
            {{ summary.progress.percent }}%
          </div>
        </div>

        <EmptyStateBox v-if="!summary.milestones.length" class="mt-4">
          <div class="flex flex-col items-center gap-3">
            <div class="text-ink-gray-6">No milestones yet</div>
            <Button variant="solid" icon-left="lucide-plus" @click="openMilestoneDialog">
              Add milestone
            </Button>
          </div>
        </EmptyStateBox>

        <div v-else class="mt-4 overflow-x-auto pb-2">
          <div class="relative min-w-max">
            <div class="grid overflow-hidden rounded border" :style="chartGridStyle">
              <div
                class="sticky left-0 z-20 border-b border-outline-gray-1 bg-surface-white"
                :style="{ gridColumn: '1', gridRow: '1' }"
              />
              <div
                v-for="week in weekSegments"
                :key="week.key"
                class="border-b border-l border-outline-gray-1 bg-surface-gray-1 px-3 py-2 text-center text-sm font-medium text-ink-gray-5"
                :style="{ gridColumn: `${week.start + 2} / span ${week.days}`, gridRow: '1' }"
              >
                {{ week.label }}
              </div>

              <template v-for="(row, rowIndex) in chartRows" :key="row.lane">
                <div
                  class="sticky left-0 z-20 flex items-center border-t border-outline-gray-1 bg-surface-white px-3 text-base font-medium text-ink-gray-8"
                  :style="{ gridColumn: '1', gridRow: `${rowIndex + 2}` }"
                >
                  {{ row.lane }}
                </div>
                <div
                  class="border-t border-outline-gray-1 bg-surface-white"
                  :style="{ gridColumn: `2 / span ${chartDays}`, gridRow: `${rowIndex + 2}` }"
                />
                <button
                  v-for="milestone in row.milestones"
                  :key="milestone.name"
                  class="z-10 flex min-w-0 items-center rounded border px-3 text-left transition focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  :class="barClass(milestone)"
                  :style="[barStyle(milestone, rowIndex), milestoneBarStyle(milestone)]"
                  @click="selectedMilestoneName = milestone.name"
                >
                  <span
                    v-if="milestone.status === 'Achieved'"
                    class="lucide-circle-check mr-2 h-4 w-4 shrink-0 text-ink-green-3"
                  />
                  <span class="min-w-0 truncate text-base font-semibold">
                    {{ milestone.title }}
                  </span>
                  <span class="ml-2 shrink-0 text-sm opacity-70">{{ milestone.progress }}%</span>
                </button>
              </template>

              <div
                v-if="todayOffset !== null"
                class="pointer-events-none z-30 flex justify-center"
                :style="{
                  gridColumn: `${todayOffset + 2}`,
                  gridRow: `1 / span ${chartRows.length + 1}`,
                }"
              >
                <div class="relative h-full border-l border-dashed border-outline-gray-4">
                  <div
                    class="absolute left-1/2 top-2 -translate-x-1/2 rounded bg-surface-gray-7 px-2 py-0.5 text-sm font-semibold text-ink-white"
                  >
                    Today
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="selectedMilestone" class="rounded border bg-surface-white p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="truncate text-xl font-semibold text-ink-gray-8">
                {{ selectedMilestone.title }}
              </h3>
              <Badge :class="statusClass(selectedMilestone.status)">
                {{ selectedMilestone.status }}
              </Badge>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-base text-ink-gray-5">
              <span>
                {{ selectedMilestone.done_task_count }} / {{ selectedMilestone.task_count }} tasks
              </span>
              <span v-if="selectedMilestone.start_date">
                Starts {{ dayjsLocal(selectedMilestone.start_date).format('D MMM YYYY') }}
              </span>
              <span v-if="selectedMilestone.target_date">
                Target {{ dayjsLocal(selectedMilestone.target_date).format('D MMM YYYY') }}
              </span>
              <span v-if="selectedMilestone.lane">
                {{ selectedMilestone.lane }}
              </span>
              <span v-if="selectedMilestone.responsible_user">
                {{ $user(selectedMilestone.responsible_user).full_name }}
              </span>
            </div>
          </div>
          <Button icon-left="lucide-plus" @click="openTaskDialog(selectedMilestone.name)">
            Add task
          </Button>
        </div>

        <div class="mt-4 h-1.5 overflow-hidden rounded bg-surface-gray-2">
          <div
            class="h-full rounded bg-surface-green-5 transition-all"
            :style="{ width: `${selectedMilestone.progress}%` }"
          />
        </div>

        <div v-if="selectedMilestone.description" class="prose-v3 mt-4 text-base text-ink-gray-7">
          <div v-html="selectedMilestone.description" />
        </div>

        <div v-if="selectedMilestone.tasks.length" class="mt-4 divide-y rounded border">
          <router-link
            v-for="task in selectedMilestone.tasks"
            :key="task.name"
            :to="{ name: 'SpaceTask', params: { spaceId, taskId: task.name } }"
            class="flex items-center gap-3 px-3 py-2.5 transition hover:bg-surface-gray-2"
          >
            <TaskStatusIcon :status="task.status" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-base font-medium text-ink-gray-8">{{ task.title }}</div>
              <div class="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-ink-gray-5">
                <span>#{{ task.name }}</span>
                <span v-if="task.assigned_to">{{ $user(task.assigned_to).full_name }}</span>
                <span v-if="task.due_date">{{ dayjsLocal(task.due_date).format('D MMM') }}</span>
              </div>
            </div>
          </router-link>
        </div>

        <div
          v-else
          class="mt-4 rounded border border-dashed py-5 text-center text-base text-ink-gray-5"
        >
          No tasks under this milestone
        </div>
      </div>
    </div>

    <Dialog title="New milestone" v-model:open="showMilestoneDialog">
      <div class="space-y-4">
        <FormControl
          label="Title"
          v-model="newMilestone.doc.title"
          required
          autofocus
          autocomplete="off"
        />
        <div class="grid grid-cols-2 gap-2">
          <Combobox
            placeholder="Owner"
            :options="userOptions"
            v-model="newMilestone.doc.responsible_user"
          />
          <Combobox
            placeholder="Lane"
            :options="laneOptions"
            allowCustomValue
            openOnFocus
            v-model="newMilestone.doc.lane"
          />
          <DatePicker
            v-model="newMilestone.doc.start_date"
            placeholder="Start date"
            format="D MMM, YYYY"
          />
          <DatePicker
            v-model="newMilestone.doc.target_date"
            placeholder="Target date"
            format="D MMM, YYYY"
          />
        </div>
        <FormControl label="Description" type="textarea" v-model="newMilestone.doc.description" />
        <ErrorMessage :message="newMilestone.error" />
      </div>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :loading="newMilestone.loading"
          @click="createMilestone"
        >
          Create
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  Badge,
  Button,
  Combobox,
  DatePicker,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingText,
  dayjsLocal,
  useNewDoc,
} from 'frappe-ui'
import EmptyStateBox from '@/components/EmptyStateBox.vue'
import SpaceTabs from '@/components/SpaceTabs.vue'
import TaskStatusIcon from '@/components/NewTaskDialog/TaskStatusIcon.vue'
import { showNewTaskDialog } from '@/components/NewTaskDialog'
import { activeUsers, useUser } from '@/data/users'
import { JourneyMilestone, useJourney } from '@/data/journey'
import { GPJourney, GPJourneyMilestone } from '@/types/doctypes'
import { Space } from '@/data/spaces'

const props = defineProps<{
  spaceId: string
  space?: Space
}>()

const showMilestoneDialog = ref(false)
const selectedMilestoneName = ref<string | null>(null)
const journey = useJourney(() => props.spaceId)
const DAY_WIDTH = 18
const LANE_LABEL_WIDTH = 140
const FALLBACK_SPAN_DAYS = 14
const TRACK_HEIGHT = 52
const LANE_VERTICAL_PADDING = 16
const DEFAULT_LANE = 'Unassigned'

const summary = computed(() => journey.data)
const selectedMilestone = computed(() => {
  let milestones = chartMilestones.value || []
  return (
    milestones.find((milestone) => milestone.name === selectedMilestoneName.value) || milestones[0]
  )
})

const newJourney = useNewDoc<GPJourney>('GP Journey', {
  title: '',
  project: '',
  description: '',
})

const newMilestone = useNewDoc<GPJourneyMilestone>('GP Journey Milestone', {
  title: '',
  journey: '',
  lane: '',
  start_date: '',
  responsible_user: '',
  target_date: '',
  description: '',
})

const userOptions = computed(() =>
  activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  })),
)

const laneOptions = computed(() =>
  unique((summary.value?.milestones || []).map((milestone) => normalizeLane(milestone.lane)))
    .filter((lane) => lane !== DEFAULT_LANE)
    .map((lane) => ({
      label: lane,
      value: lane,
    })),
)

const chartMilestones = computed(() => {
  let milestones = summary.value?.milestones || []
  let fallbackStart = dayjsLocal().startOf('month').subtract(1, 'month')
  return milestones.map((milestone, index) => {
    let start = getMilestoneStart(milestone) || fallbackStart.add(index * 18, 'day')
    let end = getMilestoneEnd(milestone) || start.add(FALLBACK_SPAN_DAYS, 'day')
    if (end.isBefore(start, 'day')) {
      end = start.add(1, 'day')
    }
    return {
      ...milestone,
      lane: normalizeLane(milestone.lane),
      chartStart: start.startOf('day'),
      chartEnd: end.startOf('day'),
    }
  })
})

const chartStart = computed(() => {
  let today = dayjsLocal().startOf('day')
  let dates = chartMilestones.value.map((milestone) => milestone.chartStart).concat(today)
  return startOfWeek(minDay(dates))
})

const chartEnd = computed(() => {
  let today = dayjsLocal().startOf('day')
  let dates = chartMilestones.value.map((milestone) => milestone.chartEnd).concat(today)
  return startOfWeek(maxDay(dates).add(21, 'day')).add(6, 'day')
})

const chartDays = computed(() => Math.max(chartEnd.value.diff(chartStart.value, 'day') + 1, 1))

const chartGridStyle = computed(() => ({
  gridTemplateColumns: `${LANE_LABEL_WIDTH}px repeat(${chartDays.value}, ${DAY_WIDTH}px)`,
  gridTemplateRows: `2.5rem ${chartRows.value.map((row) => `${row.trackCount * TRACK_HEIGHT + LANE_VERTICAL_PADDING}px`).join(' ')}`,
}))

const chartRows = computed(() => {
  let lanes = unique(chartMilestones.value.map((milestone) => milestone.lane))
  return lanes.map((lane) => {
    let milestones = assignTracks(
      chartMilestones.value.filter((milestone) => milestone.lane === lane),
    )
    let trackCount = Math.max(
      1,
      ...milestones.map((milestone) => Number(milestone.chartTrack || 0) + 1),
    )
    return { lane, milestones, trackCount }
  })
})

const weekSegments = computed(() => {
  let segments = []
  let cursor = chartStart.value
  while (!cursor.isAfter(chartEnd.value, 'day')) {
    let start = cursor.isBefore(chartStart.value) ? chartStart.value : cursor
    let end = cursor.add(6, 'day').isAfter(chartEnd.value) ? chartEnd.value : cursor.add(6, 'day')
    segments.push({
      key: cursor.format('YYYY-MM-DD'),
      label: cursor.format('D MMM'),
      start: start.diff(chartStart.value, 'day'),
      days: end.diff(start, 'day') + 1,
    })
    cursor = cursor.add(7, 'day')
  }
  return segments
})

const todayOffset = computed(() => {
  let today = dayjsLocal().startOf('day')
  if (today.isBefore(chartStart.value, 'day') || today.isAfter(chartEnd.value, 'day')) {
    return null
  }
  return today.diff(chartStart.value, 'day')
})

onMounted(reloadJourney)
watch(() => props.spaceId, reloadJourney)
watch(summary, (value) => {
  if (!value?.milestones.length) {
    selectedMilestoneName.value = null
    return
  }
  if (!value.milestones.find((milestone) => milestone.name === selectedMilestoneName.value)) {
    selectedMilestoneName.value = value.milestones[0].name
  }
})

function reloadJourney() {
  journey.submit({ space: props.spaceId })
}

function createJourney() {
  newJourney.doc.title = `${props.space?.title || 'Space'} Journey`
  newJourney.doc.project = props.spaceId
  newJourney.submit().then(reloadJourney)
}

function openMilestoneDialog() {
  if (!summary.value?.journey) return
  newMilestone.doc.title = ''
  newMilestone.doc.journey = summary.value.journey.name
  newMilestone.doc.lane = ''
  newMilestone.doc.start_date = ''
  newMilestone.doc.responsible_user = useUser('sessionUser').name
  newMilestone.doc.target_date = ''
  newMilestone.doc.description = ''
  showMilestoneDialog.value = true
}

function createMilestone() {
  if (!newMilestone.doc.title) {
    newMilestone.error = new Error('Milestone title is required')
    return
  }
  newMilestone.submit().then(() => {
    showMilestoneDialog.value = false
    reloadJourney()
  })
}

function openTaskDialog(milestone: string) {
  showNewTaskDialog({
    defaults: {
      project: props.spaceId,
      journey_milestone: milestone,
      assigned_to: useUser('sessionUser').name,
    },
    onSuccess: reloadJourney,
  })
}

function getMilestoneStart(milestone: JourneyMilestone) {
  let dates = [milestone.start_date]
    .concat(milestone.tasks.map((task) => task.start_date))
    .filter(Boolean)
  return dates.length ? minDay(dates.map((date) => dayjsLocal(date))) : null
}

function getMilestoneEnd(milestone: JourneyMilestone) {
  let dates = [milestone.target_date]
    .concat(milestone.tasks.map((task) => task.due_date))
    .filter(Boolean)
  return dates.length ? maxDay(dates.map((date) => dayjsLocal(date))) : null
}

function normalizeLane(lane?: string) {
  let value = String(lane || '').trim()
  return value || DEFAULT_LANE
}

function unique(values: string[]) {
  return values.filter((value, index) => values.indexOf(value) === index)
}

function startOfWeek(day: any) {
  return day.startOf('day').subtract(day.day(), 'day')
}

function assignTracks(milestones: any[]) {
  let trackEnds: any[] = []
  return milestones
    .slice()
    .sort((a, b) => {
      let startDiff = a.chartStart.diff(b.chartStart, 'day')
      return startDiff || a.chartEnd.diff(b.chartEnd, 'day')
    })
    .map((milestone) => {
      let track = trackEnds.findIndex((end) => milestone.chartStart.isAfter(end, 'day'))
      if (track === -1) {
        track = trackEnds.length
      }
      trackEnds[track] = milestone.chartEnd
      return { ...milestone, chartTrack: track }
    })
}

function minDay(days: any[]) {
  return days.reduce((min, day) => (day.isBefore(min, 'day') ? day : min), days[0])
}

function maxDay(days: any[]) {
  return days.reduce((max, day) => (day.isAfter(max, 'day') ? day : max), days[0])
}

function barStyle(milestone: any, rowIndex: number) {
  let startOffset = Math.max(milestone.chartStart.diff(chartStart.value, 'day'), 0)
  let spanDays = Math.max(milestone.chartEnd.diff(milestone.chartStart, 'day') + 1, 2)
  return {
    gridColumn: `${startOffset + 2} / span ${spanDays}`,
    gridRow: `${rowIndex + 2}`,
    height: `${TRACK_HEIGHT - 12}px`,
    marginTop: `${8 + Number(milestone.chartTrack || 0) * TRACK_HEIGHT}px`,
  }
}

function barClass(milestone: any) {
  return [
    {
      'shadow-sm ring-2 ring-outline-gray-3': selectedMilestoneName.value === milestone.name,
    },
  ]
}

function milestoneBarStyle(milestone: any) {
  let palette = milestonePalette(milestone)
  return {
    backgroundColor: palette.background,
    borderColor: palette.border,
    color: palette.text,
  }
}

function milestonePalette(milestone: any) {
  if (isComplete(milestone)) {
    return { background: '#dcfce7', border: '#22c55e', text: '#14532d' }
  }
  if (isPastDue(milestone)) {
    return { background: '#fee2e2', border: '#ef4444', text: '#7f1d1d' }
  }
  if (hasTasks(milestone)) {
    return { background: '#fef3c7', border: '#f59e0b', text: '#78350f' }
  }
  return { background: '#ffffff', border: '#d1d5db', text: '#374151' }
}

function hasTasks(milestone: any) {
  return Number(milestone.task_count || 0) > 0
}

function isComplete(milestone: any) {
  return (
    hasTasks(milestone) &&
    Number(milestone.done_task_count || 0) >= Number(milestone.task_count || 0)
  )
}

function isPastDue(milestone: any) {
  return (
    hasTasks(milestone) &&
    !isComplete(milestone) &&
    milestone.chartEnd.isBefore(dayjsLocal(), 'day')
  )
}

function statusClass(status: GPJourneyMilestone['status']) {
  return {
    'Not Started': 'text-ink-gray-6',
    'In Progress': 'text-ink-blue-3',
    Achieved: 'text-ink-green-3',
    Blocked: 'text-ink-red-3',
  }[status]
}
</script>
