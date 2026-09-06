'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Image, Type } from 'lucide-react';

interface Props {
  sceneNumber: number;
  totalScenesCount?: number;
  rawText: string;
  onChangeText: (text: string) => void;
  onBlurSave?: () => void;
  onSelectFindingHighlight?: (findingId: string) => void;
}

export default function ScreenplayPage({
  sceneNumber,
  totalScenesCount,
  rawText,
  onChangeText,
  onBlurSave,
  onSelectFindingHighlight
}: Props) {
  const [editing, setEditing] = useState(false);
  const [textVal, setTextVal] = useState(rawText);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Dynamic formatting controls
  const [fontFamily, setFontFamily] = useState<'Courier Prime' | 'Courier New' | 'Inter' | 'Roboto Mono' | 'Georgia'>('Courier Prime');
  const [fontSize, setFontSize] = useState<'12pt' | '14pt' | '16pt' | '18pt'>('12pt');

  useEffect(() => {
    setTextVal(rawText);
  }, [rawText]);

  // Auto-expand textarea height on edit
  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.max(580, textareaRef.current.scrollHeight)}px`;
    }
  }, [editing, textVal]);

  const handleBlur = () => {
    setEditing(false);
    if (onBlurSave) {
      onBlurSave();
    }
  };

  const wordCount = textVal.trim() ? textVal.trim().split(/\s+/).filter(Boolean).length : 0;
  const lines = textVal.split('\n');

  // Compute inline styles based on user selection
  const fontStyle = {
    fontFamily: fontFamily === 'Courier Prime' ? '"Courier Prime", Courier, monospace'
      : fontFamily === 'Courier New' ? '"Courier New", Courier, monospace'
      : fontFamily === 'Inter' ? 'Inter, sans-serif'
      : fontFamily === 'Roboto Mono' ? '"Roboto Mono", monospace'
      : 'Georgia, serif',
    fontSize: fontSize
  };

  // Pre-process lines with dialogue context state for accurate screenplay layout
  const renderFormattedLines = () => {
    let isDialogueContext = false;
    let isFirstNonEmpty = true;

    return lines.map((line, idx) => {
      const trimmed = line.trim();

      if (!trimmed) {
        isDialogueContext = false;
        return <div key={idx} className="h-3" />;
      }

      const isFirst = isFirstNonEmpty;
      if (isFirstNonEmpty) {
        isFirstNonEmpty = false;
      }

      // 1. Slugline / Scene Heading Detection
      const isSluglinePrefix = 
        trimmed.startsWith('INT.') || 
        trimmed.startsWith('EXT.') || 
        trimmed.startsWith('INT./EXT.') || 
        trimmed.startsWith('I/E.') ||
        trimmed.startsWith('INT ') ||
        trimmed.startsWith('EXT ');

      const hasTimeOfDaySuffix = /[\-\–\—]\s*(DAY|NIGHT|MORNING|EVENING|AFTERNOON|DUSK|DAWN|CONTINUOUS|LATER|MOMENTS LATER|SAME)/i.test(trimmed);

      if (isFirst || isSluglinePrefix || hasTimeOfDaySuffix) {
        isDialogueContext = false;
        return (
          <div key={idx} className="screenplay-slugline font-bold uppercase">
            {line}
          </div>
        );
      }

      // 2. Character Name Detection (UPPERCASE, 2-30 chars, no sentence punctuation)
      if (
        trimmed.length > 1 &&
        trimmed.length < 35 &&
        trimmed === trimmed.toUpperCase() &&
        !trimmed.includes('—') &&
        !trimmed.startsWith('(') &&
        !trimmed.endsWith('.') &&
        !trimmed.endsWith('!') &&
        !trimmed.endsWith('?')
      ) {
        isDialogueContext = true;
        return (
          <div key={idx} className="screenplay-character font-bold">
            {line}
          </div>
        );
      }

      // 3. Parenthetical Detection
      if (trimmed.startsWith('(') && trimmed.endsWith(')')) {
        if (isDialogueContext) {
          return (
            <div key={idx} className="screenplay-parenthetical">
              {line}
            </div>
          );
        }
      }

      // 4. Special Inline Highlights for Reference Mockup
      if (trimmed.includes('faded Polaroid of the waterfront warehouse')) {
        isDialogueContext = false;
        return (
          <div key={idx} className="screenplay-action">
            John freezes. His eyes dart across the{' '}
            <span
              onClick={(e) => {
                e.stopPropagation();
                if (onSelectFindingHighlight) onSelectFindingHighlight('knowledge-gap');
              }}
              className="highlight-knowledge-gap cursor-pointer hover:opacity-80 font-bold"
              title="Knowledge Gap Finding #1"
            >
              faded Polaroid of the waterfront warehouse
            </span>
            .
          </div>
        );
      }

      if (trimmed.includes('The pier was sealed three weeks ago.')) {
        isDialogueContext = true;
        return (
          <div key={idx} className="screenplay-dialogue">
            Where did you find this?{' '}
            <span
              onClick={(e) => {
                e.stopPropagation();
                if (onSelectFindingHighlight) onSelectFindingHighlight('procedure-check');
              }}
              className="highlight-procedure-check cursor-pointer hover:opacity-80 font-bold"
              title="1985 Procedure Reality Check #2"
            >
              The pier was sealed three weeks ago.
            </span>
          </div>
        );
      }

      // Insert Prop Card Mockup for Scene 14
      if (trimmed.includes('She pulls a water-damaged 4x6 print')) {
        isDialogueContext = false;
        return (
          <React.Fragment key={idx}>
            <div className="screenplay-action">{line}</div>
            <div className="inline-prop-card flex items-center justify-between font-sans text-xs shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded bg-cardHover border border flex items-center justify-center text-amber-500">
                  <Image className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-amber-500 font-mono text-[10px] uppercase">
                      PROP #PR-088
                    </span>
                    <span className="text-txtMuted text-[10px] font-mono">From Sc. 07</span>
                  </div>
                  <h5 className="font-bold text-txtPrimary text-xs">
                    Polaroid 600 • Waterfront Pier 19
                  </h5>
                </div>
              </div>
            </div>
          </React.Fragment>
        );
      }

      // 5. Dialogue Line Rendering (Left-aligned within dialogue block margin)
      if (isDialogueContext) {
        return (
          <div key={idx} className="screenplay-dialogue">
            {line}
          </div>
        );
      }

      // 6. Action Line Rendering (Left-aligned narrative description)
      return (
        <div key={idx} className="screenplay-action">
          {line}
        </div>
      );
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-app overflow-y-auto p-4 md:p-6 pb-16 select-text transition-colors">
      {/* Top Page Header Metadata & Dynamic Formatting Controls */}
      <div className="max-w-3xl w-full mx-auto mb-3 flex items-center justify-between text-[11px] font-mono text-txtSecondary select-none bg-card/50 p-2.5 rounded-xl border border-border shadow-sm shrink-0">
        <div className="flex items-center space-x-3">
          <span className="font-bold text-txtPrimary uppercase">SCENE {sceneNumber}</span>
          <span>•</span>
          <div className="flex items-center space-x-1.5">
            <Type className="w-3 h-3 text-accent-light" />
            <span className="text-txtMuted font-semibold">Font:</span>
            <select
              value={fontFamily}
              onChange={(e) => setFontFamily(e.target.value as any)}
              className="bg-card border border-border rounded-md px-2 py-0.5 text-[10px] text-txtPrimary font-bold focus:outline-none focus:border-accent cursor-pointer hover:border-accent/50 transition-colors"
            >
              <option value="Courier Prime">Courier Prime</option>
              <option value="Courier New">Courier New</option>
              <option value="Inter">Inter (Sans)</option>
              <option value="Roboto Mono">Roboto Mono</option>
              <option value="Georgia">Georgia (Serif)</option>
            </select>
          </div>
          <span>•</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-txtMuted font-semibold">Size:</span>
            <select
              value={fontSize}
              onChange={(e) => setFontSize(e.target.value as any)}
              className="bg-card border border-border rounded-md px-2 py-0.5 text-[10px] text-txtPrimary font-bold focus:outline-none focus:border-accent cursor-pointer hover:border-accent/50 transition-colors"
            >
              <option value="12pt">12pt (Standard)</option>
              <option value="14pt">14pt (Medium)</option>
              <option value="16pt">16pt (Large)</option>
              <option value="18pt">18pt (XL)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-2 font-mono text-[10px]">
          {editing && (
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 font-bold animate-pulse">
              Editing Raw Text
            </span>
          )}
          <span>PAGE {sceneNumber} OF {totalScenesCount || 1}</span>
          <span>•</span>
          <span>{wordCount} WORDS</span>
        </div>
      </div>

      {/* Screenplay Paper Container (Fully wraps the scene height dynamically) */}
      <div className="max-w-3xl w-full mx-auto screenplay-paper rounded-2xl p-8 md:p-12 min-h-[calc(100vh-180px)] h-fit shadow-2xl relative transition-colors mb-12 shrink-0">
        <div className="absolute top-6 right-8 text-[11px] font-mono opacity-60 select-none flex items-center gap-2">
          {editing && <span className="text-[10px] text-txtMuted font-sans">Click outside to format</span>}
          <span>{sceneNumber}.</span>
        </div>

        {editing ? (
          <textarea
            ref={textareaRef}
            value={textVal}
            onChange={(e) => {
              setTextVal(e.target.value);
              onChangeText(e.target.value);
              if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
                textareaRef.current.style.height = `${Math.max(580, textareaRef.current.scrollHeight)}px`;
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Tab') {
                e.preventDefault();
                const start = e.currentTarget.selectionStart;
                const end = e.currentTarget.selectionEnd;
                const val = textVal;
                const newVal = val.substring(0, start) + '    ' + val.substring(end);
                setTextVal(newVal);
                onChangeText(newVal);
                setTimeout(() => {
                  if (textareaRef.current) {
                    textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4;
                  }
                }, 0);
              }
              if (e.key === 'Escape') {
                setEditing(false);
                if (onBlurSave) onBlurSave();
              }
            }}
            onBlur={handleBlur}
            style={fontStyle}
            className="w-full min-h-[580px] bg-transparent text-screenplay focus:outline-none resize-none leading-relaxed overflow-hidden font-mono"
            autoFocus
          />
        ) : (
          <div
            onClick={() => setEditing(true)}
            style={fontStyle}
            className="text-screenplay cursor-text min-h-[580px] leading-relaxed pb-4"
          >
            {renderFormattedLines()}
          </div>
        )}
      </div>
    </div>
  );
}
