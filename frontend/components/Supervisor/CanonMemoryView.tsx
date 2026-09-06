'use client';

import React, { useState } from 'react';
import { StoryStateResponse } from '@/lib/api';
import { Layers, User, Box, MapPin, BookOpen, Share2, Tag } from 'lucide-react';

interface Props {
  storyState: StoryStateResponse | null;
  onSelectSceneNumber?: (sceneNum: number) => void;
}

export default function CanonMemoryView({ storyState, onSelectSceneNumber }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<'CHARACTERS' | 'LOCATIONS' | 'OBJECTS' | 'RELATIONSHIPS' | 'KNOWLEDGE' | 'WORLD_RULES'>('CHARACTERS');

  if (!storyState) {
    return (
      <div className="p-6 text-center text-txtSecondary space-y-2">
        <Layers className="w-6 h-6 mx-auto text-accent-light mb-1" />
        <p className="text-xs font-medium">No story memory compiled yet.</p>
        <p className="text-[11px] text-txtMuted">Analyze scenes to populate Canon Memory.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full space-y-3 text-xs min-h-0 overflow-hidden">
      {/* Category Pills */}
      <div className="flex items-center space-x-1 overflow-x-auto pb-1 font-mono text-[10px] font-bold shrink-0">
        <button
          onClick={() => setSelectedCategory('CHARACTERS')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'CHARACTERS'
              ? 'bg-accent/20 border-accent/40 text-txtPrimary'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          Characters ({storyState.characters.length})
        </button>

        <button
          onClick={() => setSelectedCategory('OBJECTS')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'OBJECTS'
              ? 'bg-accent/20 border-accent/40 text-txtPrimary'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          Objects ({storyState.objects.length})
        </button>

        <button
          onClick={() => setSelectedCategory('LOCATIONS')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'LOCATIONS'
              ? 'bg-accent/20 border-accent/40 text-txtPrimary'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          Locations ({storyState.locations.length})
        </button>

        <button
          onClick={() => setSelectedCategory('KNOWLEDGE')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'KNOWLEDGE'
              ? 'bg-accent/20 border-accent/40 text-txtPrimary'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          Knowledge ({storyState.knowledge_states.length})
        </button>

        <button
          onClick={() => setSelectedCategory('RELATIONSHIPS')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'RELATIONSHIPS'
              ? 'bg-accent/20 border-accent/40 text-txtPrimary'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          Relationships ({storyState.relationships.length})
        </button>

        <button
          onClick={() => setSelectedCategory('WORLD_RULES')}
          className={`px-2.5 py-1 rounded-lg border transition-colors whitespace-nowrap ${
            selectedCategory === 'WORLD_RULES'
              ? 'bg-tertiary/20 border-tertiary/40 text-tertiary font-bold'
              : 'bg-card border text-txtSecondary hover:text-txtPrimary'
          }`}
        >
          World Rules
        </button>
      </div>

      {/* Characters List */}
      {selectedCategory === 'CHARACTERS' && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
          {storyState.characters.map((c) => (
            <div key={c.id} className="p-3 rounded-xl bg-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-txtPrimary text-sm flex items-center space-x-1.5">
                  <User className="w-3.5 h-3.5 text-accent-light" />
                  <span>{c.name}</span>
                </h4>
                {c.residence && (
                  <span className="text-[10px] font-mono text-txtMuted">Residence: {c.residence}</span>
                )}
              </div>

              {c.current_location && (
                <div className="text-[11px] text-txtSecondary flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-secondary shrink-0" />
                  <span>Current Location: <strong className="text-txtPrimary">{c.current_location.name}</strong></span>
                </div>
              )}

              {c.possessions.length > 0 && (
                <div className="text-[11px] text-txtMuted">
                  Possessions: {c.possessions.map((p) => p.name).join(', ')}
                </div>
              )}

              {c.knowledge.length > 0 && (() => {
                const uniqueMap = new Map();
                c.knowledge.forEach((k) => {
                  const normKey = k.knowledge.trim().replace(/^["']|["']$/g, '').replace(/[.,!?]+$/, '').trim().toLowerCase();
                  if (!uniqueMap.has(normKey)) {
                    uniqueMap.set(normKey, k.knowledge.replace(/^["']|["']$/g, '').replace(/[.,!?]+$/, '').trim());
                  }
                });
                const uniqueKnowledgeTexts = Array.from(uniqueMap.values());
                return (
                  <div className="space-y-1 pt-1 border-t border-border/50 text-[11px]">
                    <span className="text-[10px] font-bold uppercase text-txtMuted block">Established Knowledge:</span>
                    {uniqueKnowledgeTexts.map((text, idx) => (
                      <div key={idx} className="text-txtSecondary flex items-start space-x-1">
                        <span className="text-accent-light">•</span>
                        <span>{text}</span>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          ))}
        </div>
      )}

      {/* Objects List */}
      {selectedCategory === 'OBJECTS' && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
          {storyState.objects.length === 0 ? (
            <div className="p-6 text-center text-txtMuted italic bg-card rounded-xl border border-border">
              No objects recorded in story memory yet.
            </div>
          ) : (
            storyState.objects.map((o) => (
              <div key={o.id} className="p-3 rounded-xl bg-card border border-border space-y-1.5">
                <h4 className="font-bold text-txtPrimary text-sm flex items-center space-x-1.5">
                  <Box className="w-3.5 h-3.5 text-amber-500" />
                  <span>{o.name}</span>
                </h4>
                {o.current_owner && (
                  <div className="text-[11px] text-txtSecondary">
                    Current Owner: <strong className="text-amber-600">{o.current_owner.name}</strong>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Locations List */}
      {selectedCategory === 'LOCATIONS' && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
          {storyState.locations.length === 0 ? (
            <div className="p-6 text-center text-txtMuted italic bg-card rounded-xl border border-border">
              No locations recorded in story memory yet.
            </div>
          ) : (
            storyState.locations.map((loc) => {
              const presentChars = storyState.characters.filter(
                (c) => c.current_location?.id === loc.id || c.current_location?.name === loc.name
              );

              return (
                <div key={loc.id} className="p-3 rounded-xl bg-card border border-border space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-txtPrimary text-sm flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-secondary" />
                      <span>{loc.name}</span>
                    </h4>
                    {loc.type && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary/15 border border-secondary/30 text-secondary">
                        {loc.type}
                      </span>
                    )}
                  </div>

                  {presentChars.length > 0 ? (
                    <div className="text-[11px] text-txtSecondary flex items-center gap-1">
                      <span className="text-txtMuted font-medium">Currently Present:</span>
                      <span className="font-semibold text-txtPrimary">
                        {presentChars.map((c) => c.name).join(', ')}
                      </span>
                    </div>
                  ) : (
                    <div className="text-[11px] text-txtMuted italic">
                      No characters currently stationed at this location.
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Knowledge States List */}
      {selectedCategory === 'KNOWLEDGE' && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
          {storyState.knowledge_states.length === 0 ? (
            <div className="p-6 text-center text-txtMuted italic bg-card rounded-xl border border-border">
              No character knowledge states recorded yet.
            </div>
          ) : (
            storyState.knowledge_states.map((k) => (
              <div key={k.id} className="p-3 rounded-xl bg-card border border-border space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-txtPrimary flex items-center space-x-1">
                    <BookOpen className="w-3.5 h-3.5 text-accent-light" />
                    <span>{k.character?.name || 'Character'}</span>
                  </span>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-accent/15 border border-accent/30 text-accent-light font-bold">
                    {k.knowledge_type || 'FACT'}
                  </span>
                </div>

                <p className="text-[11px] text-txtSecondary leading-relaxed pl-3 border-l-2 border-accent/40 font-mono">
                  "{k.knowledge.replace(/^["']|["']$/g, '').replace(/[.,!?]+$/, '').trim()}"
                </p>

                {k.source_scene_number && onSelectSceneNumber && (
                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => onSelectSceneNumber(k.source_scene_number!)}
                      className="text-[10px] font-bold text-accent-light hover:underline flex items-center gap-0.5"
                    >
                      <Tag className="w-3 h-3" />
                      <span>Jump to Scene {k.source_scene_number} &rarr;</span>
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Relationships List */}
      {selectedCategory === 'RELATIONSHIPS' && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-2 min-h-0">
          {storyState.relationships.length === 0 ? (
            <div className="p-6 text-center text-txtMuted italic bg-card rounded-xl border border-border">
              No character relationships recorded yet.
            </div>
          ) : (
            storyState.relationships.map((rel) => (
              <div key={rel.id} className="p-3 rounded-xl bg-card border border-border flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <Share2 className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  <span className="font-bold text-txtPrimary">{rel.source?.name || 'Unknown'}</span>
                  <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-700 dark:text-amber-300 font-semibold">
                    {rel.relationship_type.replace('_', ' ')}
                  </span>
                  <span className="font-bold text-txtPrimary">{rel.target?.name || 'Unknown'}</span>
                </div>
                {rel.source_scene_number && onSelectSceneNumber && (
                  <button
                    onClick={() => onSelectSceneNumber(rel.source_scene_number!)}
                    className="text-[10px] font-bold text-accent-light hover:underline font-mono"
                  >
                    Scene {rel.source_scene_number}
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* World Rules */}
      {selectedCategory === 'WORLD_RULES' && (
        <div className="p-4 rounded-xl bg-tertiary/10 border border-tertiary/30 space-y-2">
          <h4 className="font-bold text-tertiary text-xs uppercase tracking-wider">
            Established Fictional World Rules:
          </h4>
          <p className="text-xs text-txtPrimary leading-relaxed">
            Fictional rules established by the writer (e.g. teleportation, sci-fi devices) are protected from external real-world research challenges.
          </p>
        </div>
      )}
    </div>
  );
}

