'use client';

import React from 'react';
import { SceneAnalysis } from '@/lib/api';
import { Sparkles, Users, MapPin, Package, Building, CheckCircle2, ArrowRight } from 'lucide-react';

interface Props {
  analysis: SceneAnalysis | null;
  sceneNumber?: number;
}

export default function SceneAnalysisView({ analysis, sceneNumber }: Props) {
  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-500 border border-dashed border-border rounded-2xl">
        <Sparkles className="w-10 h-10 text-gray-600 mb-3" />
        <h3 className="text-sm font-semibold text-gray-400">No Scene Analysis Loaded</h3>
        <p className="text-xs text-gray-600 max-w-xs mt-1">
          Enter screenplay text on the left and click "Analyze Scene" to view Gemini's structured semantic output.
        </p>
      </div>
    );
  }

  const characters = analysis.entities.filter((e) => e.type.toLowerCase() === 'character');
  const locations = analysis.entities.filter((e) => e.type.toLowerCase() === 'location');
  const objects = analysis.entities.filter((e) => e.type.toLowerCase() === 'object');
  const orgs = analysis.entities.filter((e) => e.type.toLowerCase() === 'organization');

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
      {/* Scene Summary */}
      <div className="p-4 rounded-xl bg-accent/10 border border-accent/20">
        <div className="flex items-center space-x-2 text-xs font-semibold text-accent-light uppercase tracking-wider mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Scene Summary {sceneNumber ? `(Scene ${sceneNumber})` : ''}</span>
        </div>
        <p className="text-sm text-gray-200 leading-relaxed font-medium">
          {analysis.scene_summary}
        </p>
      </div>

      {/* Extracted Entities */}
      <div className="p-4 rounded-xl bg-card border border-border space-y-3">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Extracted Entities ({analysis.entities.length})
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Characters */}
          {characters.length > 0 && (
            <div className="p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-accent-light mb-2">
                <Users className="w-3.5 h-3.5" />
                <span>Characters</span>
              </div>
              <ul className="space-y-1">
                {characters.map((c, i) => (
                  <li key={i} className="text-xs text-gray-200 font-medium flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-light" />
                    <span>{c.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Locations */}
          {locations.length > 0 && (
            <div className="p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-accent-amber mb-2">
                <MapPin className="w-3.5 h-3.5" />
                <span>Locations</span>
              </div>
              <ul className="space-y-1">
                {locations.map((l, i) => (
                  <li key={i} className="text-xs text-gray-200 font-medium flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-amber" />
                    <span>{l.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Objects */}
          {objects.length > 0 && (
            <div className="p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-accent-emerald mb-2">
                <Package className="w-3.5 h-3.5" />
                <span>Objects</span>
              </div>
              <ul className="space-y-1">
                {objects.map((o, i) => (
                  <li key={i} className="text-xs text-gray-200 font-medium flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-emerald" />
                    <span>{o.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Organizations */}
          {orgs.length > 0 && (
            <div className="p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-purple-400 mb-2">
                <Building className="w-3.5 h-3.5" />
                <span>Organizations</span>
              </div>
              <ul className="space-y-1">
                {orgs.map((og, i) => (
                  <li key={i} className="text-xs text-gray-200 font-medium flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    <span>{og.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Facts */}
      {analysis.facts.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Established Facts ({analysis.facts.length})
          </h4>
          <div className="space-y-2">
            {analysis.facts.map((f, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-background border border-border text-xs flex items-center justify-between">
                <span className="font-semibold text-accent-light">{f.subject}</span>
                <span className="text-gray-400 font-mono text-[11px] px-2 py-0.5 bg-card rounded">{f.predicate}</span>
                <span className="font-medium text-gray-200">{f.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events */}
      {analysis.events.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Scene Events ({analysis.events.length})
          </h4>
          <div className="space-y-2">
            {analysis.events.map((ev, i) => (
              <div key={i} className="p-3 rounded-lg bg-background border border-border space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-accent/20 text-accent-light">
                    {ev.event_type}
                  </span>
                  {ev.location && (
                    <span className="text-[11px] text-accent-amber font-medium flex items-center">
                      <MapPin className="w-3 h-3 mr-1" />
                      {ev.location}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-200 font-medium">{ev.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
