'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
  PlotEventItem, 
  TimelineViewResponse, 
  getTimeline, 
  extractTimeline 
} from '../../lib/api';
import { 
  GitCommit, 
  RotateCw, 
  Layers, 
  Sparkles, 
  ArrowUpRight, 
  AlertCircle, 
  ExternalLink,
  ShieldAlert,
  Zap,
  Info,
  CheckCircle2,
  Bookmark,
  Eye
} from 'lucide-react';

interface TimelineViewProps {
  projectId: string;
  onNavigateToScene?: (sceneNumber: number) => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({ projectId, onNavigateToScene }) => {
  const [timelineData, setTimelineData] = useState<TimelineViewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTrack, setSelectedTrack] = useState<string>('ALL');
  const [selectedEvent, setSelectedEvent] = useState<PlotEventItem | null>(null);

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTimeline(projectId);
      setTimelineData(data);
    } catch (err: any) {
      console.error('Failed to load timeline:', err);
      setError(err.message || 'Failed to load timeline events.');
    } finally {
      setLoading(false);
    }
  };

  const handleReExtract = async () => {
    try {
      setExtracting(true);
      setError(null);
      const data = await extractTimeline(projectId);
      setTimelineData(data);
    } catch (err: any) {
      console.error('Failed to re-extract plot timeline:', err);
      setError(err.message || 'Failed to extract plot timeline.');
    } finally {
      setExtracting(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchTimeline();
    }
  }, [projectId]);

  // Unique track names
  const availableTracks = useMemo(() => {
    if (!timelineData) return [];
    return Array.from(new Set(timelineData.events.map(e => e.track_name)));
  }, [timelineData]);

  // Track counts
  const trackCounts = useMemo(() => {
    if (!timelineData) return { main: 0, subplot: 0, custom: {} as Record<string, number> };
    const main = timelineData.events.filter(e => e.track_type === 'MAIN_PLOT').length;
    const subplot = timelineData.events.filter(e => e.track_type === 'SUBPLOT').length;
    const custom: Record<string, number> = {};
    timelineData.events.forEach(e => {
      if (e.track_name) {
        custom[e.track_name] = (custom[e.track_name] || 0) + 1;
      }
    });
    return { main, subplot, custom };
  }, [timelineData]);

  // Filtered events with Search
  const filteredEvents = useMemo(() => {
    if (!timelineData) return [];
    let list = timelineData.events;
    if (selectedTrack === 'MAIN_PLOT') list = list.filter(e => e.track_type === 'MAIN_PLOT');
    else if (selectedTrack === 'SUBPLOT') list = list.filter(e => e.track_type === 'SUBPLOT');
    else if (selectedTrack !== 'ALL') list = list.filter(e => e.track_name === selectedTrack);

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(e =>
        e.title.toLowerCase().includes(q) ||
        e.description.toLowerCase().includes(q) ||
        (e.excerpt && e.excerpt.toLowerCase().includes(q))
      );
    }
    return list;
  }, [timelineData, selectedTrack, searchQuery]);

  // Group events by scene number
  const scenesGrouped = useMemo(() => {
    const map = new Map<number, PlotEventItem[]>();
    filteredEvents.forEach(e => {
      const list = map.get(e.scene_number) || [];
      list.push(e);
      map.set(e.scene_number, list);
    });
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [filteredEvents]);

  // Helper for Importance Colors
  const getImportanceBadge = (importance: string) => {
    switch (importance?.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <Sparkles className="w-3 h-3 text-amber-500" />
            CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
            <Zap className="w-3 h-3 text-blue-500" />
            HIGH
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md bg-neutral-500/15 text-neutral-600 dark:text-neutral-400 border border-neutral-500/30">
            <Info className="w-3 h-3 text-neutral-400" />
            MEDIUM
          </span>
        );
    }
  };

  // Helper for Connection Badges
  const getConnectionBadge = (type?: string | null, targetEventId?: string | null) => {
    if (
      !type || 
      !targetEventId || 
      type === 'null' || 
      targetEventId === 'null' || 
      type === 'None' || 
      targetEventId === 'None' ||
      !type.trim() ||
      !targetEventId.trim()
    ) {
      return null;
    }
    let badgeClass = 'bg-neutral-500/10 text-neutral-600 border-neutral-500/20';
    let icon = <ArrowUpRight className="w-3 h-3 shrink-0" />;

    switch (type.toUpperCase()) {
      case 'TRIGGERS':
        badgeClass = 'bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border-cyan-500/30';
        icon = <Zap className="w-3 h-3 text-cyan-500 shrink-0" />;
        break;
      case 'CONVERGES_WITH':
        badgeClass = 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30';
        icon = <GitCommit className="w-3 h-3 text-emerald-500 shrink-0" />;
        break;
      case 'REVEALS':
        badgeClass = 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30';
        icon = <Eye className="w-3 h-3 text-amber-500 shrink-0" />;
        break;
      case 'CONTRADICTS':
        badgeClass = 'bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30';
        icon = <ShieldAlert className="w-3 h-3 text-rose-500 shrink-0" />;
        break;
    }

    const targetEvent = timelineData?.events.find(e => e.event_id === targetEventId);
    let targetLabel = targetEventId;
    if (targetEvent) {
      targetLabel = `Sc. ${targetEvent.scene_number}: ${targetEvent.title}`;
    } else {
      const match = targetEventId.match(/scene_(\d+)_event_(\d+)/i);
      if (match) {
        targetLabel = `Sc. ${match[1]} Event ${match[2]}`;
      }
    }

    return (
      <button
        type="button"
        onClick={(e) => {
          if (targetEvent) {
            e.stopPropagation();
            setSelectedEvent(targetEvent);
          }
        }}
        title={targetEvent ? `Jump to target event: ${targetEvent.title}` : targetEventId}
        className={`inline-flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-md border text-left ${badgeClass} hover:opacity-90 max-w-[260px] cursor-pointer`}
      >
        {icon}
        <span className="font-semibold shrink-0">{type}</span>
        <span className="opacity-80 text-[11px] truncate">&rarr; {targetLabel}</span>
      </button>
    );
  };


  return (
    <div className="flex flex-col h-full bg-app text-txtPrimary overflow-hidden transition-colors">
      {/* Top Header & Toolbar */}
      <div className="p-4 sm:p-6 border-b border-border bg-card shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <GitCommit className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-txtPrimary">Plot & Subplot Timeline Visualizer</h1>
            </div>
            <p className="text-xs text-txtSecondary mt-1">
              Structural narrative milestones extracted via Script Supervisor Plot Structure Agent
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative w-48 sm:w-64">
              <input
                type="text"
                placeholder="Search plot events..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-cardHover border border-border rounded-xl px-3 py-1.5 text-xs text-txtPrimary placeholder-txtMuted focus:outline-none focus:border-amber-500"
              />
            </div>

            <button
              onClick={handleReExtract}
              disabled={extracting}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary text-white hover:bg-secondary disabled:opacity-50 transition-all shadow-sm shrink-0"
            >
              <RotateCw className={`w-3.5 h-3.5 ${extracting ? 'animate-spin' : ''}`} />
              {extracting ? 'Extracting...' : 'Re-Analyze Structure'}
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border overflow-x-auto pb-1 text-xs">
          <span className="text-txtSecondary font-medium flex items-center gap-1 mr-1 shrink-0">
            <Layers className="w-3.5 h-3.5" /> Track Filter:
          </span>
          
          <button
            onClick={() => setSelectedTrack('ALL')}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 ${
              selectedTrack === 'ALL'
                ? 'bg-accent/20 border border-accent/40 text-txtPrimary font-bold shadow-xs'
                : 'bg-cardHover border border-border text-txtSecondary hover:text-txtPrimary'
            }`}
          >
            All Events ({timelineData?.events.length || 0})
          </button>

          <button
            onClick={() => setSelectedTrack('MAIN_PLOT')}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 ${
              selectedTrack === 'MAIN_PLOT'
                ? 'bg-amber-600 text-white font-semibold shadow-xs'
                : 'bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20'
            }`}
          >
            Main Plot Spine ({trackCounts.main})
          </button>

          <button
            onClick={() => setSelectedTrack('SUBPLOT')}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 ${
              selectedTrack === 'SUBPLOT'
                ? 'bg-purple-600 text-white font-semibold shadow-xs'
                : 'bg-purple-500/10 border border-purple-500/30 text-purple-700 dark:text-purple-300 hover:bg-purple-500/20'
            }`}
          >
            Subplots ({trackCounts.subplot})
          </button>

          {availableTracks.map(trackName => (
            <button
              key={trackName}
              onClick={() => setSelectedTrack(trackName)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 ${
                selectedTrack === trackName
                  ? 'bg-secondary text-white font-semibold shadow-xs'
                  : 'bg-cardHover border border-border text-txtSecondary hover:text-txtPrimary'
              }`}
            >
              {trackName} ({trackCounts.custom[trackName] || 0})
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Timeline Canvas */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-8">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-txtSecondary">
              <RotateCw className="w-8 h-8 animate-spin text-amber-500 mb-3" />
              <p className="text-sm font-medium">Extracting and loading plot structure timeline...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-500" />
              <div>
                <p className="font-semibold text-sm">Failed to Load Timeline</p>
                <p className="mt-1">{error}</p>
                <button
                  onClick={fetchTimeline}
                  className="mt-3 px-3 py-1.5 rounded-md bg-rose-600 text-white font-medium text-xs hover:bg-rose-700"
                >
                  Retry Loading
                </button>
              </div>
            </div>
          ) : scenesGrouped.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center text-txtSecondary bg-card border border-border rounded-2xl p-8 max-w-md mx-auto my-12">
              <GitCommit className="w-12 h-12 text-txtMuted mb-3 stroke-[1.5]" />
              <p className="text-base font-semibold text-txtPrimary">No Plot Events Found</p>
              <p className="text-xs text-txtMuted max-w-sm mt-1">
                No major narrative milestones match the current filter or screenplay scenes have not yet been analyzed.
              </p>
              <button
                onClick={handleReExtract}
                className="mt-4 px-4 py-2 text-xs font-semibold rounded-lg bg-primary text-white hover:bg-secondary transition-colors"
              >
                Run AI Plot Structure Extraction
              </button>
            </div>
          ) : (
            <div className="relative pl-6 sm:pl-10 space-y-10">
              {/* Vertical Timeline Spine Line */}
              <div className="absolute top-2 bottom-6 left-3 sm:left-5 w-0.5 bg-gradient-to-b from-amber-500 via-border to-transparent" />

              {scenesGrouped.map(([sceneNum, events]) => (
                <div key={sceneNum} className="relative group">
                  {/* Scene Marker Node */}
                  <div className="absolute -left-6 sm:-left-10 top-0.5 flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-amber-500 text-white font-bold text-xs ring-4 ring-app shadow-md z-10">
                    {sceneNum}
                  </div>

                  {/* Scene Header */}
                  <div className="flex items-center flex-wrap gap-2.5 mb-3 pl-3 sm:pl-4">
                    <h3 className="text-sm font-bold text-txtPrimary tracking-wide">
                      SCENE {sceneNum}
                    </h3>
                    <span className="text-xs text-txtSecondary bg-amber-500/15 border border-amber-500/30 px-2.5 py-0.5 rounded-full font-medium">
                      {events.length} {events.length === 1 ? 'event' : 'events'}
                    </span>

                    {onNavigateToScene && (
                      <button
                        onClick={() => onNavigateToScene(sceneNum)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 dark:text-amber-400 hover:underline ml-1"
                      >
                        Open Scene {sceneNum} in Editor &rarr;
                      </button>
                    )}
                  </div>

                  {/* Events Grid for Scene */}
                  <div className={`grid gap-4 pl-3 sm:pl-4 ${
                    events.length === 1 ? 'grid-cols-1 max-w-2xl' : 'grid-cols-1 lg:grid-cols-2 max-w-4xl'
                  }`}>
                    {events.map((evt) => {
                      const isSelected = selectedEvent?.event_id === evt.event_id;
                      const isMainPlot = evt.track_type === 'MAIN_PLOT';

                      return (
                        <div
                          key={`${evt.scene_number}_${evt.event_id}_${evt.title}`}
                          onClick={() => setSelectedEvent(evt)}

                          className={`cursor-pointer transition-all duration-200 rounded-xl p-4 border text-xs relative max-w-2xl ${
                            isSelected
                              ? 'ring-2 ring-amber-500 border-amber-500 bg-card shadow-md'
                              : 'bg-card hover:shadow-md hover:border-amber-500/50 border-border'
                          }`}
                        >
                          {/* Top Track & Importance Header */}
                          <div className="flex items-center justify-between gap-2 mb-2">
                            <span
                              className={`font-semibold px-2 py-0.5 rounded text-[11px] uppercase tracking-wider ${
                                isMainPlot
                                  ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30'
                                  : 'bg-purple-500/15 text-purple-700 dark:text-purple-300 border border-purple-500/30'
                              }`}
                            >
                              {evt.track_name || (isMainPlot ? 'Main Plot Spine' : 'Subplot')}
                            </span>
                            {getImportanceBadge(evt.importance_score)}
                          </div>

                          {/* Title & Description */}
                          <h4 className="text-sm font-bold text-txtPrimary mb-1 leading-snug">
                            {evt.title}
                          </h4>
                          <p className="text-txtSecondary leading-relaxed mb-3">
                            {evt.description}
                          </p>

                          {/* Exact Excerpt Provenance Box */}
                          {evt.excerpt && (
                            <div className="p-2.5 rounded-lg bg-cardHover border border-border text-[11px] font-mono text-txtPrimary italic mb-3">
                              <span className="font-sans text-[10px] font-bold not-italic uppercase tracking-wider text-txtMuted block mb-0.5">
                                Screenplay Provenance:
                              </span>
                              "{evt.excerpt}"
                            </div>
                          )}

                          {/* Footer Action Bar */}
                          <div className="pt-2 border-t border-border flex items-center justify-between">
                            {getConnectionBadge(evt.connection_type, evt.connected_to_event) || <div />}

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (onNavigateToScene) {
                                  onNavigateToScene(evt.scene_number);
                                }
                              }}
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400 hover:text-amber-500 ml-auto"
                            >
                              View in Editor <ExternalLink className="w-3 h-3" />
                            </button>
                          </div>

                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Event Side Inspector Panel (Window-locked sticky layout) */}
        {selectedEvent && (
          <div className="w-80 sm:w-96 border-l border-border bg-card flex flex-col h-full shrink-0 shadow-xl overflow-hidden">
            {/* Panel Header */}
            <div className="flex items-center justify-between p-4 border-b border-border shrink-0 bg-card">
              <div className="flex items-center gap-2">
                <Bookmark className="w-4 h-4 text-amber-500" />
                <h3 className="text-sm font-bold text-txtPrimary">Event Details</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-xs font-semibold text-txtMuted hover:text-txtPrimary px-2 py-1 rounded hover:bg-cardHover transition-colors"
              >
                Close &times;
              </button>
            </div>

            {/* Scrollable Event Content Body */}
            <div className="p-4 space-y-4 text-xs flex-1 overflow-y-auto min-h-0">
              <div>
                <span className="text-[10px] uppercase font-bold text-txtMuted tracking-wider">
                  Event Identifier
                </span>
                <p className="font-mono text-xs font-semibold text-txtPrimary mt-0.5">
                  {selectedEvent.event_id}
                </p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-txtMuted tracking-wider">
                  Title & Track
                </span>
                <p className="text-sm font-bold text-txtPrimary mt-0.5 leading-snug">
                  {selectedEvent.title}
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cardHover border border-border text-txtSecondary">
                    {selectedEvent.track_type}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                    {selectedEvent.track_name}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-txtMuted tracking-wider">
                  Narrative Description
                </span>
                <p className="text-xs text-txtPrimary leading-relaxed mt-1 p-3 rounded-lg bg-cardHover border border-border">
                  {selectedEvent.description}
                </p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-[var(--text-secondary,#586274)] tracking-wider">
                  Exact Screenplay Excerpt
                </span>
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-xs font-mono text-txtPrimary mt-1 leading-relaxed">
                  "{selectedEvent.excerpt}"
                </div>
              </div>

              {getConnectionBadge(selectedEvent.connection_type, selectedEvent.connected_to_event) && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-txtMuted tracking-wider block mb-1">
                    Structural Narrative Connection
                  </span>
                  <div>
                    {getConnectionBadge(selectedEvent.connection_type, selectedEvent.connected_to_event)}
                  </div>
                </div>
              )}

              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300">
                <div className="flex items-center gap-1.5 font-bold mb-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  Plot Materiality Test Passed
                </div>
                <p className="text-[11px] opacity-90 leading-relaxed">
                  Removing this event would materially alter the main conflict or subplot progression.
                </p>
              </div>
            </div>

            {/* Fixed Footer Action Button */}
            {onNavigateToScene && (
              <div className="p-4 border-t border-border shrink-0 bg-card">
                <button
                  onClick={() => onNavigateToScene(selectedEvent.scene_number)}
                  className="w-full py-2.5 px-4 text-xs font-bold rounded-lg bg-primary text-white hover:bg-secondary flex items-center justify-center gap-2 shadow-sm transition-all"
                >
                  Jump to Scene {selectedEvent.scene_number} in Editor
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
