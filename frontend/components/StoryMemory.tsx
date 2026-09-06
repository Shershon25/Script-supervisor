'use client';

import React from 'react';
import { StoryStateResponse } from '@/lib/api';
import { Database, Users, MapPin, Package, CheckCircle, Film, Layers } from 'lucide-react';

interface Props {
  storyData: StoryStateResponse | null;
  loading: boolean;
}

export default function StoryMemory({ storyData, loading }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-8 text-gray-400">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 animate-pulse text-accent" />
          <span className="text-xs font-medium">Fetching Story Memory...</span>
        </div>
      </div>
    );
  }

  if (!storyData) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-500 border border-dashed border-border rounded-2xl">
        <Database className="w-10 h-10 text-gray-600 mb-3" />
        <h3 className="text-sm font-semibold text-gray-400">Story Memory Empty</h3>
        <p className="text-xs text-gray-600 max-w-xs mt-1">
          As you analyze screenplay scenes, entities, facts, and events will accumulate here permanently.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1 text-xs">
      {/* Header Banner */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-accent/20 to-purple-900/30 border border-accent/30 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-accent-light" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Persistent Story World
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-card border border-border space-y-1">
          <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
            <Users className="w-3.5 h-3.5 text-accent-light" />
            <span>Characters ({storyData.characters.length})</span>
          </h4>
          <div className="text-[11px] text-gray-400">
            {storyData.characters.map((c: any) => c.name).join(', ') || 'None'}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-card border border-border space-y-1">
          <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
            <Package className="w-3.5 h-3.5 text-amber-400" />
            <span>Objects ({storyData.objects.length})</span>
          </h4>
          <div className="text-[11px] text-gray-400">
            {storyData.objects.map((o: any) => o.name).join(', ') || 'None'}
          </div>
        </div>
      </div>
    </div>
  );
}
