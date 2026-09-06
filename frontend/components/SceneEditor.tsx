'use client';

import React, { useState, useEffect } from 'react';
import { Scene, analyzeScene } from '@/lib/api';
import { Play, Sparkles, AlertCircle, FileText } from 'lucide-react';

interface Props {
  projectId: string;
  scenes: Scene[];
  activeSceneNumber: number;
  onSceneProcessed: (scene: Scene, analysis: any) => void;
  onSelectScene: (scene: Scene) => void;
}

export default function SceneEditor({
  projectId,
  scenes,
  activeSceneNumber,
  onSceneProcessed,
  onSelectScene,
}: Props) {
  const [sceneNumber, setSceneNumber] = useState<number>(activeSceneNumber);
  const [rawText, setRawText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    setSceneNumber(activeSceneNumber);
  }, [activeSceneNumber]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim() || sceneNumber <= 0) return;

    setLoading(true);
    setError('');

    try {
      const res = await analyzeScene(projectId, sceneNumber, rawText);
      onSceneProcessed(res.scene, res.analysis);
      setRawText('');
      setSceneNumber(sceneNumber + 1);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze scene. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = (sampleNum: number) => {
    if (sampleNum === 1) {
      setSceneNumber(1);
      setRawText(
        `INT. JOHN'S APARTMENT - NIGHT\n\nJohn enters his apartment.\n\nHe looks at a photograph of his father.`
      );
    } else if (sampleNum === 2) {
      setSceneNumber(2);
      setRawText(
        `EXT. CHENNAI STREET - DAY\n\nJohn walks outside.\n\nHe gets onto his motorcycle.`
      );
    } else if (sampleNum === 3) {
      setSceneNumber(3);
      setRawText(
        `INT. CAFE - DAY\n\nJohn meets Sarah.\n\nSarah gives John a small envelope.`
      );
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 flex flex-col h-full shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-accent-light" />
          <h2 className="text-base font-semibold text-white">Screenplay Input</h2>
        </div>
        
        {/* Sample Load Buttons */}
        <div className="flex items-center space-x-1.5 text-xs">
          <span className="text-gray-400 font-medium mr-1">Demo Scenes:</span>
          <button
            type="button"
            onClick={() => handleLoadSample(1)}
            className="px-2 py-0.5 rounded bg-cardHover hover:bg-border text-gray-300 text-[11px]"
          >
            Scene 1
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample(2)}
            className="px-2 py-0.5 rounded bg-cardHover hover:bg-border text-gray-300 text-[11px]"
          >
            Scene 2
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample(3)}
            className="px-2 py-0.5 rounded bg-cardHover hover:bg-border text-gray-300 text-[11px]"
          >
            Scene 3
          </button>
        </div>
      </div>

      <form onSubmit={handleAnalyze} className="flex-1 flex flex-col space-y-4">
        {/* Scene Number */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
            Scene Number:
          </label>
          <input
            type="number"
            min="1"
            value={sceneNumber}
            onChange={(e) => setSceneNumber(parseInt(e.target.value) || 1)}
            className="w-20 px-3 py-1.5 bg-card border border-border rounded-lg text-center text-sm font-semibold text-accent-light focus:outline-none focus:border-accent"
            required
          />
        </div>

        {/* Raw Text Textarea */}
        <div className="flex-1 flex flex-col min-h-[220px]">
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder={`INT. SCENE LOCATION - DAY\n\nEnter screenplay text here...\n\nExample:\nJohn enters the apartment.\nHe looks at a photograph of Sarah.`}
            className="w-full flex-1 p-4 bg-background/80 border border-border rounded-xl font-mono text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-accent resize-none leading-relaxed"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="flex items-center space-x-2 p-3 bg-accent-rose/10 border border-accent-rose/30 rounded-xl text-xs text-accent-rose">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Button */}
        <button
          type="submit"
          disabled={loading || !rawText.trim()}
          className="w-full py-3 bg-gradient-to-r from-accent to-accent-hover hover:from-accent-hover hover:to-indigo-700 text-white font-semibold rounded-xl transition-all shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Sparkles className="w-4 h-4 animate-spin text-accent-light" />
              <span>Analyzing Scene with Gemini...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Analyze Scene</span>
            </>
          )}
        </button>
      </form>

      {/* Processed Scenes History Pills */}
      {scenes.length > 0 && (
        <div className="mt-5 pt-3 border-t border-border">
          <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Processed Scenes:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {scenes.map((s) => (
              <button
                key={s.id}
                onClick={() => onSelectScene(s)}
                className="px-3 py-1 rounded-lg text-xs font-medium bg-cardHover border border-border hover:border-accent text-gray-300 hover:text-white transition-colors"
              >
                Scene {s.scene_number}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
