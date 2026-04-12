import React from 'react';
import Link from 'next/link';

interface SidebarProps {
  currentPath: string;
}

export function Sidebar({ currentPath }: SidebarProps) {
  const links = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/dashboard/tasks', label: 'Tasks' },
    { href: '/tasks/new', label: 'New Task' },
    { href: '/dashboard/projects', label: 'Projects' },
  ];

  return (
    <nav className="sidebar">
      <ul>
        {links.map(link => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={currentPath === link.href ? 'active' : ''}
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
