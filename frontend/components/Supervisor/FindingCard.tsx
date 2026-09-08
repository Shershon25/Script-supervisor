'use client';

import React, { useState } from 'react';
import { IssueResponse } from '@/lib/api';
import { AlertTriangle, ShieldCheck, Eye, CheckCircle2, ExternalLink } from 'lucide-react';

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
  if (issue.issue_type.includes('TIMELINE')) {
    return `Align timestamps across scenes or mark as an intentional temporal anomaly / Story World Rule.`;
  }
  if (issue.issue_type.includes('WORLD_RULE')) {
    return `Review fictional physics claim. If intentional, mark as 'Intentional' so the AI adds it as a World Rule and respects it in downstream scenes.`;
  }
  if (issue.issue_type.includes('REASONING') || issue.issue_type.includes('OBJECT_STATE')) {
    return `Review narrative continuity for ${issue.title.toLowerCase()}. If intentional, mark as a story decision so the AI does not re-flag it.`;
  }
  return `Review narrative continuity for ${issue.title.toLowerCase()} or mark as intentional writer choice.`;
}

export default function FindingCard({ issue, onSelectSceneNumber, onReview }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [pendingAction, setPendingAction] = useState<{ action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN'; resType?: string } | null>(null);

  const isKnowledge = issue.issue_type.includes('KNOWLEDGE');
  const isLocation = issue.issue_type.includes('LOCATION');
  const isTimeline = issue.issue_type.includes('TIMELINE');
  const isWorldRule = issue.issue_type.includes('WORLD_RULE');
  const isObject = issue.issue_type.includes('OBJECT') || issue.issue_type.includes('OWNERSHIP');
  const isReasoning = issue.issue_type.includes('REASONING') || issue.issue_type === 'OBJECT_STATE_CONFLICT';
  const isProcedure = issue.issue_type.includes('REALITY') || issue.title.includes('Procedure') || issue.issue_type.includes('RESEARCH');
  const isResolved = issue.status === 'RESOLVED' || issue.status === 'ACCEPTED' || issue.status === 'IGNORED';

  const confidencePct = Math.round(issue.confidence * 100);

  const handleActionClick = (action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN', resType?: string) => {
    if (action === 'REOPEN') {
      confirmAction(action, resType, '');
      return;
    }
    setPendingAction({ action, resType });
    setShowNoteInput(true);
  };

  const confirmAction = async (
    action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN',
    resType?: string,
    customNote?: string
  ) => {
    setSubmitting(true);
    try {
      const finalNote = customNote !== undefined ? customNote.trim() : noteText.trim();
      const defaultFallback = resType === 'INTENTIONAL' 
        ? 'Intentional story decision' 
        : resType === 'NEEDS_REVIEW' 
        ? 'Deferred for later review' 
        : 'Resolved continuity issue';
      await onReview(action, resType, finalNote || defaultFallback);
      setShowNoteInput(false);
      setNoteText('');
      setPendingAction(null);
    } finally {
      setSubmitting(false);
    }
  };

  const isEvent = issue.issue_type.includes('EVENT');

  // Theme-aware color styles per finding category
  const cardBorderClass = isResolved
    ? 'bg-emerald-500/5 border-emerald-500/30 dark:bg-emerald-500/10 dark:border-emerald-500/40'
    : isTimeline || isLocation
    ? 'bg-rose-500/5 border-rose-500/30 dark:bg-rose-500/10 dark:border-rose-500/40 shadow-md'
    : isWorldRule
    ? 'bg-teal-500/5 border-teal-500/30 dark:bg-teal-500/10 dark:border-teal-500/40 shadow-md'
    : isKnowledge
    ? 'bg-blue-500/5 border-blue-500/30 dark:bg-blue-500/10 dark:border-blue-500/40 shadow-md'
    : isEvent || isObject
    ? 'bg-amber-500/5 border-amber-500/30 dark:bg-amber-500/10 dark:border-amber-500/40 shadow-md'
    : isReasoning
    ? 'bg-purple-500/5 border-purple-500/30 dark:bg-purple-500/10 dark:border-purple-500/40 shadow-md'
    : 'bg-secondary/10 border-secondary/40 shadow-md';

  const badgeClass = isResolved
    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700 dark:bg-emerald-500/25 dark:border-emerald-500/50 dark:text-emerald-400 font-bold'
    : isTimeline || isLocation
    ? 'bg-rose-500/15 border-rose-500/40 text-rose-700 dark:bg-rose-500/25 dark:border-rose-500/50 dark:text-rose-400 font-bold'
    : isWorldRule
    ? 'bg-teal-500/15 border-teal-500/40 text-teal-700 dark:bg-teal-500/25 dark:border-teal-500/50 dark:text-teal-400 font-bold'
    : isKnowledge
    ? 'bg-blue-500/15 border-blue-500/40 text-blue-700 dark:bg-blue-500/25 dark:border-blue-500/50 dark:text-blue-400 font-bold'
    : isEvent || isObject
    ? 'bg-amber-500/15 border-amber-500/40 text-amber-700 dark:bg-amber-500/25 dark:border-amber-500/50 dark:text-amber-400 font-bold'
    : isReasoning
    ? 'bg-purple-500/15 border-purple-500/40 text-purple-700 dark:bg-purple-500/25 dark:border-purple-500/50 dark:text-purple-400 font-bold'
    : 'bg-secondary/25 border-secondary/50 text-secondary dark:text-secondary font-bold';

  const suggestionBoxClass = isTimeline || isLocation
    ? 'bg-rose-500/10 border-rose-500/30 dark:bg-rose-500/15 dark:border-rose-500/40'
    : isWorldRule
    ? 'bg-teal-500/10 border-teal-500/30 dark:bg-teal-500/15 dark:border-teal-500/40'
    : isKnowledge
    ? 'bg-blue-500/10 border-blue-500/30 dark:bg-blue-500/15 dark:border-blue-500/40'
    : isEvent || isObject
    ? 'bg-amber-500/10 border-amber-500/30 dark:bg-amber-500/15 dark:border-amber-500/40'
    : isReasoning
    ? 'bg-purple-500/10 border-purple-500/30 dark:bg-purple-500/15 dark:border-purple-500/40'
    : 'bg-secondary/15 border-secondary/30';

  const suggestionTitleClass = isLocation
    ? 'text-rose-700 dark:text-rose-400'
    : isKnowledge || isObject
    ? 'text-amber-700 dark:text-amber-400'
    : isReasoning
    ? 'text-purple-700 dark:text-purple-400'
    : 'text-secondary';

  const gapTagClass = isLocation
    ? 'bg-rose-600 text-white'
    : isKnowledge || isObject
    ? 'bg-amber-600 text-white'
    : isReasoning
    ? 'bg-purple-600 text-white'
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
              : isTimeline
              ? 'Timeline Inconsistency'
              : isWorldRule
              ? 'Potential World Rule'
              : isObject
              ? 'Object Transfer'
              : isReasoning
              ? 'Object Continuity'
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
              const hasUrl = ev.text && (ev.text.includes('http://') || ev.text.includes('https://'));
              const urlMatch = hasUrl ? ev.text.match(/https?:\/\/[^\s]+/) : null;
              const linkUrl = urlMatch ? urlMatch[0] : null;

              return (
                <div key={idx} className={`flex items-center justify-between text-[11px] ${isGap ? 'font-bold' : 'text-txtSecondary'}`}>
                  {linkUrl ? (
                    <a
                      href={linkUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="truncate max-w-[200px] text-blue-400 hover:underline font-semibold flex items-center space-x-1"
                    >
                      <span className="truncate">{ev.text}</span>
                      <ExternalLink className="w-3 h-3 text-blue-400 flex-shrink-0" />
                    </a>
                  ) : (
                    <span className="truncate max-w-[190px] text-txtPrimary">
                      Sc. {ev.scene_number ? String(ev.scene_number).padStart(2, '0') : '??'}: {ev.text}
                    </span>
                  )}
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

      {/* Persistent Saved Writer Note Display */}
      {isResolved && issue.resolution_note && (
        <div className="p-2.5 rounded-lg bg-card/90 border border-emerald-500/30 text-xs font-mono shadow-sm space-y-0.5">
          <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block">
            ✍️ WRITER NOTE:
          </span>
          <p className="text-txtPrimary italic font-medium">"{issue.resolution_note}"</p>
        </div>
      )}

      {/* Resolve Finding Actions */}
      {!isResolved ? (
        <div className="space-y-2 pt-1">
          <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider block">
            Resolve Finding:
          </span>

          {!showNoteInput ? (
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => handleActionClick('ACCEPT', 'INTENTIONAL')}
                disabled={submitting}
                className="py-1.5 px-2 rounded-lg bg-cardHover border border-secondary/40 text-secondary hover:bg-secondary/20 font-bold text-xs transition-all disabled:opacity-50"
                title="Mark as an intentional writer story decision"
              >
                Intentional
              </button>
              <button
                onClick={() => handleActionClick('IGNORE', 'NEEDS_REVIEW')}
                disabled={submitting}
                className="py-1.5 px-2 rounded-lg bg-cardHover border border-tertiary/40 text-tertiary hover:bg-tertiary/20 font-bold text-xs transition-all disabled:opacity-50"
                title="Snooze issue to review later"
              >
                Fix Later
              </button>
              <button
                onClick={() => handleActionClick('RESOLVE', 'FIXED')}
                disabled={submitting}
                className="py-1.5 px-2 rounded-lg bg-primary hover:opacity-90 text-white font-bold text-xs transition-all shadow-md disabled:opacity-50"
                title="Mark issue as fixed"
              >
                Resolve
              </button>
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-card border border-secondary/40 space-y-2.5 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-secondary uppercase font-mono">
                  Add Note ({pendingAction?.resType || pendingAction?.action}):
                </span>
                <button
                  onClick={() => { setShowNoteInput(false); setPendingAction(null); }}
                  className="text-[10px] text-txtMuted hover:text-txtPrimary font-bold"
                >
                  Cancel
                </button>
              </div>

              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Optional writer note (e.g., Mom knows Maddie's habit from off-screen family backstory)..."
                rows={2}
                className="w-full p-2 rounded bg-cardHover border border-border text-txtPrimary text-xs focus:outline-none focus:border-secondary resize-none font-sans"
              />

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => pendingAction && confirmAction(pendingAction.action, pendingAction.resType)}
                  disabled={submitting}
                  className="py-1 px-3 rounded-lg bg-secondary text-white font-bold text-xs hover:opacity-90 transition-all disabled:opacity-50 shadow-sm"
                >
                  {submitting ? 'Saving...' : 'Save & Confirm'}
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Marked {issue.status} ({issue.resolution_type || 'Reviewed'})</span>
          </div>
          <button
            onClick={() => handleActionClick('REOPEN')}
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
