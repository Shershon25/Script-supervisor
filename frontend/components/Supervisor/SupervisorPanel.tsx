'use client';

import React, { useState } from 'react';
import { IssueResponse, StoryStateResponse } from '@/lib/api';
import FindingCard from './FindingCard';
import CanonMemoryView from './CanonMemoryView';
import ResearchView from './ResearchView';
import { Settings, ShieldCheck, Filter, Globe, Layers, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  projectId: string;
  issues: IssueResponse[];
  activeSceneNumber?: number;
  storyState: StoryStateResponse | null;
  loading: boolean;
  onSelectSceneNumber?: (sceneNum: number) => void;
  onReviewIssue: (issueId: string, action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN', resolutionType?: string, note?: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function SupervisorPanel({
  projectId,
  issues,
  activeSceneNumber = 1,
  storyState,
  loading,
  onSelectSceneNumber,
  onReviewIssue,
  collapsed = false,
  onToggleCollapse
}: Props) {
  const [activeTab, setActiveTab] = useState<'findings' | 'memory' | 'research'>('findings');
  const [findingsFilter, setFindingsFilter] = useState<'open' | 'audit' | 'all'>('open');
  const [scopeFilter, setScopeFilter] = useState<'project' | 'scene'>('project');
  const [panelWidth, setPanelWidth] = useState<number>(320); // Default width: 320px (min width)
  const isResizingRef = React.useRef(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isResizingRef.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isResizingRef.current) return;
      const newWidth = window.innerWidth - moveEvent.clientX;
      const minWidth = 320; // Minimum width set to current width (320px)
      const maxWidth = Math.min(800, window.innerWidth - 300);
      setPanelWidth(Math.max(minWidth, Math.min(maxWidth, newWidth)));
    };

    const handleMouseUp = () => {
      isResizingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  // 1. Filter by Scope (Entire Project vs Active Scene)
  const scopedIssues = scopeFilter === 'scene'
    ? issues.filter(i => i.scene_number === activeSceneNumber)
    : issues;

  // 2. Filter by Review Status
  const openIssues = scopedIssues.filter(i => i.status === 'OPEN' || i.status === 'NEEDS_REVIEW');
  const auditIssues = scopedIssues.filter(i => i.status === 'ACCEPTED' || i.status === 'IGNORED' || i.status === 'RESOLVED');

  const displayedIssues = findingsFilter === 'open'
    ? openIssues
    : findingsFilter === 'audit'
    ? auditIssues
    : scopedIssues;

  if (collapsed) {
    return (
      <aside className="w-12 border-l border bg-panel flex flex-col items-center py-4 space-y-4 select-none text-xs transition-colors shrink-0">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg bg-cardHover text-txtSecondary hover:text-txtPrimary transition-colors"
          title="Expand Supervisor Panel"
        >
          <ChevronLeft className="w-4 h-4 text-accent-light" />
        </button>
        {openIssues.length > 0 && (
          <span className="px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-500 text-[10px] font-mono font-bold" title={`${openIssues.length} open findings`}>
            {openIssues.length}
          </span>
        )}
        <div className="writing-mode-vertical text-[10px] font-bold uppercase tracking-wider text-txtMuted pt-2">
          SUPERVISOR
        </div>
      </aside>
    );
  }

  return (
    <aside 
      style={{ width: `${panelWidth}px`, minWidth: '320px' }}
      className="relative border-l border bg-panel flex flex-col h-full select-none text-xs transition-colors shrink-0"
    >
      {/* Resizable Border Handle */}
      <div
        onMouseDown={handleMouseDown}
        className="absolute -left-1 top-0 bottom-0 w-2 cursor-col-resize hover:bg-accent/40 active:bg-accent transition-colors z-30"
        title="Drag left or right to resize Supervisor panel (minimum width: 320px)"
      />
      {/* Header Bar */}
      <div className="p-3 border-b border flex items-center justify-between font-bold text-txtPrimary">
        <div className="flex items-center space-x-1.5 uppercase text-[11px] tracking-wider">
          <Settings className="w-3.5 h-3.5 text-accent-light" />
          <span>SUPERVISOR</span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 text-[10px] font-mono font-bold text-emerald-700 dark:text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Synced</span>
          </div>

          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded hover:bg-cardHover text-txtSecondary hover:text-txtPrimary transition-colors"
              title="Collapse Supervisor panel"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Scope Filter Bar */}
      <div className="px-3 py-1.5 border-b border bg-card/60 flex items-center justify-between text-[10px] font-mono">
        <span className="text-txtMuted uppercase tracking-wider font-semibold">Scope:</span>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setScopeFilter('project')}
            className={`px-2 py-0.5 rounded transition-colors flex items-center space-x-1 ${
              scopeFilter === 'project' ? 'bg-secondary/20 text-secondary font-bold border border-secondary/40' : 'text-txtSecondary hover:text-txtPrimary'
            }`}
            title="Show findings for all scenes in screenplay"
          >
            <Globe className="w-2.5 h-2.5" />
            <span>Entire Script</span>
          </button>
          <button
            onClick={() => setScopeFilter('scene')}
            className={`px-2 py-0.5 rounded transition-colors flex items-center space-x-1 ${
              scopeFilter === 'scene' ? 'bg-secondary/20 text-secondary font-bold border border-secondary/40' : 'text-txtSecondary hover:text-txtPrimary'
            }`}
            title="Show findings for active scene only"
          >
            <Layers className="w-2.5 h-2.5" />
            <span>Sc. #{activeSceneNumber}</span>
          </button>
        </div>
      </div>

      {/* Supervisor Navigation Tabs */}
      <div className="flex items-center border-b border bg-card/40 font-semibold text-txtSecondary p-1">
        <button
          onClick={() => setActiveTab('findings')}
          className={`flex-1 py-1.5 text-center rounded-lg transition-colors flex items-center justify-center space-x-1 ${
            activeTab === 'findings' ? 'bg-card text-txtPrimary font-bold shadow-sm' : 'hover:text-txtPrimary'
          }`}
        >
          <span>Findings</span>
          <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-500 text-[10px] font-mono">
            {openIssues.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('memory')}
          className={`flex-1 py-1.5 text-center rounded-lg transition-colors flex items-center justify-center space-x-1 ${
            activeTab === 'memory' ? 'bg-card text-txtPrimary font-bold shadow-sm' : 'hover:text-txtPrimary'
          }`}
        >
          <span>Canon Memory</span>
        </button>

        <button
          onClick={() => setActiveTab('research')}
          className={`flex-1 py-1.5 text-center rounded-lg transition-colors flex items-center justify-center space-x-1 ${
            activeTab === 'research' ? 'bg-card text-txtPrimary font-bold shadow-sm' : 'hover:text-txtPrimary'
          }`}
        >
          <span>Research</span>
        </button>
      </div>

      {/* Findings Filter Dropdown Bar */}
      {activeTab === 'findings' && (
        <div className="px-3 py-2 border-b border bg-card/20 flex items-center justify-between text-[10px]">
          <span className="font-bold text-txtMuted uppercase tracking-wider flex items-center space-x-1">
            <Filter className="w-3 h-3 text-accent-light" />
            <span>Filter:</span>
          </span>

          <div className="relative">
            <select
              value={findingsFilter}
              onChange={(e) => setFindingsFilter(e.target.value as 'open' | 'audit' | 'all')}
              className="bg-card border border-accent/30 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-txtPrimary focus:outline-none focus:border-accent cursor-pointer shadow-sm hover:border-accent transition-all pr-6 appearance-none font-mono"
            >
              <option value="open">Open Findings ({openIssues.length})</option>
              <option value="audit">Audit History ({auditIssues.length})</option>
              <option value="all">All Findings ({scopedIssues.length})</option>
            </select>
            <ChevronDown className="w-3 h-3 text-txtMuted absolute right-2 top-1.5 pointer-events-none" />
          </div>
        </div>
      )}

      {/* Tab Panel Content */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden p-3">
        {activeTab === 'findings' ? (
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {displayedIssues.length === 0 ? (
              <div className="p-6 text-center text-txtSecondary space-y-2">
                <ShieldCheck className="w-8 h-8 text-emerald-500 mx-auto" />
                <h4 className="font-bold text-txtPrimary text-xs">
                  {findingsFilter === 'open' ? 'Looking Good!' : findingsFilter === 'audit' ? 'No Audit Trail Yet' : 'No Issues'}
                </h4>
                <p className="text-[11px] text-txtMuted leading-relaxed">
                  {findingsFilter === 'open'
                    ? 'No open continuity or knowledge issues found in this scope.'
                    : findingsFilter === 'audit'
                    ? 'No reviewed or resolved issues in audit history.'
                    : 'No issues recorded for this scope.'}
                </p>
              </div>
            ) : (
              displayedIssues.map((issue) => (
                <FindingCard
                  key={issue.id}
                  issue={issue}
                  onSelectSceneNumber={onSelectSceneNumber}
                  onReview={(action, resType, note) => onReviewIssue(issue.id, action, resType, note)}
                />
              ))
            )}
          </div>
        ) : activeTab === 'memory' ? (
          <CanonMemoryView storyState={storyState} onSelectSceneNumber={onSelectSceneNumber} />
        ) : (
          <div className="flex-1 overflow-y-auto min-h-0 pr-1">
            <ResearchView
              projectId={projectId}
              activeSceneNumber={activeSceneNumber}
              scopeFilter={scopeFilter}
              onSelectSceneNumber={onSelectSceneNumber}
            />
          </div>
        )}
      </div>
    </aside>
  );
}
