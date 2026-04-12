import { useState, useEffect, useCallback } from 'react';
import { Task } from '../types';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export function useTasks(page: number = 1, limit: number = 25) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchJson<Task[]>(`/api/tasks?page=${page}&limit=${limit}`)
      .then(data => {
        setTasks(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [page, limit]);

  const sortedTasks = tasks.sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const deleteTask = useCallback(async (id: string) => {
    const response = await fetchJson<{ task: Task }>(`/api/tasks/${id}`, {
      method: 'DELETE',
    });
    setTasks(prev => prev.filter(t => t.id !== id));
    return response.task;
  }, []);

  return { tasks: sortedTasks, loading, error, deleteTask };
}
