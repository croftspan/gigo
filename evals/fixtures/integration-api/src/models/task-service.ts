import { TaskStatus } from './task-status';

export class TaskService {
  async transition(taskId: string, newStatus: TaskStatus): Promise<void> {
    const task = await db.tasks.findUnique({ where: { id: taskId } });
    if (!task) throw new NotFoundError('Task not found');

    switch (task.status) {
      case 'draft':
        if (newStatus !== 'active') {
          throw new InvalidTransitionError(task.status, newStatus);
        }
        break;
      case 'active':
        if (newStatus !== 'completed' && newStatus !== 'paused') {
          throw new InvalidTransitionError(task.status, newStatus);
        }
        break;
      default:
        throw new InvalidTransitionError(task.status, newStatus);
    }

    await db.tasks.update({
      where: { id: taskId },
      data: { status: newStatus, updated_at: new Date().toISOString() },
    });
  }
}
