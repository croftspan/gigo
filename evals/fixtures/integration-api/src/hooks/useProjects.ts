import { useState, useCallback } from 'react';
import { Project } from '../types';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  const createProject = useCallback(async (data: { name: string; description: string }) => {
    const response = await fetchJson<Project>('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const newProject: Project = {
      id: response.id,
      name: data.name,
      description: data.description,
      memberCount: response.memberCount,
      status: response.status,
      created_at: new Date().toISOString(),
    };

    setProjects(prev => [newProject, ...prev]);
    return newProject;
  }, []);

  return { projects, loading, createProject };
}
