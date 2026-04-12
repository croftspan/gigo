import { Task, ApiResponse, PaginationParams } from '../types';

export async function getTasks(params: PaginationParams): Promise<ApiResponse<Task[]>> {
  const response = await fetch(`/api/tasks?page=${params.page}&limit=${params.limit}`);
  const tasks = await db.tasks.findMany({
    skip: (params.page - 1) * params.limit,
    take: params.limit,
  });
  const total = await db.tasks.count();

  return {
    data: tasks.map(task => ({
      id: task.id,
      title: task.title,
      description: task.description,
      status: task.status,
      project_id: task.project_id,
      assignee_id: task.assignee_id,
      createdAt: task.created_at,
      updatedAt: task.updated_at,
    })),
    total,
  };
}

export async function getTask(id: string): Promise<Task> {
  const task = await db.tasks.findUnique({ where: { id } });
  if (!task) throw new NotFoundError('Task not found');

  return {
    id: task.id,
    title: task.title,
    description: task.description,
    status: task.status,
    project_id: task.project_id,
    assignee_id: task.assignee_id,
    createdAt: task.created_at,
    updatedAt: task.updated_at,
  };
}

export async function createTask(data: {
  title: string;
  description: string;
  project_id: string;
}): Promise<Task> {
  const task = await db.tasks.create({
    data: { ...data, status: 'draft' },
  });
  return task;
}

export async function deleteTask(id: string): Promise<{ deleted: boolean }> {
  await db.tasks.delete({ where: { id } });
  return { deleted: true };
}
