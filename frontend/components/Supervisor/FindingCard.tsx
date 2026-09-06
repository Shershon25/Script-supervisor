'use client';

import React, { useState } from 'react';
import { IssueResponse } from '@/lib/api';
import { AlertTriangle, ShieldCheck, Eye, CheckCircle2 } from 'lucide-react';

interface Props {
  issue: IssueResponse;
  onSelectSceneNumber?: (sceneNum: number) => void;
  onReview: (action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN', resolutionType?: string, note?: string) => void;
}

function getSuggestionText(issue: IssueResponse): string {
  if (issue.issue_type.includes('LOCATION')) {
    return `Add a scene depicting travel or location transition prior to Scene ${issue.scene_number || 'N'}, or clarify character location in dialogue.`;
  }
  if (issue.issue_type.includes('FACT')) {
    return `Align fact values across preceding scenes or confirm this is an intentional character change.`;
  }
  if (issue.issue_type.includes('KNOWLEDGE')) {
    return `Add an earlier scene where character acquires this information or clarify source in dialogue.`;
  }
  if (issue.issue_type.includes('OBJECT') || issue.issue_type.includes('OWNERSHIP')) {
    return `Add an object transfer event (give/take) or update item possession details.`;
  }
  return `Review narrative continuity for ${issue.title.toLowerCase()} or mark as intentional writer choice.`;
}

export default function FindingCard({ issue, onSelectSceneNumber, onReview }: Props) {
  const [submitting, setSubmitting] = useState(false);

  const isKnowledge = issue.issue_type.includes('KNOWLEDGE');
  const isLocation = issue.issue_type.includes('LOCATION');
  const isObject = issue.issue_type.includes('OBJECT') || issue.issue_type.includes('OWNERSHIP');
  const isProcedure = issue.issue_type.includes('REALITY') || issue.title.includes('Procedure') || issue.issue_type.includes('RESEARCH');
  const isResolved = issue.status === 'RESOLVED' || issue.status === 'ACCEPTED' || issue.status === 'IGNORED';

  const confidencePct = Math.round(issue.confidence * 100);

  const handleAction = async (action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN', resType?: string) => {
    setSubmitting(true);
    try {
      await onReview(action, resType, `Writer decision for ${issue.title}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Theme-aware color styles per finding category
  const cardBorderClass = isResolved
    ? 'bg-emerald-500/5 border-emerald-500/30 dark:bg-emerald-500/10 dark:border-emerald-500/40'
    : isLocation
    ? 'bg-rose-500/5 border-rose-500/30 dark:bg-rose-500/10 dark:border-rose-500/40 shadow-md'
    : isKnowledge || isObject
    ? 'bg-amber-500/5 border-amber-500/30 dark:bg-amber-500/10 dark:border-amber-500/40 shadow-md'
    : 'bg-secondary/10 border-secondary/40 shadow-md';

  const badgeClass = isResolved
    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700 dark:bg-emerald-500/25 dark:border-emerald-500/50 dark:text-emerald-400 font-bold'
    : isLocation
    ? 'bg-rose-500/15 border-rose-500/40 text-rose-700 dark:bg-rose-500/25 dark:border-rose-500/50 dark:text-rose-400 font-bold'
    : isKnowledge || isObject
    ? 'bg-amber-500/15 border-amber-500/40 text-amber-700 dark:bg-amber-500/25 dark:border-amber-500/50 dark:text-amber-400 font-bold'
    : 'bg-secondary/25 border-secondary/50 text-secondary dark:text-secondary font-bold';

  const suggestionBoxClass = isLocation
    ? 'bg-rose-500/10 border-rose-500/30 dark:bg-rose-500/15 dark:border-rose-500/40'
    : isKnowledge || isObject
    ? 'bg-amber-500/10 border-amber-500/30 dark:bg-amber-500/15 dark:border-amber-500/40'
    : 'bg-secondary/15 border-secondary/30';

  const suggestionTitleClass = isLocation
    ? 'text-rose-700 dark:text-rose-400'
    : isKnowledge || isObject
    ? 'text-amber-700 dark:text-amber-400'
    : 'text-secondary';

  const gapTagClass = isLocation
    ? 'bg-rose-600 text-white'
    : isKnowledge || isObject
    ? 'bg-amber-600 text-white'
    : 'bg-secondary text-white';

  return (
    <div className={`p-4 rounded-xl border transition-all space-y-3 ${cardBorderClass}`}>
      {/* Category Badge & Confidence */}
      <div className="flex items-center justify-between">
        <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] uppercase border flex items-center space-x-1 ${badgeClass}`}>
          {isResolved ? (
            <CheckCircle2 className="w-3 h-3 text-secondary mr-1" />
          ) : (
            <AlertTriangle className="w-3 h-3 mr-1" />
          )}
          <span>
            {isKnowledge
              ? 'Knowledge Gap'
              : isLocation
              ? 'Location Conflict'
              : isObject
              ? 'Object Transfer'
              : isProcedure
              ? '@ 1985 Procedure'
              : issue.issue_type.replace(/_/g, ' ')}
          </span>
        </span>

        <span className="text-[10px] font-mono text-txtMuted font-semibold">
          {confidencePct}% conf.
        </span>
      </div>

      {/* Title & Description */}
      <div>
        <h4 className="text-sm font-bold text-txtPrimary leading-snug">
          {issue.title}
        </h4>
        <p className="text-xs text-txtSecondary mt-1 leading-relaxed">
          {issue.description}
        </p>
      </div>

      {/* Evidence Trail Sub-section */}
      {issue.evidence && issue.evidence.length > 0 ? (
        <div className="p-2.5 rounded-lg bg-card/90 border border-border space-y-1.5 text-xs font-mono shadow-inner">
          <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider block">
            EVIDENCE TRAIL:
          </span>

          <div className="space-y-1.5">
            {issue.evidence.map((ev, idx) => {
              const isGap = idx === issue.evidence.length - 1 && !isResolved;
              return (
                <div key={idx} className={`flex items-center justify-between text-[11px] ${isGap ? 'font-bold' : 'text-txtSecondary'}`}>
                  <span className="truncate max-w-[190px] text-txtPrimary">
                    Sc. {ev.scene_number ? String(ev.scene_number).padStart(2, '0') : '??'}: {ev.text}
                  </span>
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    {ev.scene_number && onSelectSceneNumber && (
                      <button
                        onClick={() => onSelectSceneNumber(ev.scene_number!)}
                        className="text-secondary hover:underline font-semibold flex items-center space-x-0.5 text-[10px]"
                      >
                        <span>View</span>
                        <Eye className="w-3 h-3 ml-0.5" />
                      </button>
                    )}
                    {isGap && (
                      <span className={`px-1.5 py-0.2 rounded text-[9px] uppercase font-mono font-bold shadow-sm ${gapTagClass}`}>
                        GAP
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="p-2 rounded-lg bg-card/90 border border-border text-[11px] font-mono text-txtSecondary flex items-center justify-between">
          <span>Sc. {issue.scene_number ? String(issue.scene_number).padStart(2, '0') : '??'}: {issue.title}</span>
          {issue.scene_number && onSelectSceneNumber && (
            <button onClick={() => onSelectSceneNumber(issue.scene_number!)} className="text-secondary hover:underline font-semibold flex items-center space-x-0.5 text-[10px]">
              <span>View</span>
              <Eye className="w-3 h-3 ml-0.5" />
            </button>
          )}
        </div>
      )}

      {/* AI Suggestion Sub-section */}
      <div className={`p-2.5 rounded-lg border text-txtPrimary text-xs leading-relaxed font-medium ${suggestionBoxClass}`}>
        <strong className={`font-bold block mb-0.5 text-[10px] uppercase ${suggestionTitleClass}`}>
          SUGGESTION:
        </strong>
        {getSuggestionText(issue)}
      </div>

      {/* Resolve Finding Actions */}
      {!isResolved ? (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider block">
            Resolve Finding:
          </span>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => handleAction('ACCEPT', 'INTENTIONAL')}
              disabled={submitting}
              className="py-1.5 px-2 rounded-lg bg-cardHover border border-secondary/40 text-secondary hover:bg-secondary/20 font-bold text-xs transition-all disabled:opacity-50"
              title="Mark as an intentional writer story decision"
            >
              Intentional
            </button>
            <button
              onClick={() => handleAction('IGNORE', 'NEEDS_REVIEW')}
              disabled={submitting}
              className="py-1.5 px-2 rounded-lg bg-cardHover border border-tertiary/40 text-tertiary hover:bg-tertiary/20 font-bold text-xs transition-all disabled:opacity-50"
              title="Snooze issue to review later"
            >
              Fix Later
            </button>
            <button
              onClick={() => handleAction('RESOLVE', 'FIXED')}
              disabled={submitting}
              className="py-1.5 px-2 rounded-lg bg-primary hover:opacity-90 text-white font-bold text-xs transition-all shadow-md disabled:opacity-50"
              title="Mark issue as fixed"
            >
              Resolve
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Marked {issue.status} ({issue.resolution_type || 'Reviewed'})</span>
          </div>
          <button
            onClick={() => handleAction('REOPEN')}
            disabled={submitting}
            className="text-[10px] font-bold text-txtMuted hover:text-txtPrimary underline font-mono"
          >
            Reopen
          </button>
        </div>
      )}

      {/* Status tracking footer */}
      <div className="text-[10px] text-txtMuted font-mono flex items-center justify-between pt-1">
        <span>{isResolved ? `Reviewed • Status ${issue.status}` : 'Unsaved change • Auto-tracking'}</span>
      </div>
    </div>
  );
}
