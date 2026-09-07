'use client';

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Project } from '@/lib/api';

import { Sparkles, Sun, Moon, Check, PlayCircle, Loader2, ChevronDown, Search, X, Folder, Plus, FolderPlus, Upload, Download, Trash2, Square, Pencil, HelpCircle } from 'lucide-react';
import ImportScreenplayModal from '@/components/Import/ImportScreenplayModal';
import ExportScreenplayModal from '@/components/Export/ExportScreenplayModal';
import { AboutModal } from '@/components/About/AboutModal';

interface Props {
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onCreateProject: (title: string) => Promise<void>;
  onRenameProject?: (projectId: string, newTitle: string) => Promise<void>;
  onDeleteProject?: (projectId: string) => Promise<void>;
  onImportSuccess?: () => void;
  activeTab: 'editor' | 'outline' | 'characters' | 'reasoning' | 'timeline' | 'settings';
  onSelectTab: (tab: 'editor' | 'outline' | 'characters' | 'reasoning' | 'timeline' | 'settings') => void;
  activeSceneNumber: number;
  activeSceneHeading?: string;
  totalScenesCount: number;
  analyzing: boolean;
  batchProgress?: { current: number; total: number; currentHeading?: string } | null;
  isStale?: boolean;
  saveStatus?: 'saved' | 'saving' | 'unsaved';
  onAnalyzeScene: () => void;
  onAnalyzeAllScenes: () => void;
  onStopAnalysis?: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export default function HeaderNav({
  projects,
  activeProject,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onImportSuccess,
  activeTab,
  onSelectTab,
  activeSceneNumber,
  activeSceneHeading,
  totalScenesCount,
  analyzing,
  batchProgress,
  isStale,
  saveStatus = 'saved',
  onAnalyzeScene,
  onAnalyzeAllScenes,
  onStopAnalysis,
  theme,
  onToggleTheme
}: Props) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [projectToRename, setProjectToRename] = useState<Project | null>(null);
  const [renameTitle, setRenameTitle] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredProjects = projects.filter(p =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectTitle.trim()) return;
    try {
      setCreating(true);
      await onCreateProject(newProjectTitle.trim());
      setNewProjectTitle('');
      setShowCreateModal(false);
    } catch (err) {
      console.error('Create project failed:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectToRename || !renameTitle.trim() || !onRenameProject) return;
    try {
      setRenaming(true);
      await onRenameProject(projectToRename.id, renameTitle.trim());
      setProjectToRename(null);
      setRenameTitle('');
    } catch (err) {
      console.error('Rename project failed:', err);
    } finally {
      setRenaming(false);
    }
  };

  return (
    <>
      <header className="h-14 border-b border bg-panel backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-50 text-xs select-none transition-colors">
      {/* Left: Project Selector & Draft info */}
      <div className="flex items-center space-x-3">
        {/* Searchable Project Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-1.5 font-bold text-txtPrimary hover:text-secondary focus:outline-none py-1 px-2 rounded-lg hover:bg-cardHover transition-colors text-xs"
          >
            <Folder className="w-3.5 h-3.5 text-secondary shrink-0" />
            <span className="truncate max-w-[160px] sm:max-w-[220px]">
              Projects / {activeProject?.title || 'Select Project'}
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-txtSecondary transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-1.5 w-64 rounded-xl bg-panel border border-border shadow-xl z-50 overflow-hidden flex flex-col p-2 text-xs">
              {/* Search Bar */}
              <div className="relative mb-2">
                <Search className="w-3.5 h-3.5 text-txtSecondary absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Search projects..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoFocus
                  className="w-full pl-8 pr-7 py-1.5 bg-cardHover border border-border rounded-lg text-txtPrimary placeholder-txtMuted text-xs focus:outline-none focus:border-secondary"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2 top-2 text-txtSecondary hover:text-txtPrimary"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Project Options List */}
              <div className="max-h-48 overflow-y-auto space-y-1">
                {filteredProjects.length === 0 ? (
                  <div className="p-3 text-center text-txtSecondary text-[11px]">
                    No projects found
                  </div>
                ) : (
                  filteredProjects.map((p) => {
                    const isSelected = p.id === activeProject?.id;
                    return (
                      <div
                        key={p.id}
                        className={`w-full px-2.5 py-1.5 rounded-lg flex items-center justify-between transition-colors group ${
                          isSelected
                            ? 'bg-accent/20 text-txtPrimary font-bold'
                            : 'hover:bg-cardHover text-txtSecondary hover:text-txtPrimary'
                        }`}
                      >
                        <button
                          onClick={() => {
                            onSelectProject(p);
                            setDropdownOpen(false);
                            setSearchQuery('');
                          }}
                          className="flex-1 text-left truncate flex items-center justify-between pr-1"
                        >
                          <span className="truncate">{p.title}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-secondary shrink-0 ml-1.5" />}
                        </button>
                        <div className="flex items-center space-x-0.5 shrink-0 opacity-60 group-hover:opacity-100">
                          {onRenameProject && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setProjectToRename(p);
                                setRenameTitle(p.title);
                                setDropdownOpen(false);
                              }}
                              className="p-1 rounded text-txtMuted hover:text-secondary hover:bg-secondary/10 transition-colors"
                              title={`Rename project "${p.title}"`}
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {onDeleteProject && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setProjectToDelete(p);
                                setDropdownOpen(false);
                              }}
                              className="p-1 rounded text-txtMuted hover:text-red-600 dark:hover:text-red-400 hover:bg-red-500/10 transition-colors"
                              title={`Delete project "${p.title}"`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Divider & Action Buttons */}
              <div className="pt-2 mt-1 border-t border-border space-y-1">
                <button
                  onClick={() => {
                    setShowCreateModal(true);
                    setDropdownOpen(false);
                  }}
                  className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-blue-600 dark:text-blue-400 hover:bg-cardHover font-bold transition-colors text-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>New Project...</span>
                </button>

                {activeProject && onRenameProject && (
                  <button
                    onClick={() => {
                      setProjectToRename(activeProject);
                      setRenameTitle(activeProject.title);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-txtSecondary hover:text-txtPrimary hover:bg-cardHover font-medium transition-colors text-xs"
                  >
                    <Pencil className="w-3.5 h-3.5 text-secondary" />
                    <span>Rename Project...</span>
                  </button>
                )}

                {activeProject && (
                  <button
                    onClick={() => {
                      setShowImportModal(true);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-txtSecondary hover:text-txtPrimary hover:bg-cardHover font-medium transition-colors text-xs"
                  >
                    <Upload className="w-3.5 h-3.5 text-secondary" />
                    <span>Import Screenplay...</span>
                  </button>
                )}

                {activeProject && (
                  <button
                    onClick={() => {
                      setShowExportModal(true);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-txtSecondary hover:text-txtPrimary hover:bg-cardHover font-medium transition-colors text-xs"
                  >
                    <Download className="w-3.5 h-3.5 text-secondary" />
                    <span>Export Screenplay...</span>
                  </button>
                )}

                {activeProject && onDeleteProject && (
                  <button
                    onClick={() => {
                      setProjectToDelete(activeProject);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-red-600 dark:text-red-400 hover:bg-red-500/10 font-bold transition-colors text-xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Current Project...</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-border hidden sm:block" />


        {/* Workspace Mode Tabs */}
        <div className="hidden sm:flex items-center space-x-1 font-semibold text-txtSecondary">
          <button
            onClick={() => onSelectTab('editor')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'editor' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Editor
          </button>
          <button
            onClick={() => onSelectTab('outline')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'outline' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Outline
          </button>
          <button
            onClick={() => onSelectTab('characters')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'characters' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Characters
          </button>
          <button
            onClick={() => onSelectTab('reasoning')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'reasoning' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Reasoning
          </button>
          <button
            onClick={() => onSelectTab('timeline')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'timeline' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Timeline
          </button>
          <button
            onClick={() => onSelectTab('settings')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'settings' ? 'bg-accent/20 text-txtPrimary font-bold' : 'hover:text-txtPrimary'}`}
          >
            Settings
          </button>
        </div>
      </div>


      {/* Center: Current Scene Badge */}
      <div className="hidden md:flex items-center space-x-2 text-txtSecondary font-mono text-[11px]">
        <span className="w-2 h-2 rounded-full bg-secondary animate-pulse flex-shrink-0" />
        <span className="truncate max-w-[180px] lg:max-w-[280px]">
          Scene {activeSceneNumber} {activeSceneHeading ? `• ${activeSceneHeading}` : ''}
        </span>
      </div>

      {/* Right Actions: Sync, Analyze Buttons, Theme Toggle, User Avatar */}
      <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
        <div className="hidden lg:flex items-center space-x-1.5 text-txtSecondary text-[11px] font-medium">
          {saveStatus === 'saving' ? (
            <>
              <Loader2 className="w-3.5 h-3.5 text-tertiary animate-spin" />
              <span className="text-tertiary font-semibold">Saving...</span>
            </>
          ) : saveStatus === 'unsaved' ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
              <span className="text-tertiary font-semibold">Unsaved</span>
            </>
          ) : (
            <>
              <Check className="w-3.5 h-3.5 text-secondary" />
              <span>Saved</span>
            </>
          )}
        </div>

        {/* Stale Analysis Warning Badge */}
        {isStale && (
          <span className="px-2 py-0.5 rounded-full bg-tertiary/20 border border-tertiary/40 text-tertiary text-[10px] font-mono font-bold animate-pulse flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
            <span>Stale Text</span>
          </span>
        )}

        {/* Analyze Active Scene Button */}
        <button
          onClick={onAnalyzeScene}
          disabled={analyzing}
          className="px-3.5 py-1.5 rounded-lg text-white font-bold flex items-center space-x-1.5 shadow-sm transition-all disabled:opacity-50 text-[11px] bg-amber-500 hover:bg-amber-600 active:bg-amber-700"
          title="Analyze active scene with unified Script Supervisor pipeline"
        >
          <Sparkles className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? (batchProgress ? `Sc. ${batchProgress.current}/${batchProgress.total}` : 'Analyzing...') : isStale ? 'Re-Analyze Scene' : 'Analyze Scene'}</span>
        </button>

        {/* Analyze All Scenes / Stop Analysis Button */}
        {analyzing && batchProgress ? (
          <button
            onClick={onStopAnalysis}
            className="px-2.5 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-600 dark:text-red-400 font-bold flex items-center space-x-1.5 transition-all text-[11px] animate-pulse cursor-pointer shadow-sm"
            title="Stop batch scene analysis midway"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Stop ({batchProgress.current}/{batchProgress.total})</span>
          </button>
        ) : (
          <button
            onClick={onAnalyzeAllScenes}
            disabled={analyzing}
            className="px-2.5 py-1.5 rounded-lg bg-cardHover border border-border hover:border-secondary text-txtPrimary font-semibold flex items-center space-x-1.5 transition-all disabled:opacity-50 text-[11px]"
            title={`Sequentially analyze all ${totalScenesCount} scenes in project`}
          >
            <PlayCircle className="w-3.5 h-3.5 text-secondary" />
            <span className="hidden sm:inline">Analyze All ({totalScenesCount})</span>
          </button>
        )}

        {/* How It Works / About Button */}
        <button
          onClick={() => setShowAboutModal(true)}
          className="px-2.5 py-1.5 rounded-lg bg-cardHover border border-border hover:border-blue-500 text-txtPrimary font-semibold flex items-center space-x-1.5 transition-all text-[11px]"
          title="How Script Supervisor works"
        >
          <HelpCircle className="w-3.5 h-3.5 text-blue-500" />
          <span className="hidden sm:inline">How It Works</span>
        </button>

        {/* Dark/Light Theme Switcher */}
        <button
          onClick={onToggleTheme}
          className="p-1.5 rounded-lg bg-cardHover border border-border text-txtSecondary hover:text-txtPrimary transition-colors"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-tertiary" /> : <Moon className="w-4 h-4 text-secondary" />}
        </button>
      </div>
    </header>

    {/* About / How It Works Modal */}
    <AboutModal 
      isOpen={showAboutModal} 
      onClose={() => setShowAboutModal(false)} 
      theme={theme} 
    />

    {/* Create Project Modal (Portaled directly to document.body for true viewport centering) */}
    {showCreateModal && mounted && createPortal(
      <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
        <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-txtPrimary relative">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400 shrink-0">
                <FolderPlus className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-txtPrimary">Create New Project</h3>
                <p className="text-xs text-txtSecondary mt-0.5">Start a fresh screenplay project with independent story state.</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(false)}
              className="p-1 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleCreateSubmit} className="space-y-4 pt-1">
            <div>
              <label className="block text-xs font-bold text-txtPrimary mb-1.5">Project Title</label>
              <input
                type="text"
                placeholder="e.g. 'The Lost Horizon' or 'Nightfall'"
                value={newProjectTitle}
                onChange={(e) => setNewProjectTitle(e.target.value)}
                className="w-full px-4 py-2.5 bg-panel border border-border rounded-xl text-xs text-txtPrimary placeholder:text-txtMuted focus:outline-none focus:border-secondary focus:ring-2 focus:ring-blue-500/20 transition-all font-medium"
                autoFocus
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating || !newProjectTitle.trim()}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg disabled:opacity-50 shrink-0"
              >
                {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                Create Project
              </button>
            </div>
          </form>
        </div>
      </div>,
      document.body
    )}

    {/* Import Screenplay Modal */}
    {activeProject && (
      <ImportScreenplayModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        projectId={activeProject.id}
        projectName={activeProject.title}
        onImportSuccess={() => {
          if (onImportSuccess) onImportSuccess();
        }}
        theme={theme}
      />
    )}

    {/* Export Screenplay Modal */}
    {activeProject && (
      <ExportScreenplayModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        projectId={activeProject.id}
        projectName={activeProject.title}
        theme={theme}
      />
    )}

    {/* Delete Project Confirmation Modal */}
    {projectToDelete && mounted && createPortal(
      <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
        <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-txtPrimary relative">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-red-500/10 border border-red-500/20 rounded-xl text-red-600 dark:text-red-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-txtPrimary">Delete Project</h3>
                <p className="text-xs text-txtSecondary mt-0.5">This action cannot be undone.</p>
              </div>
            </div>
            <button
              onClick={() => setProjectToDelete(null)}
              className="p-1 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="bg-panel border border-border rounded-xl p-3.5 text-xs space-y-1.5">
            <p className="font-semibold text-txtPrimary">
              Are you sure you want to permanently delete <span className="font-bold text-red-500 font-mono">"{projectToDelete.title}"</span>?
            </p>
            <p className="text-txtMuted text-[11px]">
              All associated screenplay scenes, character profiles, story state, research tasks, and issues will be permanently deleted.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setProjectToDelete(null)}
              className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={deleting}
              onClick={async () => {
                if (!projectToDelete || !onDeleteProject) return;
                try {
                  setDeleting(true);
                  await onDeleteProject(projectToDelete.id);
                  setProjectToDelete(null);
                } catch (err) {
                  console.error('Delete project failed:', err);
                } finally {
                  setDeleting(false);
                }
              }}
              className="px-5 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg disabled:opacity-50 shrink-0"
            >
              {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              Delete Project
            </button>
          </div>
        </div>
      </div>,
      document.body
    )}

    {/* Rename Project Modal */}
    {projectToRename && mounted && createPortal(
      <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
        <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-txtPrimary relative">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-secondary/10 border border-secondary/20 rounded-xl text-secondary shrink-0">
                <Pencil className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-txtPrimary">Rename Project</h3>
                <p className="text-xs text-txtSecondary mt-0.5">Enter a new title for this project.</p>
              </div>
            </div>
            <button
              onClick={() => { setProjectToRename(null); setRenameTitle(''); }}
              className="p-1 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleRenameSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-txtSecondary mb-1.5">
                Project Title
              </label>
              <input
                type="text"
                value={renameTitle}
                onChange={(e) => setRenameTitle(e.target.value)}
                placeholder="Enter new project title..."
                autoFocus
                className="w-full px-3.5 py-2 bg-panel border border-border rounded-xl text-txtPrimary text-xs focus:outline-none focus:border-secondary font-medium"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => { setProjectToRename(null); setRenameTitle(''); }}
                className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!renameTitle.trim() || renaming}
                className="px-5 py-2.5 bg-secondary hover:opacity-90 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg disabled:opacity-50 shrink-0"
              >
                {renaming ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Pencil className="w-3.5 h-3.5" />}
                Save Title
              </button>
            </div>
          </form>
        </div>
      </div>,
      document.body
    )}
  </>
);
}
