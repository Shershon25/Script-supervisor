'use client';

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  FileText, Upload, AlertCircle, CheckCircle2, Loader2, X, 
  Film, AlertTriangle, ChevronRight, FileCheck, Layers, Sparkles
} from 'lucide-react';
import { 
  ImportPreview, uploadDocumentForPreview, confirmDocumentImport 
} from '@/lib/api';

interface ImportScreenplayModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  onImportSuccess: (importedCount: number) => void;
  theme: 'dark' | 'light';
}

type Stage = 'SELECTING' | 'PARSING' | 'PREVIEW' | 'IMPORTING' | 'SUCCESS' | 'ERROR';

export default function ImportScreenplayModal({
  isOpen,
  onClose,
  projectId,
  projectName,
  onImportSuccess,
  theme
}: ImportScreenplayModalProps) {
  const [mounted, setMounted] = useState(false);
  const [stage, setStage] = useState<Stage>('SELECTING');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreview | null>(null);
  const [importMode, setImportMode] = useState<'append' | 'replace'>('append');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [importedCount, setImportedCount] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Reset internal state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStage('SELECTING');
      setSelectedFile(null);
      setPreviewData(null);
      setImportMode('append');
      setErrorMessage(null);
      setImportedCount(0);
    }
  }, [isOpen]);

  if (!isOpen || !mounted) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const processSelectedFile = async (file: File) => {
    const filename = file.name.toLowerCase();
    if (!filename.endsWith('.pdf') && !filename.endsWith('.docx') && !filename.endsWith('.fountain')) {
      setErrorMessage("Unsupported file format. Please select a .pdf, .docx, or .fountain file.");
      setStage('ERROR');
      return;
    }

    setSelectedFile(file);
    setErrorMessage(null);
    setStage('PARSING');

    try {
      const preview = await uploadDocumentForPreview(projectId, file);
      setPreviewData(preview);
      setStage('PREVIEW');
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to parse document.");
      setStage('ERROR');
    }
  };

  const handleConfirmImport = async () => {
    if (!previewData) return;
    setStage('IMPORTING');
    setErrorMessage(null);

    try {
      const res = await confirmDocumentImport(projectId, previewData.document_id, importMode);
      setImportedCount(res.scenes_imported);
      setStage('SUCCESS');
      onImportSuccess(res.scenes_imported);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to import scenes into project.");
      setStage('ERROR');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return createPortal(
    <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
      <div className="bg-card border border-border rounded-2xl p-6 max-w-xl w-full shadow-2xl space-y-5 text-txtPrimary relative max-h-[90vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400 shrink-0">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-txtPrimary">Import Screenplay Document</h3>
              <p className="text-xs text-txtSecondary mt-0.5">
                Ingest PDF, DOCX, or Fountain screenplay files for deterministic scene detection.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
          >
            <X className="w-4.5 h-4.5" />
          </button>
        </div>

        {/* Modal Body - Stage Views */}
        <div className="flex-1 overflow-y-auto min-h-0 space-y-4 pr-1">

          {/* STAGE 1: FILE SELECTION */}
          {stage === 'SELECTING' && (
            <div className="space-y-4">
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-border hover:border-blue-500/50 bg-panel/60 hover:bg-panel rounded-2xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-3 group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.fountain"
                  className="hidden"
                />
                <div className="p-3.5 bg-blue-500/10 rounded-2xl text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                  <FileText className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-xs font-bold text-txtPrimary">
                    Click to upload or drag & drop screenplay document
                  </p>
                  <p className="text-[11px] text-txtSecondary mt-1">
                    Supports <span className="font-semibold text-txtPrimary">.PDF</span>, <span className="font-semibold text-txtPrimary">.DOCX</span>, and <span className="font-semibold text-txtPrimary">.FOUNTAIN</span> (up to 15MB)
                  </p>
                </div>
              </div>

              <div className="p-3 bg-panel border border-border rounded-xl text-[11px] text-txtSecondary space-y-1">
                <p className="font-semibold text-txtPrimary flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  Deterministic Screenplay Extraction
                </p>
                <p>Original dialogue, character names, and scene text remain completely untouched without LLM rewriting.</p>
              </div>
            </div>
          )}

          {/* STAGE 2: PARSING STATE */}
          {stage === 'PARSING' && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
              <Loader2 className="w-10 h-10 text-blue-600 dark:text-blue-400 animate-spin" />
              <div>
                <h4 className="font-bold text-sm text-txtPrimary">Parsing Screenplay Document...</h4>
                <p className="text-xs text-txtSecondary mt-1">
                  Extracting text and identifying scene boundaries from {selectedFile?.name}.
                </p>
              </div>
            </div>
          )}

          {/* STAGE 3: PREVIEW */}
          {stage === 'PREVIEW' && previewData && (
            <div className="space-y-4">

              {/* Document Overview Summary Card */}
              <div className="p-4 bg-panel border border-border rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span className="font-bold text-xs text-txtPrimary truncate max-w-[280px]">
                      {previewData.filename}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-accent/20 px-2 py-0.5 rounded text-txtPrimary font-bold">
                    {previewData.file_type}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border/50 text-center">
                  <div className="p-2 bg-card rounded-lg">
                    <p className="text-[10px] text-txtMuted font-medium">Size</p>
                    <p className="text-xs font-bold text-txtPrimary">{formatFileSize(previewData.file_size)}</p>
                  </div>
                  <div className="p-2 bg-card rounded-lg">
                    <p className="text-[10px] text-txtMuted font-medium font-mono">Pages</p>
                    <p className="text-xs font-bold text-txtPrimary">{previewData.page_count ?? 'N/A'}</p>
                  </div>
                  <div className="p-2 bg-card rounded-lg">
                    <p className="text-[10px] text-txtMuted font-medium">Scenes Detected</p>
                    <p className="text-xs font-bold text-blue-600 dark:text-blue-400">{previewData.scene_count}</p>
                  </div>
                </div>
              </div>

              {/* Warnings Banner if Any */}
              {previewData.warnings && previewData.warnings.length > 0 && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start space-x-2 text-amber-600 dark:text-amber-400 text-xs">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    {previewData.warnings.map((w, idx) => (
                      <p key={idx}>{w}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Existing Project Content Warning Options */}
              {previewData.existing_scenes_count > 0 && (
                <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-2">
                  <p className="text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    This project already contains {previewData.existing_scenes_count} screenplay scene(s).
                  </p>
                  <p className="text-[11px] text-txtSecondary">Choose how you want to handle the import:</p>
                  
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setImportMode('append')}
                      className={`p-2.5 rounded-lg border text-left text-xs font-semibold transition flex items-center justify-between ${
                        importMode === 'append'
                          ? 'border-blue-500 bg-blue-500/10 text-txtPrimary font-bold'
                          : 'border-border bg-card text-txtSecondary hover:text-txtPrimary'
                      }`}
                    >
                      <span>Append after Scene {previewData.existing_scenes_count}</span>
                      {importMode === 'append' && <CheckCircle2 className="w-3.5 h-3.5 text-blue-500" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => setImportMode('replace')}
                      className={`p-2.5 rounded-lg border text-left text-xs font-semibold transition flex items-center justify-between ${
                        importMode === 'replace'
                          ? 'border-red-500 bg-red-500/10 text-red-600 dark:text-red-400 font-bold'
                          : 'border-border bg-card text-txtSecondary hover:text-txtPrimary'
                      }`}
                    >
                      <span>Replace existing screenplay</span>
                      {importMode === 'replace' && <CheckCircle2 className="w-3.5 h-3.5 text-red-500" />}
                    </button>
                  </div>
                </div>
              )}

              {/* Detected Scenes List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-txtPrimary flex items-center justify-between">
                  <span>Detected Scene Boundaries</span>
                  <span className="text-[11px] font-normal text-txtSecondary">{previewData.scenes.length} items</span>
                </h4>

                <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                  {previewData.scenes.map((scene) => (
                    <div
                      key={scene.temporary_id}
                      className="p-2.5 bg-panel border border-border rounded-lg text-xs space-y-1 hover:border-secondary/40 transition-colors"
                    >
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-bold text-txtPrimary truncate max-w-[320px]">
                          #{scene.scene_number} {scene.heading}
                        </span>
                        <div className="flex items-center space-x-2 text-[10px] text-txtMuted shrink-0">
                          {scene.source_page_start && (
                            <span>
                              Pages {scene.source_page_start}{scene.source_page_end && scene.source_page_end !== scene.source_page_start ? `–${scene.source_page_end}` : ''}
                            </span>
                          )}
                          <span className="px-1.5 py-0.5 rounded bg-card text-emerald-600 dark:text-emerald-400 font-bold">
                            {(scene.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-txtSecondary line-clamp-2 font-mono bg-card p-1.5 rounded border border-border/40">
                        {scene.raw_text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STAGE 4: IMPORTING */}
          {stage === 'IMPORTING' && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
              <Loader2 className="w-10 h-10 text-blue-600 dark:text-blue-400 animate-spin" />
              <div>
                <h4 className="font-bold text-sm text-txtPrimary">Creating Scene Records...</h4>
                <p className="text-xs text-txtSecondary mt-1">
                  Persisting screenplay scenes and document provenance into project.
                </p>
              </div>
            </div>
          )}

          {/* STAGE 5: SUCCESS */}
          {stage === 'SUCCESS' && (
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <div>
                <h4 className="font-bold text-base text-txtPrimary">Import Complete!</h4>
                <p className="text-xs text-txtSecondary mt-1">
                  <span className="font-bold text-txtPrimary">{importedCount} scene(s)</span> successfully imported into <span className="font-semibold text-txtPrimary">{projectName}</span>.
                </p>
              </div>

              <div className="p-3 bg-panel border border-border rounded-xl text-left text-xs space-y-1 w-full max-w-sm">
                <p className="font-bold text-txtPrimary flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                  Ready for Script Supervisor Analysis
                </p>
                <p className="text-txtSecondary text-[11px]">
                  Imported scenes can now be analyzed using the Script Supervisor pipeline.
                </p>
              </div>
            </div>
          )}

          {/* STAGE 6: ERROR */}
          {stage === 'ERROR' && (
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-full text-red-600 dark:text-red-400">
                <AlertCircle className="w-10 h-10" />
              </div>
              <div className="max-w-md">
                <h4 className="font-bold text-base text-txtPrimary">Import Error</h4>
                <p className="text-xs text-red-600 dark:text-red-400 mt-1 font-medium bg-red-500/10 p-2.5 rounded-xl border border-red-500/20">
                  {errorMessage || "An unexpected error occurred during import."}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border shrink-0">
          {stage === 'SELECTING' && (
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
            >
              Cancel
            </button>
          )}

          {stage === 'PREVIEW' && (
            <>
              <button
                type="button"
                onClick={() => setStage('SELECTING')}
                className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
              >
                Choose Different File
              </button>
              <button
                type="button"
                onClick={handleConfirmImport}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg"
              >
                <span>Import {previewData?.scene_count} Scene(s)</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </>
          )}

          {stage === 'SUCCESS' && (
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-md"
            >
              Done & View Scenes
            </button>
          )}

          {stage === 'ERROR' && (
            <>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => setStage('SELECTING')}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition"
              >
                Try Again
              </button>
            </>
          )}
        </div>

      </div>
    </div>,
    document.body
  );
}
