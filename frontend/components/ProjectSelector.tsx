'use client';

import React, { useState } from 'react';
import { Project, createProject } from '@/lib/api';
import { Film, Plus, ChevronDown, Check } from 'lucide-react';

interface Props {
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (p: Project) => void;
  onProjectCreated: (p: Project) => void;
}

export default function ProjectSelector({
  projects,
  activeProject,
  onSelectProject,
  onProjectCreated,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setLoading(true);
    setError('');
    try {
      const proj = await createProject(newTitle.trim());
      onProjectCreated(proj);
      setNewTitle('');
      setIsCreating(false);
      setIsOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-card border border-border hover:border-accent-light transition-all text-sm font-medium"
      >
        <Film className="w-4 h-4 text-accent-light" />
        <span className="max-w-[180px] truncate">
          {activeProject ? activeProject.title : 'Select Project'}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 glass-panel rounded-xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="text-xs font-semibold text-gray-400 px-3 py-1.5 uppercase tracking-wider">
            Your Screenplay Projects
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1 my-1">
            {projects.length === 0 ? (
              <div className="px-3 py-2 text-xs text-gray-500 italic">No projects found.</div>
            ) : (
              projects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    onSelectProject(p);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left ${
                    activeProject?.id === p.id
                      ? 'bg-accent/20 text-accent-light font-semibold'
                      : 'hover:bg-cardHover text-gray-300'
                  }`}
                >
                  <span className="truncate">{p.title}</span>
                  {activeProject?.id === p.id && <Check className="w-4 h-4 text-accent-light" />}
                </button>
              ))
            )}
          </div>

          <div className="border-t border-border pt-2 mt-1">
            {isCreating ? (
              <form onSubmit={handleCreate} className="p-2 space-y-2">
                <input
                  type="text"
                  placeholder="Project Name..."
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-background border border-border rounded-md text-white focus:outline-none focus:border-accent"
                  autoFocus
                />
                {error && <div className="text-[10px] text-accent-rose">{error}</div>}
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={loading || !newTitle.trim()}
                    className="flex-1 px-2 py-1 text-xs bg-accent hover:bg-accent-hover rounded font-medium text-white disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="px-2 py-1 text-xs bg-cardHover text-gray-400 rounded hover:text-white"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setIsCreating(true)}
                className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 text-xs bg-accent/10 hover:bg-accent/20 text-accent-light rounded-lg font-medium transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Project</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
