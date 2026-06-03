import { useCall } from 'frappe-ui'
import { GPJourney, GPJourneyMilestone, GPTask } from '@/types/doctypes'

export interface JourneyTask extends Pick<
  GPTask,
  | 'name'
  | 'title'
  | 'status'
  | 'priority'
  | 'assigned_to'
  | 'start_date'
  | 'due_date'
  | 'project'
  | 'journey_milestone'
> {}

export interface JourneyMilestone extends Pick<
  GPJourneyMilestone,
  | 'name'
  | 'title'
  | 'description'
  | 'lane'
  | 'start_date'
  | 'responsible_user'
  | 'target_date'
  | 'status'
  | 'achieved_at'
  | 'achieved_by'
  | 'sort_order'
> {
  tasks: JourneyTask[]
  task_count: number
  done_task_count: number
  progress: number
}

export interface JourneySummary {
  journey: Pick<GPJourney, 'name' | 'title' | 'description' | 'project'>
  milestones: JourneyMilestone[]
  progress: {
    task_count: number
    done_task_count: number
    percent: number
  }
}

export function useJourney(spaceId: () => string) {
  return useCall<JourneySummary | null, { space: string }>({
    url: '/api/v2/method/gameplan.gameplan.doctype.gp_journey.gp_journey.get_for_space',
    immediate: false,
  })
}
