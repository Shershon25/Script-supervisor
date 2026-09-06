'use client';

import React, { useState, useEffect } from 'react';
import { ClaimResponse, ResearchTaskResponse, listClaims, listResearchTasks } from '@/lib/api';
import { Globe, ExternalLink, ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface Props {
  projectId: string;
  onSelectSceneNumber?: (sceneNum: number) => void;
}

export default function ResearchView({ projectId, onSelectSceneNumber }: Props) {
  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [tasksMap, setTasksMap] = useState<Record<string, ResearchTaskResponse>>({});
  const [loading, setLoading] = useState(true);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [claimsData, tasksData] = await Promise.all([
        listClaims(projectId),
        listResearchTasks(projectId).catch(() => [])
      ]);
      
      const realWorldClaims = claimsData.filter(c => c.claim_type === 'REAL_WORLD_CLAIM' && c.requires_research);
      setClaims(realWorldClaims);

      const map: Record<string, ResearchTaskResponse> = {};
      tasksData.forEach(t => {
        if (t.claim_id) {
          map[t.claim_id] = t;
        }
      });
      setTasksMap(map);
    } catch (e) {
      console.error("Error fetching research claims", e);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (claimId: string) => {
    setExpandedSources(prev => ({ ...prev, [claimId]: !prev[claimId] }));
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-txtSecondary font-mono text-xs">
        <Globe className="w-5 h-5 mx-auto animate-spin text-blue-500 mb-1" />
        <span>Loading Parallel Research Evidence...</span>
      </div>
    );
  }

  if (claims.length === 0) {
    return (
      <div className="p-6 text-center text-txtSecondary space-y-2">
        <Globe className="w-6 h-6 mx-auto text-blue-400 mb-1" />
        <h4 className="text-xs font-bold text-txtPrimary">No External Research Needed</h4>
        <p className="text-[11px] text-txtMuted leading-relaxed">
          This scene contains internal story facts. No real-world procedural, historical, or geographic claims require external web verification.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto min-h-0 space-y-3 text-xs pr-1">
      {claims.map((claim) => {
        const task = tasksMap[claim.id];
        const evaluation = task?.evaluation;
        const sources = task?.sources || [];
        const primarySource = sources[0];
        const additionalSources = sources.slice(1);
        const isExpanded = !!expandedSources[claim.id];

        return (
          <div key={claim.id} className="p-3 rounded-xl bg-card border border-border space-y-2.5 shadow-sm">
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-0.5">
                <span className="px-2 py-0.5 rounded bg-secondary/15 border border-secondary/30 text-secondary font-mono text-[10px] uppercase font-bold inline-block">
                  @ Real-World Claim
                </span>
                {claim.scene_number && onSelectSceneNumber && (
                  <button
                    onClick={() => onSelectSceneNumber(claim.scene_number!)}
                    className="ml-2 px-1.5 py-0.5 rounded bg-secondary/15 text-secondary hover:bg-secondary/25 font-bold text-[10px]"
                  >
                    Scene {claim.scene_number}
                  </button>
                )}
              </div>

              <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-lg border flex items-center space-x-1 font-mono ${
                claim.status === 'VERIFIED' || claim.status === 'LIKELY_TRUE'
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-700 dark:bg-emerald-500/25 dark:border-emerald-500/50 dark:text-emerald-400 font-bold'
                  : claim.status === 'CONTRADICTED'
                  ? 'bg-rose-500/15 border-rose-500/40 text-rose-700 dark:bg-rose-500/25 dark:border-rose-500/50 dark:text-rose-400 font-bold'
                  : 'bg-amber-500/15 border-amber-500/40 text-amber-700 dark:bg-amber-500/25 dark:border-amber-500/50 dark:text-amber-400 font-bold'
              }`}>
                {claim.status === 'VERIFIED' || claim.status === 'LIKELY_TRUE' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 mr-0.5" />
                ) : claim.status === 'CONTRADICTED' ? (
                  <XCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 mr-0.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 mr-0.5" />
                )}
                <span>{claim.status}</span>
              </span>
            </div>

            {/* Claim Text */}
            <h5 className="font-bold text-txtPrimary text-xs leading-tight">
              "{claim.claim_text}"
            </h5>

            {/* Evidence & Reasoning Section */}
            {evaluation && (
              <div className="p-2.5 rounded-lg bg-background/60 border border-border/80 space-y-2 text-[11px]">
                <div className="flex items-center justify-between text-[10px] font-mono border-b border-border/40 pb-1">
                  <span className="font-bold text-secondary flex items-center space-x-1">
                    <Globe className="w-3 h-3 text-secondary" />
                    <span>Parallel Research Evidence</span>
                  </span>
                  <span className="text-txtMuted font-mono">
                    {Math.round((evaluation.confidence || 0.9) * 100)}% Confidence
                  </span>
                </div>

                <p className="text-txtSecondary leading-relaxed text-[11px]">
                  {evaluation.reasoning || evaluation.summary}
                </p>

                {/* Primary Source Evidence Card */}
                {primarySource && (
                  <div className="space-y-1 pt-1">
                    <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider block">
                      Primary Web Source:
                    </span>
                    <div className="p-2 rounded bg-card/80 border border-border/60 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <a
                          href={primarySource.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-bold text-accent-light hover:underline flex items-center space-x-1 text-[11px] truncate"
                        >
                          <span className="truncate">{primarySource.title}</span>
                          <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0" />
                        </a>
                        <span className="text-[9px] font-mono text-txtMuted px-1.5 py-0.5 rounded bg-background flex-shrink-0">
                          {primarySource.domain}
                        </span>
                      </div>
                      {primarySource.excerpt && (
                        <p className="text-[10px] text-txtSecondary font-mono italic leading-normal bg-background/50 p-1.5 rounded border border-border/30">
                          "{primarySource.excerpt}"
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Collapsible Additional Sources List */}
                {additionalSources.length > 0 && (
                  <div className="pt-1">
                    <button
                      onClick={() => toggleExpanded(claim.id)}
                      className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition-colors py-0.5"
                    >
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      <span>
                        {isExpanded ? 'Hide' : 'Show'} {additionalSources.length} additional web {additionalSources.length === 1 ? 'source' : 'sources'}
                      </span>
                    </button>

                    {isExpanded && (
                      <div className="mt-1.5 space-y-1.5 pl-1.5 border-l-2 border-blue-500/30">
                        {additionalSources.map((src) => (
                          <div key={src.id} className="text-[10px] space-y-0.5">
                            <div className="flex items-center space-x-1.5">
                              <span className="text-blue-400 font-bold">•</span>
                              <a
                                href={src.url}
                                target="_blank"
                                rel="noreferrer"
                                className="font-semibold text-accent-light hover:underline flex items-center space-x-1 truncate"
                              >
                                <span className="truncate">{src.title}</span>
                                <ExternalLink className="w-2.5 h-2.5 text-gray-400 flex-shrink-0" />
                              </a>
                              <span className="text-[9px] font-mono text-txtMuted px-1 rounded bg-background flex-shrink-0">
                                {src.domain}
                              </span>
                            </div>
                            {src.excerpt && (
                              <p className="text-[9px] text-txtMuted font-mono italic pl-3 leading-tight">
                                "{src.excerpt}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
