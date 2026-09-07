'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Download, FileText, FileCode, FileSpreadsheet, X, Check, Settings, Sparkles } from 'lucide-react';
import { downloadProjectScript } from '@/lib/api';

interface ExportScreenplayModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  theme: 'dark' | 'light';
}

export default function ExportScreenplayModal({
  isOpen,
  onClose,
  projectId,
  projectName,
  theme
}: ExportScreenplayModalProps) {
  const [format, setFormat] = useState<'pdf' | 'docx' | 'fountain'>('pdf');
  const [fontFamily, setFontFamily] = useState<string>('Courier');
  const [fontSize, setFontSize] = useState<number>(12);
  const [downloading, setDownloading] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !mounted) return null;

  const handleExport = () => {
    try {
      setDownloading(true);
      downloadProjectScript(projectId, format, fontFamily, fontSize);
      setTimeout(() => {
        setDownloading(false);
        onClose();
      }, 800);
    } catch (err) {
      console.error('Export failed:', err);
      setDownloading(false);
    }
  };

  return createPortal(
    <div className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in theme-${theme}`}>
      <div className="bg-card border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5 text-txtPrimary relative">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500 shrink-0">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-txtPrimary">Export Screenplay</h3>
              <p className="text-xs text-txtSecondary mt-0.5">
                Export <span className="font-semibold text-txtPrimary">"{projectName}"</span> with industry-standard formatting.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-txtMuted hover:text-txtPrimary hover:bg-cardHover transition shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Format Card Selection */}
        <div className="space-y-2">
          <label className="block text-xs font-bold text-txtPrimary">Choose Export Format</label>
          <div className="grid grid-cols-3 gap-2.5">
            {/* PDF Option */}
            <button
              type="button"
              onClick={() => setFormat('pdf')}
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                format === 'pdf'
                  ? 'border-emerald-500 bg-emerald-500/10 text-txtPrimary ring-2 ring-emerald-500/20'
                  : 'border-border bg-panel hover:bg-cardHover text-txtSecondary'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <FileText className="w-5 h-5 text-emerald-500" />
                {format === 'pdf' && <Check className="w-3.5 h-3.5 text-emerald-500" />}
              </div>
              <div>
                <div className="font-bold text-xs">PDF Document</div>
                <div className="text-[10px] text-txtMuted mt-0.5">Paginated & Printed</div>
              </div>
            </button>

            {/* Word DOCX Option */}
            <button
              type="button"
              onClick={() => setFormat('docx')}
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                format === 'docx'
                  ? 'border-blue-500 bg-blue-500/10 text-txtPrimary ring-2 ring-blue-500/20'
                  : 'border-border bg-panel hover:bg-cardHover text-txtSecondary'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <FileSpreadsheet className="w-5 h-5 text-blue-500" />
                {format === 'docx' && <Check className="w-3.5 h-3.5 text-blue-500" />}
              </div>
              <div>
                <div className="font-bold text-xs">Word (.docx)</div>
                <div className="text-[10px] text-txtMuted mt-0.5">Editable Document</div>
              </div>
            </button>

            {/* Fountain Option */}
            <button
              type="button"
              onClick={() => setFormat('fountain')}
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                format === 'fountain'
                  ? 'border-purple-500 bg-purple-500/10 text-txtPrimary ring-2 ring-purple-500/20'
                  : 'border-border bg-panel hover:bg-cardHover text-txtSecondary'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <FileCode className="w-5 h-5 text-purple-500" />
                {format === 'fountain' && <Check className="w-3.5 h-3.5 text-purple-500" />}
              </div>
              <div>
                <div className="font-bold text-xs">Fountain</div>
                <div className="text-[10px] text-txtMuted mt-0.5">Plain Text Markup</div>
              </div>
            </button>
          </div>
        </div>

        {/* Formatting & Typography Options (PDF & DOCX) */}
        {format !== 'fountain' && (
          <div className="bg-panel border border-border rounded-xl p-4 space-y-3.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-txtPrimary">
              <Settings className="w-3.5 h-3.5 text-secondary" />
              <span>Typography & Layout Settings</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-txtSecondary mb-1">Font Family</label>
                <select
                  value={fontFamily}
                  onChange={(e) => setFontFamily(e.target.value)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-xs text-txtPrimary focus:outline-none focus:border-secondary font-mono"
                >
                  <option value="Courier">Courier (Industry Standard)</option>
                  <option value="Helvetica">Helvetica (Sans-Serif)</option>
                  <option value="Times-Roman">Times New Roman</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-txtSecondary mb-1">Font Size</label>
                <select
                  value={fontSize}
                  onChange={(e) => setFontSize(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-xs text-txtPrimary focus:outline-none focus:border-secondary font-mono"
                >
                  <option value={10}>10 pt (Compact)</option>
                  <option value={12}>12 pt (Hollywood Standard)</option>
                  <option value={14}>14 pt (Large Print)</option>
                </select>
              </div>
            </div>

            <div className="text-[10px] text-txtMuted flex items-center gap-1 pt-1">
              <Sparkles className="w-3 h-3 text-emerald-500 shrink-0" />
              <span>Orphan character header protection enabled automatically.</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-panel border border-border hover:bg-cardHover text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={downloading}
            onClick={handleExport}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md hover:shadow-lg disabled:opacity-50 shrink-0 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            {downloading ? 'Exporting...' : `Export as ${format.toUpperCase()}`}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
