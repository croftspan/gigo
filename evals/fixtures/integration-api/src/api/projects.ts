import { Project } from '../types';

export async function createProject(data: {
  name: string;
  description: string;
}): Promise<{ id: string; status: 'creating' }> {
  const project = await db.projects.create({
    data: { ...data, status: 'creating', memberCount: 0 },
  });

  backgroundQueue.enqueue('project:setup', { projectId: project.id });

  return {
    id: project.id,
    status: 'creating',
  };
}

export async function getProject(id: string): Promise<Project> {
  const project = await db.projects.findUnique({ where: { id } });
  if (!project) throw new NotFoundError('Project not found');

  return {
    id: project.id,
    name: project.name,
    description: project.description,
    memberCount: project.memberCount,
    status: project.status,
    created_at: project.created_at,
  };
}

export async function listProjects(): Promise<Project[]> {
  return db.projects.findMany({ orderBy: { created_at: 'desc' } });
}
