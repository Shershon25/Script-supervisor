'use client';

import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';
import { Scene } from '@/lib/api';

interface Props {
  scene: Scene;
  totalScenes: number;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting?: boolean;
}

export default function DeleteSceneModal({
  scene,
  totalScenes,
  onConfirm,
  onCancel,
  isDeleting = false,
}: Props) {
  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}
    >
      {/* Modal Panel */}
      <div className="relative w-full max-w-md mx-4 rounded-2xl bg-card border border-border shadow-2xl overflow-hidden">

        {/* Amber accent top bar — matches Stale Text visual language */}
        <div className="h-1 w-full bg-gradient-to-r from-tertiary via-amber-400 to-tertiary" />

        {/* Header */}
        <div className="flex items-start justify-between p-5 pb-3">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-tertiary/15 border border-tertiary/30 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-5 h-5 text-tertiary" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-txtPrimary">Continuity Warning</h2>
              <p className="text-[11px] text-txtMuted font-mono mt-0.5">
                Scene {scene.scene_number} of {totalScenes}
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg hover:bg-cardHover text-txtMuted hover:text-txtPrimary transition-colors"
            title="Cancel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 pb-4 space-y-3">
          {/* Stale-text style pulsing badge */}
          <div className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-tertiary/10 border border-tertiary/25">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse flex-shrink-0" />
            <span className="text-[11px] font-mono font-bold text-tertiary">
              Mid-script deletion detected
            </span>
          </div>

          <p className="text-xs text-txtSecondary leading-relaxed">
            Deleting <span className="font-bold text-txtPrimary">Scene {scene.scene_number}</span> will
            permanently remove all continuity data extracted from it — facts, events, knowledge
            states, issues, and research tasks.
          </p>

          <p className="text-xs text-txtSecondary leading-relaxed">
            Since this is not the last scene, all remaining scenes will be{' '}
            <span className="font-semibold text-txtPrimary">renumbered sequentially</span> and{' '}
            <span className="font-semibold text-txtPrimary">re-analyzed from scratch</span> to
            restore continuity integrity.
          </p>

          {/* What will happen summary */}
          <div className="rounded-lg bg-cardHover border border-border p-3 space-y-1.5 text-[11px] font-mono text-txtSecondary">
            <div className="flex items-center space-x-2">
              <span className="text-tertiary font-bold">1.</span>
              <span>Delete Scene {scene.scene_number} + its extracted data</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-tertiary font-bold">2.</span>
              <span>Renumber remaining {totalScenes - 1} scenes (no gaps)</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-tertiary font-bold">3.</span>
              <span>Re-analyze all scenes to rebuild continuity</span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end space-x-2 px-5 py-4 border-t border-border bg-panel">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-txtSecondary hover:text-txtPrimary hover:bg-cardHover border border-border transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-tertiary hover:bg-amber-600 active:bg-amber-700 flex items-center space-x-1.5 transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Trash2 className={`w-3.5 h-3.5 ${isDeleting ? 'animate-pulse' : ''}`} />
            <span>{isDeleting ? 'Deleting...' : 'Delete & Re-analyze All'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
