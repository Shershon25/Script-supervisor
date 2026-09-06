'use client';

import React, { useState } from 'react';
import { ReasoningResult, RetrievalResponse, retrieveContext, runReasoning } from '@/lib/api';
import { Brain, Layers, Search, CheckCircle2, AlertTriangle, XCircle, FileText, Compass, Sparkles } from 'lucide-react';

interface Props {
  projectId: string;
  scenes: { id: string; scene_number: number; raw_text: string }[];
}

export default function ReasoningView({ projectId, scenes }: Props) {
  const [selectedSceneId, setSelectedSceneId] = useState<string>(scenes.length > 0 ? scenes[0].id : '');
  const [taskType, setTaskType] = useState<string>('CONTINUITY');
  const [entityFilter, setEntityFilter] = useState<string>('');
  
  const [retrievedData, setRetrievedData] = useState<RetrievalResponse | null>(null);
  const [reasoningData, setReasoningData] = useState<ReasoningResult | null>(null);
  
  const [loadingContext, setLoadingContext] = useState<boolean>(false);
  const [loadingReasoning, setLoadingReasoning] = useState<boolean>(false);

  const handleRetrieveContext = async () => {
    if (!selectedSceneId) return;
    setLoadingContext(true);
    try {
      const entities = entityFilter ? entityFilter.split(',').map((e) => e.trim()) : [];
      const res = await retrieveContext(projectId, selectedSceneId, taskType, entities);
      setRetrievedData(res);
    } catch (e: any) {
      alert(e.message || 'Failed to retrieve context');
    }
  };

  const handleRunReasoning = async () => {
    if (!selectedSceneId) return;
    setLoadingReasoning(true);
    try {
      const entities = entityFilter ? entityFilter.split(',').map((e) => e.trim()) : [];
      const res = await runReasoning(projectId, selectedSceneId, taskType, entities);
      setReasoningData(res);
    } catch (e: any) {
      alert(e.message || 'Failed to run AI story reasoning');
    } finally {
      setLoadingReasoning(false);
    }
  };

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1 text-xs">

      {/* Control Bar */}
      <div className="p-4 rounded-xl bg-card border border-border space-y-3.5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] font-bold text-txtSecondary uppercase tracking-wider block mb-1">
              Select Scene:
            </label>
            <select
              value={selectedSceneId}
              onChange={(e) => setSelectedSceneId(e.target.value)}
              className="w-full bg-cardHover border border-border rounded-lg px-2.5 py-1.5 text-txtPrimary focus:outline-none focus:border-secondary text-xs font-medium"
            >
              {scenes.map((s) => (
                <option key={s.id} value={s.id} className="bg-card text-txtPrimary">
                  Scene #{s.scene_number} ({s.raw_text.substring(0, 30)}...)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] font-bold text-txtSecondary uppercase tracking-wider block mb-1">
              Task Focus:
            </label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full bg-cardHover border border-border rounded-lg px-2.5 py-1.5 text-txtPrimary focus:outline-none focus:border-secondary text-xs font-medium"
            >
              <option value="CONTINUITY" className="bg-card text-txtPrimary">CONTINUITY (State & Facts)</option>
              <option value="KNOWLEDGE" className="bg-card text-txtPrimary">CHARACTER KNOWLEDGE</option>
              <option value="OBJECT" className="bg-card text-txtPrimary">OBJECT OWNERSHIP</option>
              <option value="LOCATION" className="bg-card text-txtPrimary">LOCATION REASONING</option>
              <option value="REALITY" className="bg-card text-txtPrimary">REALITY CHECK</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] font-bold text-txtSecondary uppercase tracking-wider block mb-1">
              Target Entities (optional):
            </label>
            <input
              type="text"
              placeholder="e.g. John, Camera"
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="w-full bg-cardHover border border-border rounded-lg px-2.5 py-1.5 text-txtPrimary placeholder-txtMuted focus:outline-none focus:border-secondary text-xs font-medium"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2 pt-1">
          <button
            onClick={handleRetrieveContext}
            disabled={loadingContext || !selectedSceneId}
            className="flex-1 py-2 px-3 rounded-lg bg-cardHover hover:bg-panel border border-border text-txtPrimary font-semibold flex items-center justify-center space-x-1.5 transition-colors disabled:opacity-50"
          >
            <Layers className={`w-3.5 h-3.5 text-secondary ${loadingContext ? 'animate-spin' : ''}`} />
            <span>Inspect Hybrid Context</span>
          </button>

          <button
            onClick={handleRunReasoning}
            disabled={loadingReasoning || !selectedSceneId}
            className="flex-1 py-2 px-3 rounded-lg bg-primary hover:bg-secondary text-white font-semibold flex items-center justify-center space-x-1.5 shadow-sm transition-all disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${loadingReasoning ? 'animate-spin' : ''}`} />
            <span>Run Targeted Reasoning</span>
          </button>
        </div>
      </div>

      {/* Reasoning Results */}
      {reasoningData && (() => {
        let title = reasoningData.conclusion;
        let description = reasoningData.summary;
        let reasoningSummary = reasoningData.reasoning_summary;
        let verdict = reasoningData.verdict;
        let confidence = reasoningData.confidence;
        let evidenceList: { provenance: string; source_text: string }[] = [];
        let writerDecision = reasoningData.writer_decision_context;

        // Try parsing JSON if raw markdown/JSON was returned
        const rawText = reasoningData.reasoning_summary || reasoningData.conclusion || '';
        if (rawText.includes('findings') || rawText.includes('```')) {
          try {
            let cleaned = rawText.trim();
            if (cleaned.startsWith('```')) {
              const lines = cleaned.split('\n');
              const firstLineIndex = lines[0].startsWith('```') ? 1 : 0;
              const lastLineIndex = lines[lines.length - 1].startsWith('```') ? lines.length - 1 : lines.length;
              cleaned = lines.slice(firstLineIndex, lastLineIndex).join('\n').trim();
            }
            const parsed = JSON.parse(cleaned);
            if (parsed.findings && parsed.findings.length > 0) {
              const f = parsed.findings[0];
              title = f.title || title;
              description = f.description || description;
              reasoningSummary = f.reasoning_summary || f.description || reasoningSummary;
              verdict = f.classification || verdict;
              confidence = f.confidence || confidence;
              evidenceList = f.evidence || [];
              if (f.writer_decision_applied && f.writer_decision) {
                writerDecision = `Authoritative Writer Decision Applied: "${f.writer_decision}"`;
              }
            }
          } catch (e) {
            // Keep fallback
          }
        }

        // Clean leftover markdown codeblock prefix
        title = title.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').trim();

        return (
          <div className="p-4 rounded-xl bg-card border border-border space-y-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="font-bold text-txtPrimary uppercase text-[10px] tracking-wider flex items-center space-x-1.5">
                <Brain className="w-3.5 h-3.5 text-tertiary" />
                <span>Targeted AI Story Reasoning Finding:</span>
              </span>
              <span
                className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-lg border font-mono ${
                  verdict === 'CONFLICT'
                    ? 'bg-rose-500/15 border-rose-500/40 text-rose-700 dark:bg-rose-500/25 dark:border-rose-500/50 dark:text-rose-400 font-bold'
                    : verdict === 'AMBIGUOUS'
                    ? 'bg-amber-500/15 border-amber-500/40 text-amber-700 dark:bg-amber-500/25 dark:border-amber-500/50 dark:text-amber-400 font-bold'
                    : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700 dark:bg-emerald-500/25 dark:border-emerald-500/50 dark:text-emerald-400 font-bold'
                }`}
              >
                {verdict} ({Math.round(confidence * 100)}% Confidence)
              </span>
            </div>

            {/* Title Header */}
            <h4 className="text-sm font-bold text-txtPrimary leading-tight">
              {title}
            </h4>

            {/* Human Readable Reasoning Explanation */}
            <div className="p-3 rounded-lg bg-cardHover border border-border space-y-2">
              <p className="text-xs text-txtPrimary leading-relaxed font-medium">
                {description}
              </p>
              {reasoningSummary && reasoningSummary !== description && (
                <p className="text-[11px] text-txtSecondary leading-relaxed italic border-t border-border/50 pt-2">
                  {reasoningSummary}
                </p>
              )}
            </div>

            {/* Cited Provenance Evidence List */}
            {evidenceList.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider block">
                  Cited Provenance Evidence ({evidenceList.length}):
                </span>
                <div className="space-y-1.5">
                  {evidenceList.map((ev, idx) => (
                    <div key={idx} className="p-2 rounded bg-background border border-border/60 text-[11px] font-mono space-y-0.5">
                      <span className="font-bold text-accent-light block text-[10px]">
                        {ev.provenance}
                      </span>
                      <p className="text-txtSecondary italic font-sans leading-relaxed">
                        "{ev.source_text}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Writer Decision Context */}
            {writerDecision && (
              <div className="p-2.5 rounded-lg bg-tertiary/10 border border-tertiary/30 text-txtPrimary text-[11px] font-medium">
                <strong className="block text-[10px] uppercase font-bold text-tertiary mb-0.5">
                  Authoritative Writer Decision Context:
                </strong>
                {writerDecision}
              </div>
            )}
          </div>
        );
      })()}

      {/* Retrieved Context Items Details */}
      {retrievedData && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <span className="font-bold text-txtSecondary uppercase text-[10px] tracking-wider flex items-center space-x-1">
              <Compass className="w-3.5 h-3.5 text-secondary" />
              <span>Retrieved Hybrid Context ({retrievedData.total_retrieved} Items):</span>
            </span>
          </div>

          <div className="space-y-2">
            {retrievedData.items.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-cardHover border border-border space-y-1 font-mono text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-accent-light">{item.provenance_tag}</span>
                  <span className="text-[10px] text-txtMuted px-1.5 py-0.5 rounded bg-card border border-border">
                    Score: {item.relevance_score.toFixed(2)} ({item.retrieval_reason})
                  </span>
                </div>
                <p className="text-txtPrimary font-sans leading-relaxed">
                  {item.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
