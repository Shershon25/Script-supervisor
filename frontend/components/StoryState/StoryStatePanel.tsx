'use client';

import React, { useState } from 'react';
import { StoryStateResponse, CharacterState } from '@/lib/api';
import { Users, MapPin, Package, BookOpen, Layers, CheckCircle2, Film, Brain, Share2, Tag } from 'lucide-react';

interface Props {
  storyState: StoryStateResponse | null;
  loading: boolean;
  onSelectSceneNumber?: (sceneNum: number) => void;
}

export default function StoryStatePanel({ storyState, loading, onSelectSceneNumber }: Props) {
  const [activeSection, setActiveSection] = useState<'all' | 'characters' | 'objects' | 'facts' | 'knowledge'>('all');

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Layers className="w-6 h-6 animate-spin text-accent mb-2" />
        <span className="text-xs font-medium">Deriving Story World State...</span>
      </div>
    );
  }

  if (!storyState || (storyState.characters.length === 0 && storyState.events.length === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-500 border border-dashed border-border rounded-2xl">
        <Layers className="w-10 h-10 text-gray-600 mb-3" />
        <h3 className="text-sm font-semibold text-gray-400">Story State Empty</h3>
        <p className="text-xs text-gray-600 max-w-xs mt-1">
          Analyze screenplay scenes to build an evolving, persistent model of characters, locations, possessions, and knowledge.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
      {/* Header Bar */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-accent/20 via-purple-900/30 to-card border border-accent/30 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-accent-light" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Current Story World State
          </span>
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-semibold text-gray-300">
          <span className="px-2 py-0.5 rounded bg-accent/20 border border-accent/30 text-accent-light">
            {storyState.characters.length} Characters
          </span>
          <span className="px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-amber-300">
            {storyState.locations.length} Locations
          </span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
            {storyState.objects.length} Objects
          </span>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex space-x-1 bg-card/60 p-1 rounded-xl border border-border text-xs">
        <button
          onClick={() => setActiveSection('all')}
          className={`flex-1 py-1 px-2 rounded-lg font-medium transition-colors ${activeSection === 'all' ? 'bg-accent text-white shadow' : 'text-gray-400 hover:text-white'}`}
        >
          All Overview
        </button>
        <button
          onClick={() => setActiveSection('characters')}
          className={`flex-1 py-1 px-2 rounded-lg font-medium transition-colors ${activeSection === 'characters' ? 'bg-accent text-white shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Characters ({storyState.characters.length})
        </button>
        <button
          onClick={() => setActiveSection('objects')}
          className={`flex-1 py-1 px-2 rounded-lg font-medium transition-colors ${activeSection === 'objects' ? 'bg-accent text-white shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Objects ({storyState.objects.length})
        </button>
        <button
          onClick={() => setActiveSection('knowledge')}
          className={`flex-1 py-1 px-2 rounded-lg font-medium transition-colors ${activeSection === 'knowledge' ? 'bg-accent text-white shadow' : 'text-gray-400 hover:text-white'}`}
        >
          Knowledge ({storyState.knowledge_states.length})
        </button>
      </div>

      {/* CHARACTERS SECTION */}
      {(activeSection === 'all' || activeSection === 'characters') && storyState.characters.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Users className="w-4 h-4 text-accent-light" />
            <span>Character Profiles & State</span>
          </h4>

          <div className="grid grid-cols-1 gap-3">
            {storyState.characters.map((c) => (
              <div key={c.id} className="p-4 rounded-xl bg-background border border-border space-y-2.5">
                <div className="flex items-center justify-between">
                  <h5 className="text-sm font-bold text-white flex items-center space-x-2">
                    <span>{c.name}</span>
                    {c.attributes?.occupation && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-card text-gray-400 border border-border">
                        {c.attributes.occupation}
                      </span>
                    )}
                  </h5>
                </div>

                {/* Residence vs Current Location */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {c.residence && (
                    <div className="p-2 rounded-lg bg-card/60 border border-border flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-accent-amber flex-shrink-0" />
                      <span className="text-gray-400">Residence:</span>
                      <span className="font-semibold text-white">{c.residence}</span>
                    </div>
                  )}
                  {c.current_location && (
                    <div className="p-2 rounded-lg bg-accent/10 border border-accent/20 flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-accent-light flex-shrink-0 animate-bounce" />
                      <span className="text-accent-light font-medium">Current Location:</span>
                      <span className="font-bold text-white">{c.current_location.name}</span>
                    </div>
                  )}
                </div>

                {/* Possessions */}
                {c.possessions.length > 0 && (
                  <div className="text-xs space-y-1">
                    <span className="text-gray-400 font-medium flex items-center space-x-1">
                      <Package className="w-3 h-3 text-accent-emerald" />
                      <span>Possessions:</span>
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {c.possessions.map((p, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-medium text-[11px]">
                          {p.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Character Relationships */}
                {c.relationships.length > 0 && (
                  <div className="text-xs space-y-1 pt-1">
                    <span className="text-gray-400 font-medium flex items-center space-x-1">
                      <Share2 className="w-3 h-3 text-purple-400" />
                      <span>Relationships:</span>
                    </span>
                    <ul className="space-y-1">
                      {c.relationships.map((rel) => (
                        <li key={rel.id} className="text-[11px] text-gray-300 flex items-center justify-between p-1.5 rounded bg-card">
                          <span>
                            <span className="font-semibold text-white">{rel.source.name}</span>{' '}
                            <span className="font-mono text-purple-300">({rel.relationship_type})</span>{' '}
                            <span className="font-semibold text-white">{rel.target?.name || ''}</span>
                          </span>
                          {rel.source_scene_number && onSelectSceneNumber && (
                            <button
                              onClick={() => onSelectSceneNumber(rel.source_scene_number!)}
                              className="text-[10px] text-accent-light hover:underline flex items-center space-x-0.5"
                            >
                              <Tag className="w-2.5 h-2.5" />
                              <span>Scene {rel.source_scene_number}</span>
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Character Knowledge */}
                {c.knowledge.length > 0 && (
                  <div className="text-xs space-y-1 pt-1">
                    <span className="text-gray-400 font-medium flex items-center space-x-1">
                      <Brain className="w-3 h-3 text-accent-light" />
                      <span>Known Information:</span>
                    </span>
                    <ul className="space-y-1">
                      {c.knowledge.map((k) => (
                        <li key={k.id} className="text-[11px] text-gray-200 p-2 rounded bg-accent/10 border border-accent/20 flex items-center justify-between">
                          <span>• {k.knowledge}</span>
                          {k.source_scene_number && onSelectSceneNumber && (
                            <button
                              onClick={() => onSelectSceneNumber(k.source_scene_number!)}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-accent/20 text-accent-light hover:bg-accent/30 font-semibold"
                            >
                              Scene {k.source_scene_number}
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* OBJECTS SECTION */}
      {(activeSection === 'all' || activeSection === 'objects') && storyState.objects.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Package className="w-4 h-4 text-accent-emerald" />
            <span>Story Objects & Ownership</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {storyState.objects.map((o) => (
              <div key={o.id} className="p-3 rounded-lg bg-background border border-border text-xs space-y-1">
                <div className="font-bold text-white flex items-center justify-between">
                  <span>{o.name}</span>
                </div>
                {o.current_owner && (
                  <div className="text-[11px] text-gray-400 flex items-center space-x-1">
                    <span>Owner:</span>
                    <span className="font-semibold text-accent-emerald">{o.current_owner.name}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KNOWLEDGE STATES SECTION */}
      {(activeSection === 'all' || activeSection === 'knowledge') && storyState.knowledge_states.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Brain className="w-4 h-4 text-accent-light" />
            <span>Character Knowledge Log</span>
          </h4>
          <div className="space-y-2">
            {storyState.knowledge_states.map((k) => (
              <div key={k.id} className="p-3 rounded-lg bg-background border border-border text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-white">{k.character.name}</span>
                  <span className="text-gray-400 mx-1.5">knows:</span>
                  <span className="font-medium text-gray-200">{k.knowledge}</span>
                </div>
                {k.source_scene_number && onSelectSceneNumber && (
                  <button
                    onClick={() => onSelectSceneNumber(k.source_scene_number!)}
                    className="px-2 py-0.5 rounded bg-accent/20 text-accent-light text-[10px] font-semibold hover:bg-accent/30"
                  >
                    Scene {k.source_scene_number}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FACTS SECTION */}
      {storyState.facts.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center space-x-1.5">
            <BookOpen className="w-4 h-4 text-accent-amber" />
            <span>Established World Facts</span>
          </h4>
          <div className="space-y-2">
            {storyState.facts.map((f) => (
              <div key={f.id} className="p-2.5 rounded-lg bg-background border border-border text-xs flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-accent-light">{f.subject.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-card text-gray-400 border border-border">
                    {f.predicate}
                  </span>
                  <span className="font-medium text-gray-200">{f.value}</span>
                </div>
                {f.source_scene_number && onSelectSceneNumber && (
                  <button
                    onClick={() => onSelectSceneNumber(f.source_scene_number!)}
                    className="text-[10px] text-gray-400 hover:text-accent-light font-mono hover:underline"
                  >
                    Scene {f.source_scene_number}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CHRONOLOGICAL EVENTS TIMELINE */}
      {storyState.events.length > 0 && (
        <div className="p-4 rounded-xl bg-card border border-border space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Film className="w-4 h-4 text-purple-400" />
            <span>Chronological Event Timeline</span>
          </h4>
          <div className="relative border-l border-border ml-3 pl-4 space-y-3">
            {storyState.events.map((ev) => (
              <div key={ev.id} className="relative group">
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-accent-light ring-4 ring-card" />
                <div className="p-3 rounded-xl bg-background border border-border space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-accent-light font-mono px-2 py-0.5 rounded bg-accent/10">
                        {ev.event_type}
                      </span>
                      {ev.scene_number && onSelectSceneNumber && (
                        <button
                          onClick={() => onSelectSceneNumber(ev.scene_number!)}
                          className="font-semibold text-gray-400 hover:text-accent-light flex items-center hover:underline"
                        >
                          <Film className="w-3 h-3 mr-1 text-gray-500" />
                          Scene {ev.scene_number}
                        </button>
                      )}
                    </div>
                    {ev.location && (
                      <span className="text-accent-amber font-medium flex items-center">
                        <MapPin className="w-3 h-3 mr-1" />
                        {ev.location.name}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-200 font-medium">{ev.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
