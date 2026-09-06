'use client';

import React from 'react';
import { Scene, IssueResponse } from '@/lib/api';
import { FileText, AlertTriangle, CheckCircle2, ArrowRight, Clock } from 'lucide-react';

interface Props {
  scenes: Scene[];
  issues: IssueResponse[];
  activeSceneNumber: number;
  onSelectScene: (sceneNum: number) => void;
}

export default function OutlineView({ scenes, issues, activeSceneNumber, onSelectScene }: Props) {
  return (
    <div className="flex-1 p-6 overflow-y-auto bg-app space-y-6 text-xs transition-colors">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-lg font-bold text-txtPrimary">Screenplay Structure Outline</h2>
          <p className="text-xs text-txtSecondary mt-0.5">
            Index of {scenes.length} scenes with continuity status and scene breakdown.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenes.map((sc) => {
          const sceneIssues = issues.filter(i => i.scene_number === sc.scene_number);
          const openIssues = sceneIssues.filter(i => i.status === 'OPEN' || i.status === 'NEEDS_REVIEW');
          const slugline = sc.raw_text.split('\n')[0] || `SCENE ${sc.scene_number}`;
          const isSelected = sc.scene_number === activeSceneNumber;

          return (
            <div
              key={sc.id}
              onClick={() => onSelectScene(sc.scene_number)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-3 shadow-md hover:shadow-lg ${
                isSelected
                  ? 'bg-card border-accent shadow-accent/10'
                  : 'bg-card/70 border-border hover:bg-card hover:border-accent/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full bg-secondary/15 border border-secondary/30 text-secondary font-bold text-[10px] uppercase font-mono">
                  Scene #{sc.scene_number}
                </span>

                {!sc.is_analyzed ? (
                  <span className="px-2 py-0.5 rounded-full bg-slate-500/15 border border-slate-500/30 text-slate-600 dark:text-slate-400 font-semibold text-[10px] flex items-center space-x-1" title="Scene has not been analyzed yet">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>Not Analyzed</span>
                  </span>
                ) : openIssues.length > 0 ? (
                  <span className="px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-700 dark:bg-rose-500/25 dark:border-rose-500/50 dark:text-rose-400 font-bold text-[10px] flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-rose-600 dark:text-rose-400" />
                    <span>{openIssues.length} Finding{openIssues.length > 1 ? 's' : ''}</span>
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-700 dark:bg-emerald-500/25 dark:border-emerald-500/50 dark:text-emerald-400 font-bold text-[10px] flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    <span>Clean</span>
                  </span>
                )}
              </div>

              <div>
                <h4 className="font-bold text-txtPrimary text-xs leading-snug font-mono line-clamp-1">
                  {slugline}
                </h4>
                <p className="text-txtSecondary text-[11px] mt-1 line-clamp-2 leading-relaxed">
                  {sc.raw_text.split('\n').slice(1).join(' ').trim() || 'Empty scene description.'}
                </p>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-txtMuted pt-2 border-t border-border/50">
                <span>{sc.raw_text.trim().split(/\s+/).length} words</span>
                <span className="text-accent-light font-semibold flex items-center space-x-1 group">
                  <span>Open in Editor</span>
                  <ArrowRight className="w-3 h-3 ml-0.5 transition-transform group-hover:translate-x-0.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
