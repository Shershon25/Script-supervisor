'use client';

import React, { useState } from 'react';
import { IssueResponse } from '@/lib/api';
import IssueReviewModal from './IssueReviewModal';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, Tag, ShieldAlert, Check, EyeOff, RotateCcw, History, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  projectId: string;
  issues: IssueResponse[];
  loading: boolean;
  onSelectSceneNumber?: (sceneNum: number) => void;
  onIssueReviewed?: (updatedIssue: IssueResponse) => void;
}

export default function IssuePanel({ projectId, issues, loading, onSelectSceneNumber, onIssueReviewed }: Props) {
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'OPEN' | 'ACCEPTED' | 'RESOLVED' | 'IGNORED'>('OPEN');
  const [selectedIssueForReview, setSelectedIssueForReview] = useState<{ issue: IssueResponse; action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN' } | null>(null);
  const [expandedHistory, setExpandedHistory] = useState<Record<string, boolean>>({});

  const toggleHistory = (issueId: string) => {
    setExpandedHistory(prev => ({ ...prev, [issueId]: !prev[issueId] }));
  };

  const filteredIssues = issues.filter((i) => {
    if (filterStatus === 'ALL') return true;
    return i.status.toUpperCase() === filterStatus;
  });

  const openCount = issues.filter((i) => i.status.toUpperCase() === 'OPEN').length;
  const acceptedCount = issues.filter((i) => i.status.toUpperCase() === 'ACCEPTED').length;
  const resolvedCount = issues.filter((i) => i.status.toUpperCase() === 'RESOLVED').length;
  const ignoredCount = issues.filter((i) => i.status.toUpperCase() === 'IGNORED').length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-gray-400">
        <ShieldAlert className="w-6 h-6 animate-spin text-amber-400 mb-2" />
        <span className="text-xs font-medium">Evaluating Continuity Candidates...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
      {/* Review Modal */}
      {selectedIssueForReview && (
        <IssueReviewModal
          projectId={projectId}
          issue={selectedIssueForReview.issue}
          initialAction={selectedIssueForReview.action}
          onClose={() => setSelectedIssueForReview(null)}
          onReviewed={(updated) => {
            if (onIssueReviewed) onIssueReviewed(updated);
          }}
        />
      )}

      {/* Header Bar */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-amber-500/20 via-rose-900/30 to-card border border-amber-500/30 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Human-in-the-Loop Continuity Review
          </span>
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-semibold">
          <span className="px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-amber-300">
            {openCount} Open
          </span>
          {acceptedCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-purple-500/20 border border-purple-500/30 text-purple-300">
              {acceptedCount} Accepted
            </span>
          )}
          {resolvedCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
              {resolvedCount} Resolved
            </span>
          )}
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center space-x-1 bg-card/60 p-1 rounded-xl border border-border text-xs font-medium">
        <button
          onClick={() => setFilterStatus('OPEN')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterStatus === 'OPEN' ? 'bg-amber-500 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Open ({openCount})
        </button>
        <button
          onClick={() => setFilterStatus('ACCEPTED')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterStatus === 'ACCEPTED' ? 'bg-purple-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Accepted ({acceptedCount})
        </button>
        <button
          onClick={() => setFilterStatus('RESOLVED')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterStatus === 'RESOLVED' ? 'bg-emerald-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Resolved ({resolvedCount})
        </button>
        <button
          onClick={() => setFilterStatus('IGNORED')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterStatus === 'IGNORED' ? 'bg-gray-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Ignored ({ignoredCount})
        </button>
        <button
          onClick={() => setFilterStatus('ALL')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterStatus === 'ALL' ? 'bg-accent text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          All ({issues.length})
        </button>
      </div>

      {/* Empty State */}
      {filteredIssues.length === 0 && (
        <div className="p-8 rounded-2xl bg-card border border-border text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <h4 className="text-sm font-bold text-white">No {filterStatus === 'ALL' ? '' : filterStatus} Issues</h4>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            {filterStatus === 'OPEN'
              ? 'All detected continuity issues have been reviewed by the writer!'
              : 'No issues match the selected status filter.'}
          </p>
        </div>
      )}

      {/* Issue Cards */}
      <div className="space-y-3">
        {filteredIssues.map((issue) => {
          const isError = issue.severity.toUpperCase() === 'ERROR';
          const isWarning = issue.severity.toUpperCase() === 'WARNING';
          const confPercent = Math.round(issue.confidence * 100);

          const statusUpper = issue.status.toUpperCase();
          const isResolved = statusUpper === 'RESOLVED';
          const isAccepted = statusUpper === 'ACCEPTED';
          const isIgnored = statusUpper === 'IGNORED';

          return (
            <div
              key={issue.id}
              className={`p-4 rounded-xl border transition-all ${
                isResolved
                  ? 'bg-emerald-500/5 border-emerald-500/30'
                  : isAccepted
                  ? 'bg-purple-500/5 border-purple-500/30'
                  : isIgnored
                  ? 'bg-gray-500/5 border-gray-500/30 opacity-70'
                  : isError
                  ? 'bg-rose-500/5 border-rose-500/30'
                  : 'bg-amber-500/5 border-amber-500/30'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center space-x-2">
                  {isError ? (
                    <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  ) : isWarning ? (
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  ) : (
                    <Info className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  )}
                  <h4 className="text-sm font-bold text-white leading-tight">
                    {issue.title}
                  </h4>
                </div>

                <div className="flex items-center space-x-1.5 flex-shrink-0">
                  {/* Status Badge */}
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                      isResolved
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : isAccepted
                        ? 'bg-purple-500/20 border-purple-500/40 text-purple-300'
                        : isIgnored
                        ? 'bg-gray-500/20 border-gray-500/40 text-gray-300'
                        : isError
                        ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                        : 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                    }`}
                  >
                    {issue.status}
                  </span>

                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-card border border-border text-gray-300">
                    {confPercent}% Confidence
                  </span>
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-gray-300 mb-3 leading-relaxed">
                {issue.description}
              </p>

              {/* Grounded Evidence Box */}
              {issue.evidence && issue.evidence.length > 0 && (
                <div className="p-3 rounded-lg bg-background border border-border/80 space-y-2 mb-3">
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center space-x-1">
                    <Tag className="w-3 h-3 text-accent-light" />
                    <span>Grounded Screenplay Evidence:</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {issue.evidence.map((ev, idx) => (
                      <div key={idx} className="p-2 rounded bg-card/70 border border-border/60 space-y-1">
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-accent-light uppercase">
                            {ev.type.replace(/_/g, ' ')}
                          </span>
                          {ev.scene_number && onSelectSceneNumber && (
                            <button
                              onClick={() => onSelectSceneNumber(ev.scene_number!)}
                              className="px-1.5 py-0.5 rounded bg-accent/20 text-accent-light hover:bg-accent/30 font-bold"
                            >
                              Scene {ev.scene_number}
                            </button>
                          )}
                        </div>
                        <p className="text-[11px] text-gray-200 font-mono italic">
                          "{ev.text}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Writer Resolution Note (If resolved/ignored) */}
              {issue.resolution_note && (
                <div className="p-2.5 rounded-lg bg-accent/10 border border-accent/20 text-xs mb-3 space-y-1">
                  <div className="text-[10px] font-bold text-accent-light uppercase">
                    Writer Resolution ({issue.resolution_type || 'Note'}):
                  </div>
                  <p className="text-gray-200 italic">"{issue.resolution_note}"</p>
                </div>
              )}

              {/* Human-in-the-Loop Action Buttons */}
              <div className="pt-2 border-t border-border/60 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1.5">
                  {!isResolved && !isIgnored && (
                    <>
                      <button
                        onClick={() => setSelectedIssueForReview({ issue, action: 'ACCEPT' })}
                        className="px-2.5 py-1 rounded-lg bg-purple-600/20 border border-purple-500/30 hover:bg-purple-600/30 text-purple-300 font-semibold text-[11px] flex items-center space-x-1 transition-colors"
                      >
                        <Check className="w-3 h-3" />
                        <span>Accept</span>
                      </button>

                      <button
                        onClick={() => setSelectedIssueForReview({ issue, action: 'RESOLVE' })}
                        className="px-2.5 py-1 rounded-lg bg-emerald-600/20 border border-emerald-500/30 hover:bg-emerald-600/30 text-emerald-300 font-semibold text-[11px] flex items-center space-x-1 transition-colors"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Resolve</span>
                      </button>

                      <button
                        onClick={() => setSelectedIssueForReview({ issue, action: 'IGNORE' })}
                        className="px-2.5 py-1 rounded-lg bg-cardHover border border-border hover:bg-border text-gray-300 font-medium text-[11px] flex items-center space-x-1 transition-colors"
                      >
                        <EyeOff className="w-3 h-3 text-gray-400" />
                        <span>Ignore</span>
                      </button>
                    </>
                  )}

                  {(isResolved || isIgnored) && (
                    <button
                      onClick={() => setSelectedIssueForReview({ issue, action: 'REOPEN' })}
                      className="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 hover:bg-amber-500/30 text-amber-300 font-semibold text-[11px] flex items-center space-x-1 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Reopen</span>
                    </button>
                  )}
                </div>

                {/* Audit History Toggle */}
                {issue.reviews && issue.reviews.length > 0 && (
                  <button
                    onClick={() => toggleHistory(issue.id)}
                    className="text-[11px] text-gray-400 hover:text-white flex items-center space-x-1 font-medium hover:underline"
                  >
                    <History className="w-3 h-3" />
                    <span>Audit History ({issue.reviews.length})</span>
                    {expandedHistory[issue.id] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                )}
              </div>

              {/* Audit History List */}
              {expandedHistory[issue.id] && issue.reviews && issue.reviews.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border/40 space-y-1.5 text-[11px]">
                  <span className="font-bold text-gray-400 uppercase tracking-wider block text-[10px]">
                    Review Audit Trail:
                  </span>
                  {issue.reviews.map((rev) => (
                    <div key={rev.id} className="p-2 rounded bg-card/60 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-white">{rev.action}</span>
                        <span className="text-gray-400 mx-1.5">({rev.previous_status} → {rev.new_status})</span>
                        {rev.note && <span className="text-gray-300 font-mono italic">"{rev.note}"</span>}
                      </div>
                      <span className="text-[10px] text-gray-500 font-mono">
                        {new Date(rev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
