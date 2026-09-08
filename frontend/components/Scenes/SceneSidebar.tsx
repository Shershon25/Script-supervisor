'use client';

import React, { useState } from 'react';
import { Scene, IssueResponse } from '@/lib/api';
import { Search, Plus, ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  scenes: Scene[];
  activeSceneNumber: number;
  issues?: IssueResponse[];
  onSelectScene: (scene: Scene) => void;
  onAddScene: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function SceneSidebar({
  scenes,
  activeSceneNumber,
  issues = [],
  onSelectScene,
  onAddScene,
  collapsed,
  onToggleCollapse
}: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearchInput, setShowSearchInput] = useState(false);

  const filteredScenes = scenes.filter((s) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      s.scene_number.toString() === term ||
      s.raw_text.toLowerCase().includes(term)
    );
  });

  const getSlugline = (text: string) => {
    const lines = text.trim().split('\n').map(l => l.trim()).filter(Boolean);
    // Find the first line containing INT. or EXT. or INT/EXT.
    const headingLine = lines.find(l => /^(?:INT\.|EXT\.|INT\/EXT\.|I\/E\.)/i.test(l));
    if (headingLine) {
      return headingLine.substring(0, 26).toUpperCase();
    }
    // Fall back to first non-transition line (e.g. skip FADE IN:)
    const contentLine = lines.find(l => !/^(?:FADE IN:|FADE OUT|CUT TO:)/i.test(l)) || lines[0] || '';
    return contentLine.substring(0, 26).toUpperCase();
  };

  if (collapsed) {
    return (
      <div className="w-12 border-r border bg-panel flex flex-col items-center py-4 space-y-4 transition-colors">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg bg-cardHover text-txtSecondary hover:text-txtPrimary"
          title="Expand Scene Navigator"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <div className="writing-mode-vertical text-[10px] font-bold uppercase tracking-wider text-txtMuted">
          Scenes ({scenes.length})
        </div>
      </div>
    );
  }

  return (
    <aside className="w-56 border-r border bg-panel flex flex-col h-full select-none text-xs transition-colors">
      {/* Sidebar Header */}
      <div className="p-3 border-b border flex items-center justify-between font-bold text-txtPrimary">
        <div className="flex items-center space-x-1.5">
          <span className="uppercase text-[11px] tracking-wider">Scenes ({scenes.length})</span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowSearchInput(!showSearchInput)}
            className="p-1 rounded hover:bg-cardHover text-txtSecondary hover:text-txtPrimary"
            title="Search scenes"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded hover:bg-cardHover text-txtSecondary hover:text-txtPrimary"
            title="Collapse sidebar"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Live Search Input */}
      {showSearchInput && (
        <div className="p-2 border-b border bg-card">
          <input
            type="text"
            placeholder="Search scene, slugline..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-2.5 py-1 bg-cardHover border border rounded text-xs text-txtPrimary placeholder-txtMuted focus:outline-none focus:border-accent"
            autoFocus
          />
        </div>
      )}

      {/* Scenes List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-[11px]">
        {filteredScenes.map((s) => {
          const isActive = s.scene_number === activeSceneNumber;
          const slug = getSlugline(s.raw_text);

          // Calculate real open issues for this scene
          const sceneIssues = issues.filter(
            (i) => i.scene_number === s.scene_number && (i.status === 'OPEN' || i.status === 'NEEDS_REVIEW')
          );
          const hasContinuityGap = sceneIssues.some((i) => !i.issue_type.includes('REALITY'));
          const hasResearchCheck = sceneIssues.some((i) => i.issue_type.includes('REALITY') || i.issue_type.includes('RESEARCH'));

          return (
            <button
              key={s.id}
              onClick={() => onSelectScene(s)}
              className={`w-full text-left px-2.5 py-2 rounded-lg transition-all flex items-center justify-between ${
                isActive
                  ? 'bg-secondary/15 border border-secondary/40 font-bold text-txtPrimary shadow-sm'
                  : 'hover:bg-cardHover text-txtSecondary'
              }`}
            >
              <div className="flex items-center space-x-2 truncate">
                <span className={`w-5 text-right font-semibold ${isActive ? 'text-secondary font-bold' : 'text-txtMuted'}`}>
                  {s.scene_number}
                </span>
                <span className="truncate">{slug}</span>
              </div>

              {/* Real Issue Indicator Dots */}
              <div className="flex items-center space-x-1 flex-shrink-0">
                {!s.is_analyzed && (
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400/50" title="Not Analyzed Yet" />
                )}
                {hasContinuityGap && <span className="w-1.5 h-1.5 rounded-full bg-tertiary" title="Continuity/Knowledge Issue" />}
                {hasResearchCheck && <span className="w-1.5 h-1.5 rounded-full bg-secondary" title="Reality/Research Check" />}
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Add Scene Button */}
      <div className="p-2 border-t border">
        <button
          onClick={onAddScene}
          className="w-full py-1.5 px-3 rounded-lg bg-cardHover border border hover:bg-card text-txtPrimary font-semibold flex items-center justify-center space-x-1.5 transition-colors text-xs"
        >
          <Plus className="w-3.5 h-3.5 text-accent-light" />
          <span>Add Scene</span>
        </button>
      </div>
    </aside>
  );
}
