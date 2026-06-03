import { computed, MaybeRefOrGetter, toValue, watch } from 'vue'
import { useList } from 'frappe-ui'
import { GPJourneyMilestone } from '@/types/doctypes'

interface MilestoneOption {
  label: string
  value: string
}

export function useMilestoneOptions(project: MaybeRefOrGetter<string | undefined>) {
  const projectName = computed(() => {
    let value = toValue(project)
    return value ? String(value) : ''
  })

  const milestones = useList<Pick<GPJourneyMilestone, 'name' | 'title'>>({
    doctype: 'GP Journey Milestone',
    fields: ['name', 'title'],
    filters: () => ({
      project: projectName.value || '__no_project__',
    }),
    orderBy: 'sort_order asc, creation asc',
    limit: 999,
    initialData: [],
    immediate: false,
  })

  watch(
    projectName,
    (value) => {
      if (value) {
        milestones.reload()
      }
    },
    { immediate: true },
  )

  const options = computed<MilestoneOption[]>(() => {
    return [
      {
        label: 'No milestone',
        value: '<no_milestone>',
      },
    ].concat(
      (milestones.data || []).map((milestone) => ({
        label: milestone.title,
        value: String(milestone.name),
      })),
    )
  })

  return { milestones, options }
}
