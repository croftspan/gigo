'use client';

import React, { useState } from 'react';
import { Sidebar } from '../../../../components/Sidebar';

export default function NewTaskPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, project_id: 'default' }),
    });
  };

  return (
    <div className="layout">
      <Sidebar currentPath="/dashboard/tasks/new" />
      <main>
        <h1>Create New Task</h1>
        <form onSubmit={handleSubmit}>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Task title" />
          <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" />
          <button type="submit">Create Task</button>
        </form>
      </main>
    </div>
  );
}
