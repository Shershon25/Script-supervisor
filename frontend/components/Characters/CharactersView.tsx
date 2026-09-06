'use client';

import React, { useState } from 'react';
import { StoryStateResponse, CharacterState } from '@/lib/api';
import { 
  Users, MapPin, Package, BookOpen, Search, UserCheck, 
  HeartHandshake, ArrowUpRight, Bookmark, X, Home, ShieldCheck 
} from 'lucide-react';

interface Props {
  storyState: StoryStateResponse | null;
  onSelectSceneNumber?: (sceneNum: number) => void;
}

const MAJOR_RELATION_TYPES = [
  'brother_of', 'sister_of', 'parent_of', 'child_of', 'father_of', 'mother_of',
  'son_of', 'daughter_of', 'spouse_of', 'married_to', 'friend_of', 'enemy_of',
  'rival_of', 'works_for', 'boss_of', 'partner_of'
];

function invertRelation(relType: string): string {
  const norm = relType.toLowerCase().trim();
  if (norm === 'parent_of' || norm === 'father_of' || norm === 'mother_of') return 'child_of';
  if (norm === 'child_of' || norm === 'son_of' || norm === 'daughter_of') return 'parent_of';
  if (norm === 'works_for') return 'boss_of';
  if (norm === 'boss_of') return 'works_for';
  if (norm === 'brother_of') return 'brother_of';
  if (norm === 'sister_of') return 'sister_of';
  if (norm === 'sibling_of') return 'sibling_of';
  return norm;
}

function formatRelationLabel(relType: string): string {
  const norm = relType.toLowerCase().trim();
  if (norm === 'parent_of' || norm === 'father_of' || norm === 'mother_of') return 'Parent of';
  if (norm === 'child_of' || norm === 'son_of' || norm === 'daughter_of') return 'Child of';
  if (norm === 'brother_of') return 'Brother of';
  if (norm === 'sister_of') return 'Sister of';
  if (norm === 'sibling_of') return 'Sibling of';
  if (norm === 'spouse_of' || norm === 'married_to') return 'Spouse of';
  if (norm === 'works_for') return 'Works for';
  if (norm === 'boss_of') return 'Employer of';
  if (norm === 'friend_of') return 'Friend of';
  if (norm === 'enemy_of' || norm === 'rival_of') return 'Rival of';
  return relType.replace('_of', '').replace('_', ' ');
}

