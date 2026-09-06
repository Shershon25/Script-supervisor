'use client';

import React, { useState } from 'react';
import { IssueResponse, reviewIssue } from '@/lib/api';
import { X, Check, EyeOff, CheckCircle2, RotateCcw, AlertTriangle } from 'lucide-react';

interface Props {
  projectId: string;
  issue: IssueResponse;
  initialAction: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN';
  onClose: () => void;
  onReviewed: (updatedIssue: IssueResponse) => void;
}

export default function IssueReviewModal({ projectId, issue, initialAction, onClose, onReviewed }: Props) {
  const [action, setAction] = useState<'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN'>(initialAction);
  const [resolutionType, setResolutionType] = useState<string>(
    initialAction === 'RESOLVE' ? 'INTENTIONAL' : initialAction === 'IGNORE' ? 'FALSE_POSITIVE' : 'ACCEPTED_AS_IS'
  );
  const [note, setNote] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (action === 'RESOLVE' && !note.trim()) {
      setErrorMsg('Please enter an explanation note for resolving this issue.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await reviewIssue(projectId, issue.id, action, resolutionType, note.trim() || undefined);
      onReviewed(res.issue);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to record review decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-card border border-border rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center space-x-2">
            {action === 'ACCEPT' && <Check className="w-5 h-5 text-purple-400" />}
            {action === 'IGNORE' && <EyeOff className="w-5 h-5 text-gray-400" />}
            {action === 'RESOLVE' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
            {action === 'REOPEN' && <RotateCcw className="w-5 h-5 text-amber-400" />}
            <h3 className="text-base font-bold text-white">
              {action === 'ACCEPT' && 'Accept Issue as Valid'}
              {action === 'IGNORE' && 'Ignore Continuity Warning'}
              {action === 'RESOLVE' && 'Resolve Continuity Issue'}
              {action === 'REOPEN' && 'Reopen Continuity Issue'}
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-cardHover"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Issue Title & Summary */}
        <div className="p-3 rounded-xl bg-background border border-border space-y-1 text-xs">
          <div className="font-bold text-white flex items-center justify-between">
            <span>{issue.title}</span>
            <span className="font-mono text-accent-light px-2 py-0.5 rounded bg-accent/10">
              Scene {issue.scene_number}
            </span>
          </div>
          <p className="text-gray-400 text-[11px] leading-relaxed">{issue.description}</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Action Choice Tabs */}
          <div>
            <label className="text-[11px] font-semibold text-gray-300 uppercase tracking-wider block mb-1.5">
              Review Action:
            </label>
            <div className="grid grid-cols-4 gap-1 bg-background p-1 rounded-xl border border-border font-medium">
              <button
                type="button"
                onClick={() => setAction('ACCEPT')}
                className={`py-1.5 px-2 rounded-lg text-[11px] transition-colors ${action === 'ACCEPT' ? 'bg-purple-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Accept
              </button>
              <button
                type="button"
                onClick={() => setAction('IGNORE')}
                className={`py-1.5 px-2 rounded-lg text-[11px] transition-colors ${action === 'IGNORE' ? 'bg-gray-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Ignore
              </button>
              <button
                type="button"
                onClick={() => setAction('RESOLVE')}
                className={`py-1.5 px-2 rounded-lg text-[11px] transition-colors ${action === 'RESOLVE' ? 'bg-emerald-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Resolve
              </button>
              <button
                type="button"
                onClick={() => setAction('REOPEN')}
                className={`py-1.5 px-2 rounded-lg text-[11px] transition-colors ${action === 'REOPEN' ? 'bg-amber-600 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                Reopen
              </button>
            </div>
          </div>

          {/* Resolution Type Dropdown (If Resolve or Ignore) */}
          {(action === 'RESOLVE' || action === 'IGNORE') && (
            <div>
              <label className="text-[11px] font-semibold text-gray-300 uppercase tracking-wider block mb-1.5">
                Resolution Reason / Category:
              </label>
              <select
                value={resolutionType}
                onChange={(e) => setResolutionType(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-xl text-xs text-white focus:outline-none focus:border-accent"
              >
                <option value="INTENTIONAL">Intentional Story Choice (Flashback / Relocation / Secret)</option>
                <option value="FIXED">Fixed in Screenplay Text</option>
                <option value="FALSE_POSITIVE">False Positive / AI Misinterpretation</option>
                <option value="ACCEPTED_AS_IS">Accepted As-Is (Acknowledged Flaw)</option>
                <option value="NEEDS_REVIEW">Needs Further Review</option>
              </select>
            </div>
          )}

          {/* Explanation / Writer Note */}
          <div>
            <label className="text-[11px] font-semibold text-gray-300 uppercase tracking-wider block mb-1.5">
              Writer Explanation / Notes {action === 'RESOLVE' ? '(Required)' : '(Optional)'}:
            </label>
            <textarea
              rows={3}
              placeholder={
                action === 'RESOLVE'
                  ? 'Explain why this is intentional or how it was resolved...'
                  : 'Add optional notes for your records...'
              }
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full p-3 bg-background border border-border rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              required={action === 'RESOLVE'}
            />
          </div>

          {/* Submit / Cancel Buttons */}
          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-cardHover hover:bg-border text-xs text-gray-300 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-accent hover:bg-accent-hover text-xs text-white font-bold shadow-lg transition-all disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Save Decision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
