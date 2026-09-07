'use client';

import React, { useState, useEffect } from 'react';
import { ClaimResponse, ResearchTaskResponse, listClaims, listResearchTasks, triggerResearch, getResearchTask } from '@/lib/api';
import { Globe, Search, ExternalLink, CheckCircle2, AlertTriangle, XCircle, HelpCircle, Shield, RefreshCw, FileText, ChevronDown, ChevronRight } from 'lucide-react';

interface Props {
  projectId: string;
  onSelectSceneNumber?: (sceneNum: number) => void;
}

function cleanResearchText(text?: string): string {
  if (!text) return '';
  return text
    .replace(/Source\s+[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\s*/gi, '')
    .replace(/Source\s+ID\s*:\s*[a-f0-9-]{36}\s*/gi, '')
    .replace(/#{1,6}\s+/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();
}

export default function ResearchPanel({ projectId, onSelectSceneNumber }: Props) {

  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterCategory, setFilterCategory] = useState<'ALL' | 'REAL_WORLD' | 'RESEARCH_NEEDED' | 'FICTIONAL'>('ALL');
  const [researchingClaimId, setResearchingClaimId] = useState<string | null>(null);
  const [expandedTask, setExpandedTask] = useState<Record<string, ResearchTaskResponse | null>>({});
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const toggleExpanded = (claimId: string) => {
    setExpandedSources(prev => ({ ...prev, [claimId]: !prev[claimId] }));
  };


  useEffect(() => {
    fetchClaims();
  }, [projectId]);

  const fetchClaims = async () => {
    setLoading(true);
    try {
      const [claimsData, tasksData] = await Promise.all([
        listClaims(projectId),
        listResearchTasks(projectId)
      ]);
      setClaims(claimsData);

      const taskMap: Record<string, ResearchTaskResponse> = {};
      tasksData.forEach((task) => {
        if (task.claim_id) {
          taskMap[task.claim_id] = task;
        }
      });
      setExpandedTask(taskMap);
    } catch (e) {
      console.error("Error fetching claims and research tasks", e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunResearch = async (claimId: string, force: boolean = false) => {
    setResearchingClaimId(claimId);
    try {
      const res = await triggerResearch(projectId, claimId, force);
      if (res.task_id) {
        const taskData = await getResearchTask(projectId, res.task_id);
        setExpandedTask(prev => ({ ...prev, [claimId]: taskData }));
      }
      await fetchClaims();
    } catch (e: any) {
      alert(e.message || 'Parallel research failed');
    } finally {
      setResearchingClaimId(null);
    }
  };

  const filteredClaims = claims.filter((c) => {
    if (filterCategory === 'REAL_WORLD') return c.claim_type === 'REAL_WORLD_CLAIM';
    if (filterCategory === 'RESEARCH_NEEDED') return c.requires_research;
    if (filterCategory === 'FICTIONAL') return c.claim_type === 'FICTIONAL_WORLD_RULE';
    return true;
  });

  const researchNeededCount = claims.filter((c) => c.requires_research).length;
  const verifiedCount = claims.filter((c) => c.status === 'VERIFIED' || c.status === 'LIKELY_TRUE').length;
  const contradictedCount = claims.filter((c) => c.status === 'CONTRADICTED').length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-gray-400">
        <Globe className="w-6 h-6 animate-spin text-blue-400 mb-2" />
        <span className="text-xs font-medium">Analyzing Screenplay Claims & Web Evidence...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
      {/* Top Header */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-blue-900/40 via-purple-900/30 to-card border border-blue-500/30 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Globe className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            External Reality & Parallel Search Engine
          </span>
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-semibold">
          <span className="px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/30 text-blue-300">
            {claims.length} Claims
          </span>
          {verifiedCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
              {verifiedCount} Verified
            </span>
          )}
          {contradictedCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/30 text-rose-300">
              {contradictedCount} Contradicted
            </span>
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex items-center space-x-1 bg-card/60 p-1 rounded-xl border border-border text-xs font-medium">
        <button
          onClick={() => setFilterCategory('ALL')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterCategory === 'ALL' ? 'bg-accent text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          All ({claims.length})
        </button>
        <button
          onClick={() => setFilterCategory('RESEARCH_NEEDED')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterCategory === 'RESEARCH_NEEDED' ? 'bg-blue-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Research Needed ({researchNeededCount})
        </button>
        <button
          onClick={() => setFilterCategory('REAL_WORLD')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterCategory === 'REAL_WORLD' ? 'bg-purple-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Real World
        </button>
        <button
          onClick={() => setFilterCategory('FICTIONAL')}
          className={`flex-1 py-1 px-2 rounded-lg transition-colors ${filterCategory === 'FICTIONAL' ? 'bg-amber-600 text-white font-bold shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Fictional Rules
        </button>
      </div>

      {/* Empty State */}
      {filteredClaims.length === 0 && (
        <div className="p-8 rounded-2xl bg-card border border-border text-center space-y-2">
          <Globe className="w-8 h-8 text-blue-400 mx-auto" />
          <h4 className="text-sm font-bold text-white">No Claims Found</h4>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            Analyze screenplay scenes to extract claims and verify external reality assertions.
          </p>
        </div>
      )}

      {/* Claims List */}
      <div className="space-y-3">
        {filteredClaims.map((claim) => {
          const isVerified = claim.status === 'VERIFIED' || claim.status === 'LIKELY_TRUE';
          const isContradicted = claim.status === 'CONTRADICTED';
          const isInconclusive = claim.status === 'INCONCLUSIVE';
          const taskData = expandedTask[claim.id];
          const evaluation = taskData?.evaluation || claim.evaluation;
          const sources = (taskData?.sources && taskData.sources.length > 0) ? taskData.sources : (claim.sources || []);

          const primarySource = sources[0];
          const additionalSources = sources.slice(1);
          const isExpanded = !!expandedSources[claim.id];

          return (
            <div
              key={claim.id}
              className={`p-4 rounded-xl border transition-all ${
                isVerified
                  ? 'bg-emerald-500/5 border-emerald-500/30'
                  : isContradicted
                  ? 'bg-rose-500/5 border-rose-500/30'
                  : isInconclusive
                  ? 'bg-amber-500/5 border-amber-500/30'
                  : 'bg-card border-border'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                        claim.claim_type === 'REAL_WORLD_CLAIM'
                          ? 'bg-purple-500/20 border-purple-500/30 text-purple-300'
                          : claim.claim_type === 'FICTIONAL_WORLD_RULE'
                          ? 'bg-amber-500/20 border-amber-500/30 text-amber-300'
                          : 'bg-blue-500/20 border-blue-500/30 text-blue-300'
                      }`}
                    >
                      {claim.claim_type.replace(/_/g, ' ')}
                    </span>

                    {claim.scene_number && onSelectSceneNumber && (
                      <button
                        onClick={() => onSelectSceneNumber(claim.scene_number!)}
                        className="px-1.5 py-0.5 rounded bg-accent/20 text-accent-light hover:bg-accent/30 font-bold text-[10px]"
                      >
                        Scene {claim.scene_number}
                      </button>
                    )}
                  </div>

                  <h4 className="text-sm font-bold text-white pt-1 leading-tight">
                    "{claim.claim_text}"
                  </h4>
                </div>

                {/* Status Verdict Badge */}
                <div className="flex items-center space-x-1.5 flex-shrink-0">
                  <span
                    className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded-lg border flex items-center space-x-1 ${
                      isVerified
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : isContradicted
                        ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                        : isInconclusive
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                        : 'bg-card border-border text-gray-400'
                    }`}
                  >
                    {isVerified && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                    {isContradicted && <XCircle className="w-3 h-3 text-rose-400" />}
                    {isInconclusive && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                    {!isVerified && !isContradicted && !isInconclusive && <HelpCircle className="w-3 h-3 text-gray-400" />}
                    <span>{claim.status}</span>
                  </span>
                </div>
              </div>

              {/* Context Metadata */}
              {(claim.temporal_context || claim.location_context) && (
                <div className="flex items-center space-x-3 text-[11px] text-gray-400 mb-3 font-mono">
                  {claim.temporal_context && <span>Year/Time: <strong className="text-gray-200">{claim.temporal_context}</strong></span>}
                  {claim.location_context && <span>Location: <strong className="text-gray-200">{claim.location_context}</strong></span>}
                </div>
              )}

              {/* Action Toolbar */}
              <div className="flex items-center justify-between pt-2 border-t border-border/50 text-xs">
                <div className="flex items-center space-x-2">
                  {claim.requires_research && (
                    <button
                      onClick={() => handleRunResearch(claim.id, true)}
                      disabled={researchingClaimId === claim.id}
                      className="px-2.5 py-1 rounded-lg bg-blue-600/20 border border-blue-500/30 hover:bg-blue-600/30 text-blue-300 font-semibold text-[10px] flex items-center space-x-1 transition-colors disabled:opacity-50"
                    >
                      <Search className={`w-3 h-3 ${researchingClaimId === claim.id ? 'animate-spin' : ''}`} />
                      <span>{researchingClaimId === claim.id ? 'Researching...' : 'Re-run Web Search'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Evidence & Sources Details */}
              {(evaluation || sources.length > 0) && (
                <div className="mt-3 p-3 rounded-xl bg-background border border-border space-y-3">
                  <div className="flex items-center justify-between text-xs border-b border-border/60 pb-2">
                    <span className="font-bold text-accent-light uppercase text-[10px] tracking-wider">
                      Parallel Research Evidence & Evaluation:
                    </span>
                    {evaluation && (
                      <span className="text-gray-400 font-mono text-[10px]">
                        {Math.round(evaluation.confidence * 100)}% Confidence
                      </span>
                    )}
                  </div>

                  {evaluation && (
                    <p className="text-xs text-gray-200 leading-relaxed font-medium">
                      {cleanResearchText(evaluation.summary || evaluation.reasoning)}
                    </p>
                  )}

                  {/* Primary Source Link & Collapsible Additional Sources */}
                  {primarySource && (
                    <div className="space-y-1.5 pt-2 border-t border-border/40">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                        Primary Source:
                      </span>
                      <a
                        href={primarySource.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-bold text-blue-400 hover:text-blue-300 hover:underline flex items-center space-x-1.5 text-[11px] truncate bg-card/60 p-1.5 rounded-lg border border-border/50"
                      >
                        <span className="truncate">{cleanResearchText(primarySource.title) || primarySource.domain || 'Primary Source Link'}</span>
                        <ExternalLink className="w-3 h-3 text-blue-400 flex-shrink-0" />
                        <span className="text-[9px] font-mono text-gray-400 px-1.5 py-0.5 rounded bg-background flex-shrink-0 border border-border/40 ml-auto">
                          {primarySource.domain}
                        </span>
                      </a>

                      {additionalSources.length > 0 && (
                        <div className="pt-1">
                          <button
                            onClick={() => toggleExpanded(claim.id)}
                            className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition-colors py-0.5"
                          >
                            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            <span>
                              {isExpanded ? 'Hide' : 'Show'} {additionalSources.length} additional {additionalSources.length === 1 ? 'source' : 'sources'}
                            </span>
                          </button>

                          {isExpanded && (
                            <div className="mt-1.5 space-y-1.5 pl-1.5 border-l-2 border-blue-500/30">
                              {additionalSources.map((src) => (
                                <a
                                  key={src.id || src.url}
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="font-semibold text-blue-400 hover:text-blue-300 hover:underline flex items-center space-x-1.5 text-[10px] truncate bg-card/40 p-1 rounded-md border border-border/40"
                                >
                                  <span className="truncate">{cleanResearchText(src.title) || src.domain || 'Source Link'}</span>
                                  <ExternalLink className="w-2.5 h-2.5 text-blue-400 flex-shrink-0" />
                                  <span className="text-[9px] font-mono text-gray-400 px-1 py-0.2 rounded bg-background flex-shrink-0 border border-border/30 ml-auto">
                                    {src.domain}
                                  </span>
                                </a>
                              ))}
                            </div>
                          )}
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
    </div>
  );
}