export default function CharactersView({ storyState, onSelectSceneNumber }: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<string>('ALL');
  const [selectedCharacter, setSelectedCharacter] = useState<CharacterState | null>(null);

  const characters = storyState?.characters || [];

  const availableLocations = React.useMemo(() => {
    const set = new Set<string>();
    characters.forEach(c => {
      if (c.current_location?.name) set.add(c.current_location.name);
    });
    return Array.from(set);
  }, [characters]);

  const filtered = characters.filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLocation = selectedLocation === 'ALL' || c.current_location?.name === selectedLocation;
    return matchesSearch && matchesLocation;
  });

  const getMajorRelationships = (char: CharacterState) => {
    if (!char.relationships) return [];
    
    // Group relationships per target character to prevent duplicate badges (e.g. Sibling vs Sister)
    const targetMap = new Map<string, { relationLabel: string; targetName: string; relType: string }>();

    for (const rel of char.relationships) {
      const rawType = rel.relationship_type?.toLowerCase().trim();
      if (!rawType || !MAJOR_RELATION_TYPES.includes(rawType)) continue;

      const isSource = rel.source?.id === char.id;
      const isTarget = rel.target?.id === char.id;
      if (!isSource && !isTarget) continue;

      const targetEntity = isSource ? rel.target : rel.source;
      if (!targetEntity || !targetEntity.name) continue;

      const effectiveType = isSource ? rawType : invertRelation(rawType);
      const label = formatRelationLabel(effectiveType);
      const targetName = targetEntity.name;
      const key = `${targetName.toLowerCase()}_${effectiveType.includes('child') || effectiveType.includes('parent') ? effectiveType : 'rel'}`;

      // Deduplicate: If generic "sibling_of" exists and specific "sister_of" / "brother_of" is found, upgrade to specific.
      if (!targetMap.has(key)) {
        targetMap.set(key, { relationLabel: label, targetName, relType: effectiveType });
      } else {
        const existing = targetMap.get(key)!;
        if (existing.relType === 'sibling_of' && (effectiveType === 'sister_of' || effectiveType === 'brother_of')) {
          targetMap.set(key, { relationLabel: label, targetName, relType: effectiveType });
        }
      }
    }

    return Array.from(targetMap.values()).map(v => ({ relationLabel: v.relationLabel, targetName: v.targetName }));
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-app text-xs transition-colors">
      {/* Main Directory Area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
          <div>
            <h2 className="text-lg font-bold text-txtPrimary flex items-center space-x-2">
              <Users className="w-5 h-5 text-accent-light" />
              <span>Character Directory & Story State</span>
            </h2>
            <p className="text-xs text-txtSecondary mt-0.5">
              Character profiles, current locations, key relationships, possessions, and acquired knowledge.
            </p>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            {availableLocations.length > 0 && (
              <div className="relative">
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="bg-card border border-border rounded-xl px-3 py-1.5 text-txtPrimary focus:outline-none focus:border-accent text-xs appearance-none pr-8 cursor-pointer font-mono"
                >
                  <option value="ALL">All Locations ({characters.length})</option>
                  {availableLocations.map((loc) => (
                    <option key={loc} value={loc}>
                      📍 {loc}
                    </option>
                  ))}
                </select>
                <MapPin className="w-3.5 h-3.5 text-txtMuted absolute right-2.5 top-2.5 pointer-events-none" />
              </div>
            )}

            <div className="relative w-full sm:w-64">
              <input
                type="text"
                placeholder="Search characters..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-card border border-border rounded-xl px-3 py-1.5 pl-8 text-txtPrimary placeholder-txtMuted focus:outline-none focus:border-accent text-xs"
              />
              <Search className="w-3.5 h-3.5 text-txtMuted absolute left-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="p-12 text-center text-txtSecondary space-y-2 bg-card rounded-2xl border border-border">
            <UserCheck className="w-10 h-10 text-accent-light mx-auto opacity-40" />
            <h4 className="font-bold text-txtPrimary text-sm">No Character Profiles Found</h4>
            <p className="text-xs text-txtMuted max-w-sm mx-auto">
              Run AI Scene Analysis to extract character profiles, locations, and narrative relationships.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 max-w-5xl gap-4">
            {filtered.map((char) => {
              const isSelected = selectedCharacter?.id === char.id;
              const majorRels = getMajorRelationships(char);

              return (
                <div
                  key={char.id}
                  onClick={() => setSelectedCharacter(char)}
                  className={`p-5 rounded-2xl bg-card border transition-all cursor-pointer space-y-3.5 shadow-xs hover:shadow-md ${
                    isSelected
                      ? 'ring-2 ring-accent border-accent bg-card'
                      : 'border-border hover:border-accent/50'
                  }`}
                >
                  {/* Card Header: Name & Location Badge */}
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-primary border border-border flex items-center justify-center text-white font-bold text-sm shadow-sm shrink-0">
                        {char.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold text-txtPrimary text-base leading-tight">{char.name}</h3>
                        {char.residence && (
                          <span className="text-[11px] text-txtMuted font-mono block mt-0.5">
                            Residence: {char.residence}
                          </span>
                        )}
                      </div>
                    </div>

                    {char.current_location && (
                      <span className="px-2.5 py-1 rounded-full bg-secondary/15 border border-secondary/30 text-secondary font-bold text-[10px] flex items-center space-x-1 font-mono shrink-0">
                        <MapPin className="w-3 h-3 mr-0.5 text-secondary" />
                        <span>{char.current_location.name}</span>
                      </span>
                    )}
                  </div>

                  {/* Major Character Relationships */}
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider flex items-center space-x-1">
                      <HeartHandshake className="w-3.5 h-3.5 text-amber-500" />
                      <span>Major Character Connections:</span>
                    </span>

                    {majorRels.length === 0 ? (
                      <p className="text-[11px] text-txtMuted italic pl-0.5">
                        No major familial or structural relationships recorded.
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {majorRels.map((rel, idx) => (
                          <span
                            key={idx}
                            onClick={(e) => {
                              e.stopPropagation();
                              const targetChar = characters.find(
                                (c) => c.name.toLowerCase() === rel.targetName.toLowerCase()
                              );
                              if (targetChar) {
                                setSelectedCharacter(targetChar);
                              }
                            }}
                            className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-700 dark:text-amber-300 font-medium text-[11px] flex items-center gap-1 hover:bg-amber-500/20 hover:border-amber-500/40 cursor-pointer transition-colors"
                            title={`Click to view ${rel.targetName}'s profile`}
                          >
                            <span className="capitalize font-semibold">{rel.relationLabel}</span>
                            <span className="font-bold">{rel.targetName}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Footer Drawer Prompt */}
                  <div className="pt-2 border-t border-border/60 flex items-center justify-between text-[11px] text-txtMuted font-mono">
                    <span>
                      {(char.possessions?.length || 0)} possessions &bull; {(char.knowledge?.length || 0)} knowledge facts
                    </span>
                    <span className="text-accent-light font-semibold flex items-center gap-0.5 group-hover:underline">
                      View Full Profile &rarr;
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Selected Character Inspector Side Panel (Window-locked) */}
      {selectedCharacter && (
        <div className="w-80 sm:w-96 border-l border-border bg-card flex flex-col h-full shrink-0 shadow-xl overflow-hidden">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-4 border-b border-border shrink-0 bg-card">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-xs">
                {selectedCharacter.name.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <h3 className="font-bold text-txtPrimary text-sm leading-tight">{selectedCharacter.name}</h3>
                <span className="text-[10px] text-txtMuted font-mono">Character Profile</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedCharacter(null)}
              className="text-xs font-semibold text-txtMuted hover:text-txtPrimary px-2 py-1 rounded hover:bg-cardHover transition-colors"
            >
              Close &times;
            </button>
          </div>

          {/* Scrollable Content */}
          <div className="p-4 space-y-5 text-xs flex-1 overflow-y-auto min-h-0">
            {/* Location & Residence Info */}
            <div className="p-3 rounded-xl bg-cardHover border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-txtMuted">Current Location</span>
                {selectedCharacter.current_location ? (
                  <span className="px-2 py-0.5 rounded-full bg-secondary/15 text-secondary font-bold text-[10px] flex items-center gap-1 font-mono">
                    <MapPin className="w-3 h-3" />
                    {selectedCharacter.current_location.name}
                  </span>
                ) : (
                  <span className="text-txtMuted text-[11px] italic">Unspecified</span>
                )}
              </div>

              {selectedCharacter.residence && (
                <div className="flex items-center justify-between pt-1 border-t border-border/50 text-[11px]">
                  <span className="font-bold text-txtMuted">Residence:</span>
                  <span className="text-txtPrimary font-medium">{selectedCharacter.residence}</span>
                </div>
              )}
            </div>

            {/* Possessions Section */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider flex items-center space-x-1">
                <Package className="w-3.5 h-3.5 text-tertiary" />
                <span>Possessions ({(selectedCharacter.possessions?.length || 0)}):</span>
              </span>

              {(!selectedCharacter.possessions || selectedCharacter.possessions.length === 0) ? (
                <p className="text-[11px] text-txtMuted italic p-3 rounded-lg bg-cardHover border border-border">
                  No physical items currently possessed.
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5 p-3 rounded-lg bg-cardHover border border-border">
                  {Array.from(
                    new Map(selectedCharacter.possessions.map((p) => [p.name.toLowerCase().trim(), p])).values()
                  ).map((p, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-md bg-card border border-border text-txtPrimary font-mono text-[11px] shadow-2xs">
                      {p.name}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Acquired Knowledge Section */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-txtMuted uppercase tracking-wider flex items-center space-x-1">
                <BookOpen className="w-3.5 h-3.5 text-secondary" />
                <span>Acquired Story Knowledge ({(selectedCharacter.knowledge?.length || 0)}):</span>
              </span>

              {(!selectedCharacter.knowledge || selectedCharacter.knowledge.length === 0) ? (
                <p className="text-[11px] text-txtMuted italic p-3 rounded-lg bg-cardHover border border-border">
                  No explicit story knowledge states recorded.
                </p>
              ) : (() => {
                const uniqueKnowledgeMap = new Map();
                selectedCharacter.knowledge.forEach((k) => {
                  const normKey = k.knowledge.trim().replace(/^["']|["']$/g, '').replace(/[.,!?]+$/, '').trim().toLowerCase();
                  if (!uniqueKnowledgeMap.has(normKey)) {
                    uniqueKnowledgeMap.set(normKey, k);
                  }
                });
                const uniqueKnowledge = Array.from(uniqueKnowledgeMap.values());

                return (
                  <div className="space-y-2">
                    {uniqueKnowledge.map((k, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-cardHover border border-border text-[11px] font-mono text-txtPrimary space-y-1.5">
                        <p className="leading-relaxed font-sans">
                          "{k.knowledge.replace(/^["']|["']$/g, '').replace(/[.,!?]+$/, '').trim()}"
                        </p>
                        <div className="flex items-center justify-between text-[10px] text-txtMuted pt-1 border-t border-border/40">
                          <span className="uppercase font-bold text-secondary">{k.knowledge_type}</span>
                          {k.source_scene_number && onSelectSceneNumber && (
                            <button
                              onClick={() => onSelectSceneNumber(k.source_scene_number!)}
                              className="text-accent-light hover:underline font-bold"
                            >
                              Jump to Scene {k.source_scene_number} &rarr;
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
