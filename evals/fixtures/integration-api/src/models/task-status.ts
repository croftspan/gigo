export type TaskStatus = 'draft' | 'active' | 'paused' | 'completed' | 'archived';

export const VALID_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  draft: ['active'],
  active: ['paused', 'completed'],
  paused: ['active'],
  completed: ['archived'],
  archived: [],
};

export function canTransition(from: TaskStatus, to: TaskStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}
