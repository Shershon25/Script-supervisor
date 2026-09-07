'use client';

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { 
  X, Film, Sparkles, BookOpen, Globe, ShieldCheck, 
  RefreshCw, Download, Search, CheckCircle2 
} from 'lucide-react';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
  theme?: 'dark' | 'light';
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose, theme = 'dark' }) => {
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !mounted) return null;

  const modalContent = (
    <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/65 backdrop-blur-sm animate-fade-in theme-${theme}`}>
      <div 
        className="bg-card border border-border rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl space-y-5 text-txtPrimary relative custom-scrollbar"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400 shrink-0">
              <Film className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight text-txtPrimary">Script Supervisor</h2>
                <span className="px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 rounded-full">
                  v2.0
                </span>
              </div>
              <p className="text-xs text-txtSecondary mt-0.5">Automated Story Memory & Continuity Suite</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-txtMuted hover:text-txtPrimary bg-panel hover:bg-cardHover border border-border rounded-lg transition"
            title="Close (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 30-Second Elevator Pitch Banner */}
        <div className="p-4 bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-400">
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>How it works in 30 seconds</span>
          </div>
          <p className="text-xs text-txtPrimary leading-relaxed">
            Script Supervisor reads your screenplay, builds a persistent model of your story, and checks new scenes against what has already happened. It also distinguishes fictional story rules from real-world claims and uses external research when appropriate.
          </p>
        </div>

        {/* 3-Step Visual Core Pipeline */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-txtSecondary flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-secondary" />
            <span>Core Workflow & Pipeline</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Step 1 */}
            <div className="p-3.5 bg-panel border border-border rounded-xl space-y-2">
              <div className="w-6 h-6 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 font-extrabold text-xs flex items-center justify-center border border-blue-500/20">
                1
              </div>
              <h4 className="text-xs font-bold text-txtPrimary">Scene Classification</h4>
              <p className="text-[11px] text-txtSecondary leading-snug">
                Parses raw screenplay text into standard industry elements: headings, action lines, character cues, dialogue, and parentheticals.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-3.5 bg-panel border border-border rounded-xl space-y-2">
              <div className="w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-extrabold text-xs flex items-center justify-center border border-indigo-500/20">
                2
              </div>
              <h4 className="text-xs font-bold text-txtPrimary">Story Memory Model</h4>
              <p className="text-[11px] text-txtSecondary leading-snug">
                Tracks character presence, physical movements, item ownership, knowledge gaps, and plot timelines across all scenes.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-3.5 bg-panel border border-border rounded-xl space-y-2">
              <div className="w-6 h-6 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 font-extrabold text-xs flex items-center justify-center border border-purple-500/20">
                3
              </div>
              <h4 className="text-xs font-bold text-txtPrimary">Reality & Rules Engine</h4>
              <p className="text-[11px] text-txtSecondary leading-snug">
                Separates fictional universe rules (magic/tech) from real-world claims, launching live research only when needed.
              </p>
            </div>
          </div>
        </div>

        {/* Core Features Grid */}
        <div className="space-y-3 pt-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-txtSecondary flex items-center gap-2">
            <Globe className="w-4 h-4 text-emerald-500" />
            <span>Key Features & Capabilities</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 bg-panel/60 border border-border rounded-xl flex items-start gap-2.5">
              <RefreshCw className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold text-txtPrimary">Background Scene Evaluation</div>
                <div className="text-[11px] text-txtSecondary mt-0.5 leading-snug">
                  Evaluates previous scenes asynchronously in the background so you can keep writing without waiting.
                </div>
              </div>
            </div>

            <div className="p-3 bg-panel/60 border border-border rounded-xl flex items-start gap-2.5">
              <Download className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold text-txtPrimary">Professional Export Engine</div>
                <div className="text-[11px] text-txtSecondary mt-0.5 leading-snug">
                  Export formatted screenplays directly to PDF, Microsoft Word (.docx), and Fountain text formats.
                </div>
              </div>
            </div>

            <div className="p-3 bg-panel/60 border border-border rounded-xl flex items-start gap-2.5">
              <Search className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold text-txtPrimary">Fact Extraction & Research</div>
                <div className="text-[11px] text-txtSecondary mt-0.5 leading-snug">
                  Verifies real-world travel times, geographic locations, and historical dates against live web sources.
                </div>
              </div>
            </div>

            <div className="p-3 bg-panel/60 border border-border rounded-xl flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-purple-500 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold text-txtPrimary">Writer Decision Authority</div>
                <div className="text-[11px] text-txtSecondary mt-0.5 leading-snug">
                  Respects writer choices — accepted, ignored, or resolved issues remain preserved across re-evaluations.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-border text-xs text-txtMuted">
          <div className="flex items-center gap-1.5 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Ready for spec scripts and feature screenplays</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs transition shadow-sm"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
